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
export {};
//# sourceMappingURL=preload.d.ts.map