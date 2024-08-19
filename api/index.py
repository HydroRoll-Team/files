from flask import Flask, render_template, request, redirect, send_file, url_for, send_from_directory, session, flash
from werkzeug.utils import secure_filename
import os
import zipfile
import io
import urllib.parse


app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'files'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('upload_file'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # 简单的用户名和密码验证
        if username == 'admin' and password == 'password':
            session['username'] = username
            return redirect(url_for('upload_file'))
        else:
            flash('Invalid credentials')
    return render_template('templates/login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('File successfully uploaded')
            return redirect(url_for('uploaded_files'))
    return render_template('templates/upload.html')

@app.route('/files')
def uploaded_files():
    if 'username' not in session:
        return redirect(url_for('login'))
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('templates/files.html', files=files)

@app.route('/files/<filename>')
def file_info(filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        file_ext = filename.rsplit('.', 1)[1].lower()
        if file_ext in {'png', 'jpg', 'jpeg', 'gif'}:
            file_type = 'image'
        elif file_ext in {'txt', 'pdf'}:
            file_type = 'text'
        elif file_ext == 'zip':
            file_type = 'zip'
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_contents = zip_ref.namelist()
            return render_template('templates/file_info.html', filename=filename, file_type=file_type, zip_contents=zip_contents)
        else:
            file_type = 'other'
        return render_template('templates/file_info.html', filename=filename, file_type=file_type)
    else:
        flash('File not found')
        return redirect(url_for('uploaded_files'))

@app.route('/files/<zip_filename>/<inner_filename>')
def view_inner_file(zip_filename, inner_filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
    if os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            if inner_filename in zip_ref.namelist():
                file_ext = inner_filename.rsplit('.', 1)[1].lower()
                if file_ext in {'png', 'jpg', 'jpeg', 'gif'}:
                    file_type = 'image'
                    file_data = zip_ref.read(inner_filename)
                    return send_file(io.BytesIO(file_data), mimetype=f'image/{file_ext}')
                elif file_ext in {'txt', 'pdf'}:
                    file_type = 'text'
                    file_data = zip_ref.read(inner_filename)
                    return send_file(io.BytesIO(file_data), mimetype=f'application/{file_ext}')
                else:
                    flash('Unsupported file type inside zip')
                    return redirect(url_for('file_info', filename=zip_filename))
            else:
                flash('File not found inside zip')
                return redirect(url_for('file_info', filename=zip_filename))
    else:
        flash('Zip file not found')
        return redirect(url_for('uploaded_files'))


@app.route('/download/<filename>')
def download_file(filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)