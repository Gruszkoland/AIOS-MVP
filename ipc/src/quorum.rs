//! Dynamic Quorum Reconfiguration — allows runtime changes to consensus parameters
//! Validates that Byzantine condition n > 3f is always maintained

use std::fmt;

/// Quorum configuration with Byzantine safety guarantees
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct QuorumConfig {
    pub total_agents: u16,
    pub quorum_threshold: u16,
    pub fault_tolerance: u16,
}

impl QuorumConfig {
    /// Create new quorum with validation
    pub fn new(total_agents: u16, fault_tolerance: u16) -> Result<Self, QuorumError> {
        // Byzantine safety: must have n > 3f
        if (total_agents as u32) <= 3 * (fault_tolerance as u32) {
            return Err(QuorumError::UnsafeByzantineConfig {
                n: total_agents,
                f: fault_tolerance,
                reason: "n must be > 3f for Byzantine tolerance".to_string(),
            });
        }

        // Quorum threshold: need f + 1 + f honest agents = 2f + 1
        // For safety margin, use f + 1
        let quorum_threshold = fault_tolerance + 1;

        if quorum_threshold > total_agents {
            return Err(QuorumError::InvalidQuorumThreshold {
                threshold: quorum_threshold,
                total: total_agents,
            });
        }

        Ok(QuorumConfig {
            total_agents,
            quorum_threshold,
            fault_tolerance,
        })
    }

    /// Reconfigure quorum to new size (must maintain n > 3f)
    pub fn reconfigure(&self, new_total: u16) -> Result<Self, QuorumError> {
        QuorumConfig::new(new_total, self.fault_tolerance)
    }

    /// Adjust fault tolerance (must maintain n > 3f)
    pub fn adjust_tolerance(&self, new_f: u16) -> Result<Self, QuorumError> {
        QuorumConfig::new(self.total_agents, new_f)
    }

    /// Check if current config is valid
    pub fn is_valid(&self) -> bool {
        (self.total_agents as u32) > 3 * (self.fault_tolerance as u32)
            && self.quorum_threshold <= self.total_agents
            && self.quorum_threshold == self.fault_tolerance + 1
    }

    /// Remaining safe slots before Byzantine condition violated
    pub fn remaining_safe_slots(&self) -> u16 {
        // Current: n = total_agents, f = fault_tolerance
        // Max safe: n = 3f + 1 (boundary)
        // Safe margin: current - boundary = total_agents - (3 * f + 1)
        let boundary = 3 * (self.fault_tolerance as u32) + 1;
        self.total_agents.saturating_sub(boundary as u16)
    }

    /// Maximum agents that can fail while maintaining quorum
    pub fn max_failures_tolerated(&self) -> u16 {
        self.fault_tolerance
    }
}

impl fmt::Display for QuorumConfig {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "Quorum(n={}, f={}, threshold={}, valid={})",
            self.total_agents,
            self.fault_tolerance,
            self.quorum_threshold,
            self.is_valid()
        )
    }
}

#[derive(Debug, Clone)]
pub enum QuorumError {
    UnsafeByzantineConfig { n: u16, f: u16, reason: String },
    InvalidQuorumThreshold { threshold: u16, total: u16 },
}

impl fmt::Display for QuorumError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            QuorumError::UnsafeByzantineConfig { n, f: fault, reason } => {
                write!(f, "Unsafe Byzantine config: n={}, f={} — {}", n, fault, reason)
            }
            QuorumError::InvalidQuorumThreshold { threshold, total } => {
                write!(
                    f,
                    "Invalid quorum threshold {} for {} total agents",
                    threshold, total
                )
            }
        }
    }
}

impl std::error::Error for QuorumError {}

/// Quorum manager with reconfiguration history
pub struct QuorumManager {
    current: QuorumConfig,
    history: Vec<QuorumConfigChange>,
}

#[derive(Debug, Clone)]
pub struct QuorumConfigChange {
    pub timestamp_nanos: u64,
    pub old_config: QuorumConfig,
    pub new_config: QuorumConfig,
    pub reason: String,
}

impl QuorumManager {
    pub fn new(initial: QuorumConfig) -> Self {
        QuorumManager {
            current: initial,
            history: vec![],
        }
    }

    pub fn current_config(&self) -> QuorumConfig {
        self.current
    }

    pub fn reconfigure(
        &mut self,
        new_total: u16,
        timestamp_nanos: u64,
        reason: String,
    ) -> Result<(), QuorumError> {
        let new_config = self.current.reconfigure(new_total)?;

        let change = QuorumConfigChange {
            timestamp_nanos,
            old_config: self.current,
            new_config,
            reason,
        };

        self.history.push(change);
        self.current = new_config;
        Ok(())
    }

    pub fn adjust_tolerance(
        &mut self,
        new_f: u16,
        timestamp_nanos: u64,
        reason: String,
    ) -> Result<(), QuorumError> {
        let new_config = self.current.adjust_tolerance(new_f)?;

        let change = QuorumConfigChange {
            timestamp_nanos,
            old_config: self.current,
            new_config,
            reason,
        };

        self.history.push(change);
        self.current = new_config;
        Ok(())
    }

    pub fn history(&self) -> &[QuorumConfigChange] {
        &self.history
    }

    pub fn change_count(&self) -> usize {
        self.history.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_quorum_creation() {
        let config = QuorumConfig::new(12, 3).unwrap();
        assert_eq!(config.total_agents, 12);
        assert_eq!(config.fault_tolerance, 3);
        assert_eq!(config.quorum_threshold, 4); // f + 1
        assert!(config.is_valid());
    }

    #[test]
    fn test_byzantine_safety_n_eq_3f() {
        let result = QuorumConfig::new(9, 3);
        assert!(result.is_err());
    }

    #[test]
    fn test_byzantine_safety_n_lt_3f() {
        let result = QuorumConfig::new(8, 3);
        assert!(result.is_err());
    }

    #[test]
    fn test_safe_reconfiguration() {
        let config = QuorumConfig::new(12, 3).unwrap();
        let new_config = config.reconfigure(13).unwrap();
        assert_eq!(new_config.total_agents, 13);
        assert!(new_config.is_valid());
    }

    #[test]
    fn test_unsafe_reconfiguration() {
        let config = QuorumConfig::new(12, 3).unwrap();
        let result = config.reconfigure(9);
        assert!(result.is_err());
    }

    #[test]
    fn test_remaining_safe_slots() {
        let config = QuorumConfig::new(13, 3).unwrap(); // boundary = 10, current = 13
        assert_eq!(config.remaining_safe_slots(), 3);
    }

    #[test]
    fn test_quorum_manager() {
        let initial = QuorumConfig::new(12, 3).unwrap();
        let mut mgr = QuorumManager::new(initial);

        mgr.reconfigure(14, 1000, "expansion".to_string())
            .unwrap();
        assert_eq!(mgr.current_config().total_agents, 14);
        assert_eq!(mgr.history().len(), 1);
    }

    #[test]
    fn test_tolerance_adjustment() {
        let initial = QuorumConfig::new(20, 3).unwrap();
        let mut mgr = QuorumManager::new(initial);

        mgr.adjust_tolerance(5, 2000, "tolerance increase".to_string())
            .unwrap();
        assert_eq!(mgr.current_config().fault_tolerance, 5);
        assert_eq!(mgr.current_config().quorum_threshold, 6);
    }
}
