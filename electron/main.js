const { app, BrowserWindow, shell, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let backendProcess;
const PORT = 5000;

// Get the correct paths based on whether we're in dev or production
function getResourcePath(relativePath) {
    if (app.isPackaged) {
        return path.join(process.resourcesPath, relativePath);
    }
    return path.join(__dirname, '..', relativePath);
}

// Check if we're running in packaged/production mode
function isPackaged() {
    return app.isPackaged;
}

// Simple delay function
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Start the backend server (exe in production, python in development)
function startBackendServer() {
    return new Promise((resolve, reject) => {
        const backendPath = getResourcePath('backend');
        
        let cmd, args, execPath;
        
        if (isPackaged()) {
            // Production: Use compiled exe
            execPath = path.join(backendPath, 'serverscout-backend.exe');
            
            // Check if exe exists
            if (!fs.existsSync(execPath)) {
                reject(new Error(`Backend executable not found: ${execPath}`));
                return;
            }
            
            cmd = execPath;
            args = [];
            console.log('Starting backend from exe:', execPath);
        } else {
            // Development: Use Python
            const appPath = path.join(backendPath, 'app.py');
            cmd = process.platform === 'win32' ? 'python' : 'python3';
            args = [appPath];
            console.log('Starting backend from Python:', appPath);
        }

        // Get frontend path for backend
        const frontendPath = getResourcePath('frontend');
        
        backendProcess = spawn(cmd, args, {
            cwd: backendPath,
            env: { 
                ...process.env, 
                PYTHONUNBUFFERED: '1', 
                ELECTRON_RUN: '1',
                FRONTEND_PATH: frontendPath  // Pass frontend path to backend
            },
            stdio: ['ignore', 'pipe', 'pipe'],
            // Important for Windows exe
            windowsHide: true
        });

        let serverStarted = false;
        let processExited = false;
        let fallbackTimeout = null;

        const cleanup = () => {
            if (fallbackTimeout) {
                clearTimeout(fallbackTimeout);
                fallbackTimeout = null;
            }
        };

        let outputBuffer = '';
        
        backendProcess.stdout.on('data', (data) => {
            const output = data.toString();
            outputBuffer += output;
            console.log(`Backend: ${output}`);
            
            // Detect when server is ready (check for various Flask startup messages)
            // Flask with HTTPS outputs: "Running on https://127.0.0.1:5000"
            if ((output.includes('Running on') || 
                 output.includes('Starting server') ||
                 output.includes('WARNING: This is a development server') ||
                 output.includes(' * Running on') ||
                 output.includes('https://') ||
                 output.includes('http://')) && !serverStarted) {
                serverStarted = true;
                cleanup();
                resolve();
            }
        });

        backendProcess.stderr.on('data', (data) => {
            const output = data.toString();
            outputBuffer += output;
            console.log(`Backend: ${output}`);
            
            // Flask outputs startup messages to stderr, especially with HTTPS
            // Check for any indication that server started
            if ((output.includes('Running on') || 
                 output.includes('Starting server') ||
                 output.includes('WARNING: This is a development server') ||
                 output.includes(' * Running on') ||
                 output.includes('https://') ||
                 output.includes('http://')) && !serverStarted) {
                serverStarted = true;
                cleanup();
                resolve();
            }
        });

        backendProcess.on('error', (err) => {
            console.error('Failed to start backend:', err);
            processExited = true;
            cleanup();
            if (!serverStarted) {
                reject(err);
            }
        });

        backendProcess.on('close', (code) => {
            console.log(`Backend process exited with code ${code}`);
            processExited = true;
            cleanup();
            
            // If server hasn't started yet and process exited, it's a failure
            if (!serverStarted) {
                reject(new Error(`Backend process exited unexpectedly with code ${code}`));
            }
        });

        // Fallback timeout - only resolve if process is still running
        fallbackTimeout = setTimeout(() => {
            if (!serverStarted && !processExited) {
                // Process is still running but no "Running on" detected
                // Assume it's ready (some configs may not output this)
                console.log('Timeout reached, assuming server is ready');
                serverStarted = true;
                resolve();
            }
            // If processExited is true, the close handler already rejected
        }, 15000); // Longer timeout for packaged app
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

    // Load the Flask server URL (HTTPS for security)
    // Use 127.0.0.1 instead of localhost to avoid DNS resolution issues
    mainWindow.loadURL(`https://127.0.0.1:${PORT}`);

    // Open external links in default browser
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });

    // Handle page load errors
    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
        console.error('Page load failed:', errorCode, errorDescription, validatedURL);
        if (errorCode === -106 || errorCode === -501) {
            // ERR_INTERNET_DISCONNECTED, connection refused, or SSL error
            // SSL error (-501) is expected with self-signed cert, ignore it
            if (errorCode === -106) {
                dialog.showErrorBox(
                    'Connection Error',
                    `Cannot connect to backend server at https://127.0.0.1:${PORT}\n\n` +
                    `Error: ${errorDescription}\n\n` +
                    `Please check:\n` +
                    `1. Backend server is running\n` +
                    `2. Port ${PORT} is not blocked\n` +
                    `3. Check console for backend errors`
                );
            }
        }
    });
    
    // Ignore certificate errors for self-signed certificate (localhost only)
    mainWindow.webContents.on('certificate-error', (event, url, error, certificate, callback) => {
        // Only ignore for localhost/127.0.0.1
        if (url.startsWith('https://localhost:') || url.startsWith('https://127.0.0.1:')) {
            event.preventDefault();
            callback(true); // Accept self-signed certificate
            console.log('Accepted self-signed certificate for:', url);
        } else {
            callback(false); // Reject for other domains
        }
    });

    // Log console messages from renderer
    mainWindow.webContents.on('console-message', (event, level, message) => {
        console.log(`[Renderer ${level}]:`, message);
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// Show error dialog and quit
function handleStartupError(error) {
    console.error('Failed to start application:', error);
    
    let message = `Failed to start the application:\n\n${error.message}`;
    
    if (!isPackaged()) {
        message += '\n\nMake sure Python is installed and all dependencies are available.';
    }
    
    dialog.showErrorBox('Startup Error', message);
    app.quit();
}

// Kill backend process properly on Windows
function killBackend() {
    if (backendProcess) {
        if (process.platform === 'win32') {
            // On Windows, use taskkill to ensure child processes are killed
            spawn('taskkill', ['/pid', backendProcess.pid, '/f', '/t'], { windowsHide: true });
        } else {
            backendProcess.kill('SIGTERM');
        }
        backendProcess = null;
    }
}

// App ready event
app.whenReady().then(async () => {
    try {
        console.log('Starting backend server...');
        console.log('Packaged:', isPackaged());
        
        await startBackendServer();
        
        // Small delay to ensure server is fully ready
        await delay(500);
        
        createWindow();
    } catch (error) {
        handleStartupError(error);
    }
});

// Quit when all windows are closed
app.on('window-all-closed', () => {
    killBackend();
    
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
    killBackend();
});

// Handle app quit
app.on('quit', () => {
    killBackend();
});
