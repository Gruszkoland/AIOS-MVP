//! Rate Limiting & DoS Protection — Phase 3-2
//! Token bucket algorithm for per-endpoint and per-IP rate limiting
//! Protects against denial-of-service attacks at consensus layer

use std::collections::HashMap;
use std::fmt;

/// Token bucket for rate limiting
#[derive(Debug, Clone)]
pub struct TokenBucket {
    pub capacity: f64,
    pub tokens: f64,
    pub refill_rate: f64,  // tokens per second
    pub last_refill_nanos: u64,
}

impl TokenBucket {
    pub fn new(capacity: f64, refill_rate: f64, now_nanos: u64) -> Self {
        TokenBucket {
            capacity,
            tokens: capacity, // Start full
            refill_rate,
            last_refill_nanos: now_nanos,
        }
    }

    /// Try to consume `count` tokens; returns true if allowed
    pub fn try_consume(&mut self, count: f64, now_nanos: u64) -> bool {
        self.refill(now_nanos);

        if self.tokens >= count {
            self.tokens -= count;
            true
        } else {
            false
        }
    }

    /// Refill tokens based on elapsed time
    fn refill(&mut self, now_nanos: u64) {
        let elapsed_secs = (now_nanos - self.last_refill_nanos) as f64 / 1_000_000_000.0;
        let tokens_to_add = elapsed_secs * self.refill_rate;
        self.tokens = (self.tokens + tokens_to_add).min(self.capacity);
        self.last_refill_nanos = now_nanos;
    }

    pub fn available_tokens(&mut self, now_nanos: u64) -> f64 {
        self.refill(now_nanos);
        self.tokens
    }
}

/// Rate limiter for endpoints and IPs
pub struct RateLimiter {
    /// Per-endpoint buckets (e.g., "/api/decide" → TokenBucket)
    endpoint_limits: HashMap<String, TokenBucket>,
    /// Per-IP buckets (e.g., "192.168.1.1" → TokenBucket)
    ip_limits: HashMap<String, TokenBucket>,
    /// Global bucket
    global_limit: TokenBucket,
    /// Configuration
    config: RateLimiterConfig,
}

#[derive(Debug, Clone)]
pub struct RateLimiterConfig {
    pub endpoint_capacity: f64,
    pub endpoint_refill_rate: f64, // tokens/sec
    pub ip_capacity: f64,
    pub ip_refill_rate: f64,
    pub global_capacity: f64,
    pub global_refill_rate: f64, // e.g., 10k req/sec = 10000 tokens/sec
}

impl RateLimiterConfig {
    /// Default: 1000 req/sec per endpoint, 5000 req/sec per IP, 10k req/sec global
    pub fn default() -> Self {
        RateLimiterConfig {
            endpoint_capacity: 1000.0,
            endpoint_refill_rate: 1000.0,
            ip_capacity: 5000.0,
            ip_refill_rate: 5000.0,
            global_capacity: 10000.0,
            global_refill_rate: 10000.0,
        }
    }

    /// Strict config: 100 req/sec per endpoint, 1000 per IP, 5k global (anti-DDoS)
    pub fn strict() -> Self {
        RateLimiterConfig {
            endpoint_capacity: 100.0,
            endpoint_refill_rate: 100.0,
            ip_capacity: 1000.0,
            ip_refill_rate: 1000.0,
            global_capacity: 5000.0,
            global_refill_rate: 5000.0,
        }
    }
}

impl RateLimiter {
    pub fn new(config: RateLimiterConfig, now_nanos: u64) -> Self {
        RateLimiter {
            endpoint_limits: HashMap::new(),
            ip_limits: HashMap::new(),
            global_limit: TokenBucket::new(
                config.global_capacity,
                config.global_refill_rate,
                now_nanos,
            ),
            config,
        }
    }

    /// Check if request is allowed (all three limits must pass)
    pub fn is_allowed(&mut self, endpoint: &str, client_ip: &str, now_nanos: u64) -> bool {
        // Check global limit first (cheapest)
        if !self.global_limit.try_consume(1.0, now_nanos) {
            return false;
        }

        // Check endpoint limit
        let endpoint_bucket = self
            .endpoint_limits
            .entry(endpoint.to_string())
            .or_insert_with(|| {
                TokenBucket::new(
                    self.config.endpoint_capacity,
                    self.config.endpoint_refill_rate,
                    now_nanos,
                )
            });

        if !endpoint_bucket.try_consume(1.0, now_nanos) {
            // Refund global token
            self.global_limit.tokens += 1.0;
            return false;
        }

        // Check IP limit
        let ip_bucket = self
            .ip_limits
            .entry(client_ip.to_string())
            .or_insert_with(|| {
                TokenBucket::new(
                    self.config.ip_capacity,
                    self.config.ip_refill_rate,
                    now_nanos,
                )
            });

        if !ip_bucket.try_consume(1.0, now_nanos) {
            // Refund both tokens
            self.global_limit.tokens += 1.0;
            endpoint_bucket.tokens += 1.0;
            return false;
        }

        true
    }

    /// Get remaining capacity for diagnostics
    pub fn capacity_info(&mut self, endpoint: &str, client_ip: &str, now_nanos: u64) -> CapacityInfo {
        let global_tokens = self.global_limit.available_tokens(now_nanos);
        let endpoint_tokens = self
            .endpoint_limits
            .get_mut(endpoint)
            .map(|b| b.available_tokens(now_nanos))
            .unwrap_or(self.config.endpoint_capacity);
        let ip_tokens = self
            .ip_limits
            .get_mut(client_ip)
            .map(|b| b.available_tokens(now_nanos))
            .unwrap_or(self.config.ip_capacity);

        CapacityInfo {
            global_tokens,
            endpoint_tokens,
            ip_tokens,
        }
    }

    pub fn reset(&mut self, now_nanos: u64) {
        self.endpoint_limits.clear();
        self.ip_limits.clear();
        self.global_limit = TokenBucket::new(
            self.config.global_capacity,
            self.config.global_refill_rate,
            now_nanos,
        );
    }
}

#[derive(Debug)]
pub struct CapacityInfo {
    pub global_tokens: f64,
    pub endpoint_tokens: f64,
    pub ip_tokens: f64,
}

impl fmt::Display for CapacityInfo {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "Capacity(global={:.0}, endpoint={:.0}, ip={:.0})",
            self.global_tokens, self.endpoint_tokens, self.ip_tokens
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_token_bucket_consumption() {
        let mut bucket = TokenBucket::new(100.0, 10.0, 1000);
        assert!(bucket.try_consume(50.0, 1000));
        assert_eq!(bucket.tokens, 50.0);
    }

    #[test]
    fn test_token_bucket_refill() {
        let mut bucket = TokenBucket::new(100.0, 10.0, 0);
        bucket.try_consume(80.0, 0); // Use 80 tokens
        assert_eq!(bucket.tokens, 20.0);

        // 1 second later: should gain 10 tokens
        bucket.refill(1_000_000_000);
        assert_eq!(bucket.tokens, 30.0);
    }

    #[test]
    fn test_token_bucket_capacity_limit() {
        let mut bucket = TokenBucket::new(100.0, 1000.0, 0);
        bucket.tokens = 50.0;

        // Even with high refill rate, should not exceed capacity
        bucket.refill(1_000_000_000); // 1 second, gain 1000 tokens
        assert_eq!(bucket.tokens, 100.0); // Capped at capacity
    }

    #[test]
    fn test_rate_limiter_single_request() {
        let config = RateLimiterConfig::default();
        let mut limiter = RateLimiter::new(config, 0);

        assert!(limiter.is_allowed("/api/decide", "192.168.1.1", 0));
    }

    #[test]
    fn test_rate_limiter_exceed_endpoint_limit() {
        let config = RateLimiterConfig {
            endpoint_capacity: 5.0,
            endpoint_refill_rate: 5.0,
            ..RateLimiterConfig::default()
        };
        let mut limiter = RateLimiter::new(config, 0);

        // Exhaust endpoint capacity
        for _ in 0..5 {
            assert!(limiter.is_allowed("/api/decide", "192.168.1.1", 0));
        }

        // 6th request should fail
        assert!(!limiter.is_allowed("/api/decide", "192.168.1.1", 0));
    }

    #[test]
    fn test_rate_limiter_exceed_global_limit() {
        let config = RateLimiterConfig {
            global_capacity: 3.0,
            global_refill_rate: 3.0,
            ..RateLimiterConfig::default()
        };
        let mut limiter = RateLimiter::new(config, 0);

        // 3 requests should succeed
        assert!(limiter.is_allowed("/api/decide", "192.168.1.1", 0));
        assert!(limiter.is_allowed("/api/scan", "192.168.1.2", 0));
        assert!(limiter.is_allowed("/api/status", "192.168.1.3", 0));

        // 4th should fail (global limit)
        assert!(!limiter.is_allowed("/api/other", "192.168.1.4", 0));
    }

    #[test]
    fn test_rate_limiter_refill_recovery() {
        let config = RateLimiterConfig {
            global_capacity: 10.0,
            global_refill_rate: 10.0,
            endpoint_capacity: 10.0,
            endpoint_refill_rate: 10.0,
            ..RateLimiterConfig::default()
        };
        let mut limiter = RateLimiter::new(config, 0);

        // Exhaust global and endpoint
        for _ in 0..10 {
            assert!(limiter.is_allowed("/api/decide", "192.168.1.1", 0));
        }

        assert!(!limiter.is_allowed("/api/decide", "192.168.1.1", 0));

        // Wait 1 second, tokens should refill
        assert!(limiter.is_allowed("/api/decide", "192.168.1.1", 1_000_000_000));
    }

    #[test]
    fn test_strict_config_anti_ddos() {
        let config = RateLimiterConfig::strict();
        let mut limiter = RateLimiter::new(config, 0);

        // With strict limits, even endpoint requests should be limited
        for _ in 0..100 {
            assert!(limiter.is_allowed("/api/decide", "192.168.1.1", 0));
        }

        // 101st should fail
        assert!(!limiter.is_allowed("/api/decide", "192.168.1.1", 0));
    }
}
