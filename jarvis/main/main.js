/**
 * Electron main process — window lifecycle, IPC, and memory persistence.
 */

const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const { MemoryStore } = require("./memory-store");

let mainWindow = null;
let memoryStore = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 700,
    minWidth: 640,
    minHeight: 480,
    backgroundColor: "#050508",
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, "..", "renderer", "index.html"));

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

function registerIpc() {
  ipcMain.handle("memory:load", () => {
    try {
      return { ok: true, data: memoryStore.load() };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  });

  ipcMain.handle("memory:setName", (_event, name) => {
    try {
      return { ok: true, data: memoryStore.setName(name) };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  });

  ipcMain.handle("memory:setLastGreeting", (_event, greeting) => {
    try {
      return { ok: true, data: memoryStore.setLastGreeting(greeting) };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  });

  ipcMain.handle("memory:addCorrection", (_event, text) => {
    try {
      return { ok: true, data: memoryStore.addCorrection(text) };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  });

  ipcMain.handle("memory:addHistory", (_event, entry) => {
    try {
      return { ok: true, data: memoryStore.addHistory(entry) };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  });

  ipcMain.handle("memory:clear", () => {
    try {
      return { ok: true, data: memoryStore.clear() };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  });
}

app.whenReady().then(() => {
  memoryStore = new MemoryStore(app.getPath("userData"));
  registerIpc();
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

process.on("uncaughtException", (err) => {
  console.error("[main] Uncaught exception:", err);
});

process.on("unhandledRejection", (err) => {
  console.error("[main] Unhandled rejection:", err);
});
