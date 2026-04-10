import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
/**
 * Component to display update notifications
 */
export function UpdateNotification() {
    const [updateAvailable, setUpdateAvailable] = useState(false);
    const [updateDownloaded, setUpdateDownloaded] = useState(false);
    useEffect(() => {
        // Listen for update notifications from main process
        const ipcRenderer = window.__ipcRenderer;
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
        const ipcRenderer = window.__ipcRenderer;
        if (ipcRenderer) {
            await ipcRenderer.invoke("install-update");
        }
    };
    if (!updateDownloaded)
        return null;
    return (_jsxs("div", { className: "fixed bottom-4 right-4 bg-blue-500 text-white rounded-lg shadow-lg p-4 flex items-center gap-4", children: [_jsxs("div", { children: [_jsx("p", { className: "font-bold", children: "Update Available" }), _jsx("p", { className: "text-sm", children: "A new version is ready to install" })] }), _jsx("button", { onClick: handleInstallUpdate, className: "px-4 py-2 bg-white text-blue-500 rounded font-bold hover:bg-gray-100 transition", children: "Install & Restart" })] }));
}
export default UpdateNotification;
//# sourceMappingURL=UpdateNotification.js.map