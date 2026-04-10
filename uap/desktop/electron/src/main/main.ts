const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const { autoUpdater } = require("electron-updater");

let mainWindow: any = null;

/**
 * Setup auto-updates (Phase 4)
 */
function setupAutoUpdates() {
  try {
    autoUpdater.checkForUpdatesAndNotify();

    autoUpdater.on("error", (error: any) => {
      console.error("[AutoUpdater] Error:", error);
    });

    autoUpdater.on("update-available", () => {
      console.log("[AutoUpdater] Update available");
      mainWindow?.webContents.send("update-available");
    });

    autoUpdater.on("update-downloaded", () => {
      console.log("[AutoUpdater] Update downloaded - will install on restart");
      mainWindow?.webContents.send("update-downloaded");
    });

    // Check for updates every 24 hours
    setInterval(
      () => {
        autoUpdater.checkForUpdates();
      },
      24 * 60 * 60 * 1000,
    );
  } catch (error) {
    console.error("[AutoUpdater] Setup failed:", error);
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
    icon: path.join(__dirname, "../../public/icon.png"),
  });

  const isDev = process.env.NODE_ENV === "development";
  const url = isDev
    ? "http://localhost:5173"
    : `file://${path.join(__dirname, "../../dist/index.html")}`;

  mainWindow.loadURL(url);

  if (isDev) mainWindow.webContents.openDevTools();

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// IPC Handlers
ipcMain.handle("check-backend", async () => {
  try {
    const response = await fetch("http://localhost:8001/api/arbitrage/status");
    return response.ok
      ? { status: "connected", running: true }
      : { status: "error", running: false };
  } catch (error) {
    return { status: "offline", running: false, error: String(error) };
  }
});

// App event handlers
app.on("ready", () => {
  createWindow();
  setupAutoUpdates();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (mainWindow === null) {
    createWindow();
  }
});

module.exports = { mainWindow };
