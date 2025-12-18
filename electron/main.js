const { app, BrowserWindow, shell, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

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

// Simple delay function
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Start the Flask server
function startFlaskServer() {
    return new Promise((resolve, reject) => {
        const backendPath = getResourcePath('backend');
        const appPath = path.join(backendPath, 'app.py');

        console.log('Starting Flask server from:', appPath);

        // On Windows, prefer 'python' or 'py'
        const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';

        pythonProcess = spawn(pythonCmd, [appPath], {
            cwd: backendPath,
            env: { ...process.env, PYTHONUNBUFFERED: '1', ELECTRON_RUN: '1' },
            stdio: ['ignore', 'pipe', 'pipe']
        });

        let serverStarted = false;

        pythonProcess.stdout.on('data', (data) => {
            const output = data.toString();
            console.log(`Flask: ${output}`);
            
            // Detect when Flask is ready
            if (output.includes('Running on') && !serverStarted) {
                serverStarted = true;
                resolve();
            }
        });

        pythonProcess.stderr.on('data', (data) => {
            const output = data.toString();
            console.log(`Flask: ${output}`);
            
            // Flask also outputs "Running on" to stderr sometimes
            if (output.includes('Running on') && !serverStarted) {
                serverStarted = true;
                resolve();
            }
        });

        pythonProcess.on('error', (err) => {
            console.error('Failed to start Flask:', err);
            reject(err);
        });

        pythonProcess.on('close', (code) => {
            console.log(`Flask process exited with code ${code}`);
            if (!serverStarted && code !== 0) {
                reject(new Error(`Flask exited with code ${code}`));
            }
        });

        // Fallback timeout - if no "Running on" detected in 10 seconds, assume it's ready
        setTimeout(() => {
            if (!serverStarted) {
                serverStarted = true;
                resolve();
            }
        }, 10000);
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

// Show error dialog and quit
function handleStartupError(error) {
    console.error('Failed to start application:', error);
    dialog.showErrorBox('Startup Error', 
        `Failed to start the application: ${error.message}\n\nMake sure Python is installed and all dependencies are available.`);
    app.quit();
}

// App ready event
app.whenReady().then(async () => {
    try {
        console.log('Starting Flask server...');
        await startFlaskServer();
        
        // Small delay to ensure server is fully ready
        await delay(500);
        
        createWindow();
    } catch (error) {
        handleStartupError(error);
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
