import { useEffect, useRef } from "react";
/**
 * Custom hook for polling backend with exponential backoff
 * Useful for unreliable or slow connections
 */
export function usePolling(callback, interval = 3000, enabled = true) {
    const timeoutRef = useRef(null);
    const abortControllerRef = useRef(null);
    useEffect(() => {
        if (!enabled)
            return;
        let retryCount = 0;
        const maxRetries = 3;
        const baseInterval = interval;
        const poll = async () => {
            try {
                abortControllerRef.current = new AbortController();
                const timeoutId = setTimeout(() => abortControllerRef.current?.abort(), baseInterval);
                await callback();
                clearTimeout(timeoutId);
                retryCount = 0; // Reset on success
                timeoutRef.current = setTimeout(poll, baseInterval);
            }
            catch (error) {
                console.warn("Polling error:", error);
                // Exponential backoff: 3s → 6s → 12s
                retryCount = Math.min(retryCount + 1, maxRetries);
                const backoffInterval = baseInterval * Math.pow(2, retryCount - 1);
                timeoutRef.current = setTimeout(poll, backoffInterval);
            }
        };
        poll(); // Start immediately
        return () => {
            if (timeoutRef.current)
                clearTimeout(timeoutRef.current);
            abortControllerRef.current?.abort();
        };
    }, [callback, interval, enabled]);
}
/**
 * Hook for managing periodic tasks with cleanup
 */
export function useInterval(callback, delay, enabled = true) {
    useEffect(() => {
        if (!enabled || delay === null)
            return;
        const intervalId = setInterval(callback, delay);
        return () => clearInterval(intervalId);
    }, [callback, delay, enabled]);
}
/**
 * Hook for debounced callback (useful for settings changes)
 */
export function useDebounce(callback, delay = 500) {
    const timeoutRef = useRef(null);
    return (value) => {
        if (timeoutRef.current)
            clearTimeout(timeoutRef.current);
        timeoutRef.current = setTimeout(() => callback(value), delay);
    };
}
//# sourceMappingURL=usePolling.js.map