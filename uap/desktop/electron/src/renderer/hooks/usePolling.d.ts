/**
 * Custom hook for polling backend with exponential backoff
 * Useful for unreliable or slow connections
 */
export declare function usePolling(callback: () => Promise<void>, interval?: number, enabled?: boolean): void;
/**
 * Hook for managing periodic tasks with cleanup
 */
export declare function useInterval(callback: () => void, delay: number | null, enabled?: boolean): void;
/**
 * Hook for debounced callback (useful for settings changes)
 */
export declare function useDebounce<T>(callback: (value: T) => void, delay?: number): (value: T) => void;
//# sourceMappingURL=usePolling.d.ts.map