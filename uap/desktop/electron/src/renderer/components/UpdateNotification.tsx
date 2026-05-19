import { useEffect, useState } from "react";

/**
 * Component to display update notifications
 */
export function UpdateNotification() {
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [updateDownloaded, setUpdateDownloaded] = useState(false);

  useEffect(() => {
    // Listen for update notifications from main process
    const ipcRenderer = (window as any).__ipcRenderer;

    if (ipcRenderer) {
      ipcRenderer.on("update-available", () => {
        console.log("Update available - downloading...");
        setUpdateAvailable(true);
      });

      ipcRenderer.on("update-downloaded", () => {
        console.log("Update ready to install");
        setUpdateDownloaded(true);
      });
    }

    return () => {
      ipcRenderer?.removeAllListeners("update-available");
      ipcRenderer?.removeAllListeners("update-downloaded");
    };
  }, []);

  const handleInstallUpdate = async () => {
    const ipcRenderer = (window as any).__ipcRenderer;
    if (ipcRenderer) {
      await ipcRenderer.invoke("install-update");
    }
  };

  if (!updateDownloaded) return null;

  return (
    <div className="fixed bottom-4 right-4 bg-blue-500 text-white rounded-lg shadow-lg p-4 flex items-center gap-4">
      <div>
        <p className="font-bold">Update Available</p>
        <p className="text-sm">A new version is ready to install</p>
      </div>
      <button
        onClick={handleInstallUpdate}
        className="px-4 py-2 bg-white text-blue-500 rounded font-bold hover:bg-gray-100 transition"
      >
        Install & Restart
      </button>
    </div>
  );
}

export default UpdateNotification;
