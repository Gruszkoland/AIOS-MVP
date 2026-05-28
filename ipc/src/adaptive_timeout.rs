//! Adaptive Consensus Timeout — load-aware timeout tuning
//! Monitors message latency and queue depth, adjusts timeout to maintain low E2E latency

use std::collections::VecDeque;
use std::fmt;

const MAX_HISTORY_SIZE: usize = 100;
const DEFAULT_BASE_TIMEOUT_NANOS: u64 = 5_000_000; // 5ms base
const DEFAULT_MAX_TIMEOUT_NANOS: u64 = 50_000_000; // 50ms absolute max

/// Adaptive timeout calculator
#[derive(Debug, Clone)]
pub struct TimeoutAdaptor {
    pub base_timeout_nanos: u64,
    pub max_timeout_nanos: u64,
    pub current_timeout_nanos: u64,
    latency_history: VecDeque<u64>,
    queue_depth_history: VecDeque<usize>,
    view_change_count: u32,
}

impl TimeoutAdaptor {
    pub fn new(base_nanos: u64, max_nanos: u64) -> Self {
        TimeoutAdaptor {
            base_timeout_nanos: base_nanos,
            max_timeout_nanos: max_nanos,
            current_timeout_nanos: base_nanos,
            latency_history: VecDeque::new(),
            queue_depth_history: VecDeque::new(),
            view_change_count: 0,
        }
    }

    pub fn default() -> Self {
        TimeoutAdaptor::new(DEFAULT_BASE_TIMEOUT_NANOS, DEFAULT_MAX_TIMEOUT_NANOS)
    }

    /// Record message latency and queue depth, calculate new timeout
    pub fn update(&mut self, message_latency_nanos: u64, queue_depth: usize) -> u64 {
        // Track history (circular buffer)
        if self.latency_history.len() >= MAX_HISTORY_SIZE {
            self.latency_history.pop_front();
            self.queue_depth_history.pop_front();
        }

        self.latency_history.push_back(message_latency_nanos);
        self.queue_depth_history.push_back(queue_depth);

        // Calculate load factor from recent history
        let load_factor = self.calculate_load_factor();

        // New timeout = base × load_factor, clamped to [base, max]
        let new_timeout = (self.base_timeout_nanos as f64 * load_factor) as u64;
        self.current_timeout_nanos = new_timeout.clamp(
            self.base_timeout_nanos,
            self.max_timeout_nanos,
        );

        self.current_timeout_nanos
    }

    /// Calculate load factor from average latency and queue depth
    fn calculate_load_factor(&self) -> f64 {
        if self.latency_history.is_empty() {
            return 1.0;
        }

        // Average latency
        let avg_latency = self.latency_history.iter().sum::<u64>() as f64
            / self.latency_history.len() as f64;

        // Average queue depth
        let avg_queue = self.queue_depth_history.iter().sum::<usize>() as f64
            / self.queue_depth_history.len() as f64;

        // Load factor: normalize by base timeout
        // If avg_latency is near base, load_factor ≈ 1.0
        // If avg_latency is high, load_factor increases
        let latency_ratio = avg_latency / self.base_timeout_nanos as f64;
        let queue_ratio = avg_queue / 10.0; // Normalize: 10 items = 1.0 load

        // Combined load = weighted average
        let load = (latency_ratio * 0.7) + (queue_ratio * 0.3);

        // Clamp to reasonable range [0.5, 3.0] to avoid extreme swings
        load.clamp(0.5, 3.0)
    }

    /// Record view change (indicates timeout triggered)
    pub fn on_view_change(&mut self) {
        self.view_change_count += 1;

        // If view changes frequently (>1 per second at baseline),
        // increase base timeout for recovery phase
        if self.view_change_count > 5 {
            let recovery_timeout = (self.base_timeout_nanos as f64 * 1.5) as u64;
            self.current_timeout_nanos = recovery_timeout.clamp(
                self.base_timeout_nanos,
                self.max_timeout_nanos,
            );
        }
    }

    /// Reset view change count (after stable consensus achieved)
    pub fn reset_on_stability(&mut self) {
        self.view_change_count = 0;
        self.current_timeout_nanos = self.base_timeout_nanos;
    }

    /// Clear history
    pub fn clear_history(&mut self) {
        self.latency_history.clear();
        self.queue_depth_history.clear();
        self.view_change_count = 0;
        self.current_timeout_nanos = self.base_timeout_nanos;
    }

    pub fn average_latency(&self) -> Option<u64> {
        if self.latency_history.is_empty() {
            return None;
        }
        Some(self.latency_history.iter().sum::<u64>() / self.latency_history.len() as u64)
    }

    pub fn average_queue_depth(&self) -> Option<usize> {
        if self.queue_depth_history.is_empty() {
            return None;
        }
        Some(self.queue_depth_history.iter().sum::<usize>() / self.queue_depth_history.len())
    }

    pub fn view_change_frequency(&self) -> u32 {
        self.view_change_count
    }

    pub fn history_size(&self) -> usize {
        self.latency_history.len()
    }
}

impl fmt::Display for TimeoutAdaptor {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "TimeoutAdaptor(base={}ns, current={}ns, max={}ns, view_changes={}, avg_latency={:?}ns)",
            self.base_timeout_nanos,
            self.current_timeout_nanos,
            self.max_timeout_nanos,
            self.view_change_count,
            self.average_latency()
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_creation() {
        let adaptor = TimeoutAdaptor::default();
        assert_eq!(adaptor.base_timeout_nanos, DEFAULT_BASE_TIMEOUT_NANOS);
        assert_eq!(adaptor.current_timeout_nanos, DEFAULT_BASE_TIMEOUT_NANOS);
        assert_eq!(adaptor.view_change_count, 0);
    }

    #[test]
    fn test_low_load_no_increase() {
        let mut adaptor = TimeoutAdaptor::default();

        // Low latency, small queue
        for _ in 0..10 {
            adaptor.update(1_000_000, 1); // 1ms latency, 1 item in queue
        }

        // Timeout should stay near base (load_factor close to 1.0)
        assert!(adaptor.current_timeout_nanos <= adaptor.base_timeout_nanos * 2);
    }

    #[test]
    fn test_high_load_increases_timeout() {
        let mut adaptor = TimeoutAdaptor::default();

        // High latency, deep queue
        for _ in 0..10 {
            adaptor.update(20_000_000, 50); // 20ms latency, 50 items
        }

        // Timeout should increase due to load
        assert!(adaptor.current_timeout_nanos > adaptor.base_timeout_nanos);
    }

    #[test]
    fn test_clamping_to_max() {
        let mut adaptor = TimeoutAdaptor::default();

        // Extreme load
        for _ in 0..20 {
            adaptor.update(50_000_000, 100);
        }

        // Should not exceed max
        assert!(adaptor.current_timeout_nanos <= adaptor.max_timeout_nanos);
    }

    #[test]
    fn test_view_change_recovery() {
        let mut adaptor = TimeoutAdaptor::default();

        // Trigger multiple view changes
        for _ in 0..5 {
            adaptor.on_view_change();
        }

        assert_eq!(adaptor.view_change_count, 5);

        // Should increase timeout on recovery
        let pre_recovery = adaptor.current_timeout_nanos;
        adaptor.on_view_change(); // 6th change triggers recovery
        assert!(adaptor.current_timeout_nanos >= pre_recovery);
    }

    #[test]
    fn test_reset_on_stability() {
        let mut adaptor = TimeoutAdaptor::default();

        // Create some history and view changes
        adaptor.update(10_000_000, 5);
        adaptor.on_view_change();
        adaptor.on_view_change();

        let before = adaptor.current_timeout_nanos;

        // Reset on stability
        adaptor.reset_on_stability();
        assert_eq!(adaptor.current_timeout_nanos, adaptor.base_timeout_nanos);
        assert_eq!(adaptor.view_change_count, 0);
    }

    #[test]
    fn test_average_latency() {
        let mut adaptor = TimeoutAdaptor::default();

        adaptor.update(1_000_000, 1);
        adaptor.update(2_000_000, 2);
        adaptor.update(3_000_000, 3);

        let avg = adaptor.average_latency().unwrap();
        assert_eq!(avg, 2_000_000); // (1+2+3)/3 = 2
    }

    #[test]
    fn test_history_circular_buffer() {
        let mut adaptor = TimeoutAdaptor::default();

        // Fill beyond MAX_HISTORY_SIZE
        for i in 0..MAX_HISTORY_SIZE + 50 {
            adaptor.update((i as u64) * 1_000_000, i);
        }

        // Should only keep MAX_HISTORY_SIZE entries
        assert_eq!(adaptor.history_size(), MAX_HISTORY_SIZE);
    }
}
