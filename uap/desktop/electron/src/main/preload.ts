import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("electron", {
  checkBackend: () => ipcRenderer.invoke("check-backend"),

  onBackendStatus: (callback: (event: any, data: any) => void) =>
    ipcRenderer.on("backend-status", callback),

  platform: process.platform,
  app: {
    version: "2.0.0",
    name: "ADRIAN 369 Systray",
  },
});

// Declare types for TypeScript
declare global {
  interface Window {
    electron: {
      checkBackend: () => Promise<{
        status: string;
        running: boolean;
        error?: string;
      }>;
      onBackendStatus: (callback: (event: any, data: any) => void) => void;
      platform: string;
      app: {
        version: string;
        name: string;
      };
    };
  }
}
