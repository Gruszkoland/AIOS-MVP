import { contextBridge, ipcRenderer } from "electron";
contextBridge.exposeInMainWorld("electron", {
    checkBackend: () => ipcRenderer.invoke("check-backend"),
    onBackendStatus: (callback) => ipcRenderer.on("backend-status", callback),
    platform: process.platform,
    app: {
        version: "2.0.0",
        name: "ADRIAN 369 Systray",
    },
});
//# sourceMappingURL=preload.js.map