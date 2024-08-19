const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 3000;

app.use(express.static('public'));

app.get('/api/files', (req, res) => {
    const directoryPath = path.join(__dirname, 'files');
    const getDirectoryTree = (dirPath) => {
        const files = fs.readdirSync(dirPath);
        return files.map(file => {
            const filePath = path.join(dirPath, file);
            const isDirectory = fs.statSync(filePath).isDirectory();
            return {
                name: file,
                path: filePath,
                isDirectory,
                children: isDirectory ? getDirectoryTree(filePath) : []
            };
        });
    };
    res.json(getDirectoryTree(directoryPath));
});

app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});