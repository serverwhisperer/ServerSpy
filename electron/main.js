const { app, BrowserWindow, shell, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow;
let pythonProcess;
const PORT = 5000;

// Get the correct paths based on whether we're in dev or production
function getResourcePath(relativePath) {
    if (app.isPackaged) {
        return path.join(process.resourcesPath, relativePath);
    }
    return path.join(__dirname, '..', relativePath);
}

// Check if the Flask server is running
function checkServer(callback) {
    const options = {
        host: 'localhost',
        port: PORT,
        timeout: 2000
    };

    const req = http.request(options, (res) => {
        callback(true);
    });

    req.on('error', () => {
        callback(false);
    });

    req.on('timeout', () => {
        req.destroy();
        callback(false);
    });

    req.end();
}

// Wait for the server to start
function waitForServer(callback, maxAttempts = 30) {
    let attempts = 0;

    const check = () => {
        attempts++;
        checkServer((isRunning) => {
            if (isRunning) {
                callback(true);
            } else if (attempts < maxAttempts) {
                setTimeout(check, 500);
            } else {
                callback(false);
            }
        });
    };

    check();
}

// Start the Flask server
function startFlaskServer() {
    return new Promise((resolve, reject) => {
        const backendPath = getResourcePath('backend');
        const appPath = path.join(backendPath, 'app.py');

        console.log('Starting Flask server from:', appPath);

        // Try to find Python
        const pythonCommands = ['python', 'python3', 'py'];
        let pythonCmd = 'python';

        // On Windows, prefer 'python' or 'py'
        if (process.platform === 'win32') {
            pythonCmd = 'python';
        }

        pythonProcess = spawn(pythonCmd, [appPath], {
            cwd: backendPath,
            env: { ...process.env, PYTHONUNBUFFERED: '1' },
            stdio: ['ignore', 'pipe', 'pipe']
        });

        pythonProcess.stdout.on('data', (data) => {
            console.log(`Flask: ${data}`);
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error(`Flask Error: ${data}`);
        });

        pythonProcess.on('error', (err) => {
            console.error('Failed to start Flask:', err);
            reject(err);
        });

        pythonProcess.on('close', (code) => {
            console.log(`Flask process exited with code ${code}`);
            if (code !== 0 && code !== null) {
                // Server crashed, show error
                dialog.showErrorBox('Server Error', 
                    'The backend server has stopped unexpectedly. Please restart the application.');
            }
        });

        // Wait for server to be ready
        waitForServer((isRunning) => {
            if (isRunning) {
                resolve();
            } else {
                reject(new Error('Server failed to start'));
            }
        });
    });
}

// Create the main window
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1024,
        minHeight: 700,
        title: 'ServerScout',
        icon: path.join(__dirname, 'icon.png'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true
        },
        autoHideMenuBar: true,
        backgroundColor: '#0a0f1c'
    });

    // Load the Flask server URL
    mainWindow.loadURL(`http://localhost:${PORT}`);

    // Open external links in default browser
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// App ready event
app.whenReady().then(async () => {
    try {
        // Check if server is already running
        checkServer(async (isRunning) => {
            if (!isRunning) {
                console.log('Starting Flask server...');
                await startFlaskServer();
            } else {
                console.log('Flask server already running');
            }
            createWindow();
        });
    } catch (error) {
        console.error('Failed to start application:', error);
        dialog.showErrorBox('Startup Error', 
            `Failed to start the application: ${error.message}\n\nMake sure Python is installed and all dependencies are available.`);
        app.quit();
    }
});

// Quit when all windows are closed
app.on('window-all-closed', () => {
    // Stop the Flask server
    if (pythonProcess) {
        pythonProcess.kill();
    }
    
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});

// Clean up on exit
app.on('before-quit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
});

