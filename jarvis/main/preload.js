/**
 * Preload — exposes a safe API bridge to the renderer.
 */

const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("jarvis", {
  memory: {
    load: () => ipcRenderer.invoke("memory:load"),
    setName: (name) => ipcRenderer.invoke("memory:setName", name),
    setLastGreeting: (greeting) => ipcRenderer.invoke("memory:setLastGreeting", greeting),
    addCorrection: (text) => ipcRenderer.invoke("memory:addCorrection", text),
    addHistory: (entry) => ipcRenderer.invoke("memory:addHistory", entry),
    clear: () => ipcRenderer.invoke("memory:clear"),
  },
});
