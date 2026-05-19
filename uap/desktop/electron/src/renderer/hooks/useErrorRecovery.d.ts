export interface ErrorRecoveryState {
    error: Error | null;
    retryCount: number;
    isRecovering: boolean;
    hasRecovered: boolean;
}
/**
 * Hook for automatic error recovery with retry logic
 * Useful for API calls, database operations, resource loading
 */
export declare function useErrorRecovery(maxRetries?: number): {
    execute: (fn: () => Promise<void>) => Promise<void>;
    retry: () => Promise<void>;
    reset: () => void;
    error: Error | null;
    retryCount: number;
    isRecovering: boolean;
    hasRecovered: boolean;
};
/**
 * Hook for circuit breaker pattern
 * Prevents cascading failures by stopping requests when error rate is too high
 */
export declare function useCircuitBreaker(failureThreshold?: number, resetTimeout?: number): {
    isOpen: boolean;
    failureCount: number;
    recordSuccess: () => void;
    recordFailure: () => void;
    attemptReset: () => void;
};
/**
 * Hook for fallback strategy (try primary, fallback to secondary)
 */
export declare function withFallback<T>(primary: () => Promise<T>, fallback: () => Promise<T> | T, onError?: (error: Error) => void): Promise<T>;
//# sourceMappingURL=useErrorRecovery.d.ts.map