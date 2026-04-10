import { useCallback, useRef, useState } from "react";
/**
 * Hook for automatic error recovery with retry logic
 * Useful for API calls, database operations, resource loading
 */
export function useErrorRecovery(maxRetries = 3) {
    const [state, setState] = useState({
        error: null,
        retryCount: 0,
        isRecovering: false,
        hasRecovered: false,
    });
    const retryRef = useRef();
    const execute = useCallback(async (fn) => {
        try {
            setState((prev) => ({ ...prev, isRecovering: true, error: null }));
            await fn();
            setState((prev) => ({
                ...prev,
                isRecovering: false,
                hasRecovered: true,
                retryCount: 0,
            }));
        }
        catch (error) {
            const err = error instanceof Error ? error : new Error(String(error));
            if (state.retryCount < maxRetries) {
                setState((prev) => ({
                    ...prev,
                    retryCount: prev.retryCount + 1,
                    isRecovering: true,
                    error: err,
                }));
                // Exponential backoff retry
                const delay = Math.pow(2, state.retryCount) * 1000;
                setTimeout(() => {
                    if (retryRef.current) {
                        retryRef.current();
                    }
                }, delay);
            }
            else {
                setState((prev) => ({
                    ...prev,
                    error: err,
                    isRecovering: false,
                }));
            }
        }
    }, [state.retryCount, maxRetries]);
    const retry = useCallback(async () => {
        if (retryRef.current) {
            setState((prev) => ({ ...prev, retryCount: 0 }));
            await retryRef.current();
        }
    }, []);
    const reset = useCallback(() => {
        setState({
            error: null,
            retryCount: 0,
            isRecovering: false,
            hasRecovered: false,
        });
    }, []);
    return {
        ...state,
        execute,
        retry,
        reset,
    };
}
/**
 * Hook for circuit breaker pattern
 * Prevents cascading failures by stopping requests when error rate is too high
 */
export function useCircuitBreaker(failureThreshold = 5, resetTimeout = 30000) {
    const [state, setState] = useState({
        isOpen: false,
        failureCount: 0,
        lastFailureTime: 0,
    });
    const recordSuccess = useCallback(() => {
        setState((prev) => ({
            ...prev,
            failureCount: 0,
            isOpen: false,
        }));
    }, []);
    const recordFailure = useCallback(() => {
        setState((prev) => {
            const newCount = prev.failureCount + 1;
            return {
                ...prev,
                failureCount: newCount,
                isOpen: newCount >= failureThreshold,
                lastFailureTime: Date.now(),
            };
        });
    }, [failureThreshold]);
    const attemptReset = useCallback(() => {
        setState((prev) => {
            const timeSinceLastFailure = Date.now() - prev.lastFailureTime;
            if (timeSinceLastFailure > resetTimeout) {
                return {
                    isOpen: false,
                    failureCount: 0,
                    lastFailureTime: 0,
                };
            }
            return prev;
        });
    }, [resetTimeout]);
    return {
        isOpen: state.isOpen,
        failureCount: state.failureCount,
        recordSuccess,
        recordFailure,
        attemptReset,
    };
}
/**
 * Hook for fallback strategy (try primary, fallback to secondary)
 */
export async function withFallback(primary, fallback, onError) {
    try {
        return await primary();
    }
    catch (error) {
        if (onError && error instanceof Error) {
            onError(error);
        }
        return await fallback();
    }
}
//# sourceMappingURL=useErrorRecovery.js.map