//! Kubernetes Failover Automation — Phase 4-2
//! Automatic agent restart, pod disruption budgets, readiness/liveness probes
//! Orchestrates multi-replica deployment with Byzantine fault tolerance

use std::collections::HashMap;
use std::fmt;

/// Pod replica state tracking
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PodState {
    Running,
    Pending,
    Failed,
    Unknown,
}

impl fmt::Display for PodState {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            PodState::Running => write!(f, "Running"),
            PodState::Pending => write!(f, "Pending"),
            PodState::Failed => write!(f, "Failed"),
            PodState::Unknown => write!(f, "Unknown"),
        }
    }
}

/// Pod health status
#[derive(Debug, Clone)]
pub struct PodHealth {
    pub pod_id: String,
    pub state: PodState,
    pub ready: bool,
    pub restarts: u32,
    pub last_readiness_check_ns: u64,
    pub consecutive_failures: u32,
}

impl PodHealth {
    pub fn new(pod_id: String) -> Self {
        PodHealth {
            pod_id,
            state: PodState::Pending,
            ready: false,
            restarts: 0,
            last_readiness_check_ns: 0,
            consecutive_failures: 0,
        }
    }

    pub fn is_healthy(&self) -> bool {
        self.state == PodState::Running && self.ready && self.consecutive_failures < 3
    }

    pub fn record_readiness_check(&mut self, success: bool, now_ns: u64) {
        self.last_readiness_check_ns = now_ns;
        if success {
            self.consecutive_failures = 0;
            self.ready = true;
            self.state = PodState::Running;
        } else {
            self.consecutive_failures += 1;
            if self.consecutive_failures >= 3 {
                self.state = PodState::Failed;
                self.ready = false;
            }
        }
    }

    pub fn time_since_readiness_check(&self, now_ns: u64) -> u64 {
        if now_ns < self.last_readiness_check_ns {
            return 0;
        }
        now_ns - self.last_readiness_check_ns
    }
}

/// Liveness probe for pod heartbeat detection
#[derive(Debug, Clone)]
pub struct LivenessProbe {
    pub pod_id: String,
    pub interval_ns: u64,  // Check every N nanoseconds (default: 10s = 10_000_000_000)
    pub timeout_ns: u64,   // Probe timeout (default: 5s = 5_000_000_000)
    pub failure_threshold: u32, // Restart after N failures (default: 3)
    pub last_check_ns: u64,
    pub failure_count: u32,
}

impl LivenessProbe {
    pub fn new(pod_id: String) -> Self {
        LivenessProbe {
            pod_id,
            interval_ns: 10_000_000_000,   // 10 seconds
            timeout_ns: 5_000_000_000,     // 5 seconds
            failure_threshold: 3,
            last_check_ns: 0,
            failure_count: 0,
        }
    }

    pub fn should_check(&self, now_ns: u64) -> bool {
        if self.last_check_ns == 0 {
            return true;
        }
        now_ns - self.last_check_ns >= self.interval_ns
    }

    pub fn record_result(&mut self, success: bool, now_ns: u64) -> bool {
        self.last_check_ns = now_ns;
        if success {
            self.failure_count = 0;
            false // No restart needed
        } else {
            self.failure_count += 1;
            self.failure_count >= self.failure_threshold // Return true if restart needed
        }
    }

    pub fn needs_restart(&self) -> bool {
        self.failure_count >= self.failure_threshold
    }
}

/// Readiness probe for service traffic routing
#[derive(Debug, Clone)]
pub struct ReadinessProbe {
    pub pod_id: String,
    pub interval_ns: u64,   // Check every N nanoseconds (default: 5s)
    pub success_threshold: u32, // Ready after N successes (default: 1)
    pub failure_threshold: u32, // Not ready after N failures (default: 1)
    pub last_check_ns: u64,
    pub consecutive_successes: u32,
    pub consecutive_failures: u32,
    pub is_ready: bool,
}

impl ReadinessProbe {
    pub fn new(pod_id: String) -> Self {
        ReadinessProbe {
            pod_id,
            interval_ns: 5_000_000_000,    // 5 seconds
            success_threshold: 1,
            failure_threshold: 1,
            last_check_ns: 0,
            consecutive_successes: 0,
            consecutive_failures: 0,
            is_ready: false,
        }
    }

    pub fn should_check(&self, now_ns: u64) -> bool {
        if self.last_check_ns == 0 {
            return true;
        }
        now_ns - self.last_check_ns >= self.interval_ns
    }

    pub fn record_result(&mut self, success: bool) {
        self.consecutive_successes = if success { self.consecutive_successes + 1 } else { 0 };
        self.consecutive_failures = if !success { self.consecutive_failures + 1 } else { 0 };

        if self.consecutive_successes >= self.success_threshold {
            self.is_ready = true;
        } else if self.consecutive_failures >= self.failure_threshold {
            self.is_ready = false;
        }
    }
}

/// Pod Disruption Budget (PDB) for Byzantine fault tolerance
#[derive(Debug, Clone, Copy)]
pub struct PodDisruptionBudget {
    pub min_available: u32,  // Minimum pods that must be available (e.g., 6 for 12-pod cluster)
    pub max_unavailable: u32, // Maximum pods that can be disrupted (e.g., 6 for 12-pod cluster)
}

impl PodDisruptionBudget {
    pub fn new(total_replicas: u32) -> Self {
        // For n > 3f Byzantine tolerance: 8/12 quorum = 2/3 must be available
        let min_available = (total_replicas * 2) / 3;
        let max_unavailable = total_replicas - min_available;

        PodDisruptionBudget {
            min_available,
            max_unavailable,
        }
    }

    pub fn can_disrupt(&self, current_available: u32, pods_to_disrupt: u32) -> bool {
        current_available - pods_to_disrupt >= self.min_available
    }

    pub fn safety_margin(&self, current_available: u32) -> u32 {
        if current_available < self.min_available {
            0
        } else {
            current_available - self.min_available
        }
    }
}

/// Kubernetes failover manager
pub struct FailoverManager {
    pub pods: HashMap<String, PodHealth>,
    pub liveness_probes: HashMap<String, LivenessProbe>,
    pub readiness_probes: HashMap<String, ReadinessProbe>,
    pub pdb: PodDisruptionBudget,
    pub restart_history: Vec<RestartEvent>,
}

#[derive(Debug, Clone)]
pub struct RestartEvent {
    pub pod_id: String,
    pub timestamp_ns: u64,
    pub reason: String,
    pub success: bool,
}

impl FailoverManager {
    pub fn new(total_replicas: u32) -> Self {
        FailoverManager {
            pods: HashMap::new(),
            liveness_probes: HashMap::new(),
            readiness_probes: HashMap::new(),
            pdb: PodDisruptionBudget::new(total_replicas),
            restart_history: Vec::new(),
        }
    }

    pub fn register_pod(&mut self, pod_id: String) {
        self.pods.insert(pod_id.clone(), PodHealth::new(pod_id.clone()));
        self.liveness_probes.insert(pod_id.clone(), LivenessProbe::new(pod_id.clone()));
        self.readiness_probes.insert(pod_id.clone(), ReadinessProbe::new(pod_id.clone()));
    }

    pub fn check_liveness(&mut self, pod_id: &str, success: bool, now_ns: u64) -> bool {
        if let Some(probe) = self.liveness_probes.get_mut(pod_id) {
            let needs_restart = probe.record_result(success, now_ns);
            if needs_restart {
                self.record_restart(pod_id, "Liveness probe failed", now_ns);
            }
            needs_restart
        } else {
            false
        }
    }

    pub fn check_readiness(&mut self, pod_id: &str, success: bool) {
        if let Some(probe) = self.readiness_probes.get_mut(pod_id) {
            probe.record_result(success);
            if let Some(pod) = self.pods.get_mut(pod_id) {
                pod.ready = probe.is_ready;
            }
        }
    }

    pub fn get_healthy_pod_count(&self) -> u32 {
        self.pods.values().filter(|p| p.is_healthy()).count() as u32
    }

    pub fn get_ready_pods(&self) -> Vec<String> {
        self.pods
            .iter()
            .filter(|(_, pod)| pod.ready)
            .map(|(id, _)| id.clone())
            .collect()
    }

    pub fn record_restart(&mut self, pod_id: &str, reason: &str, now_ns: u64) {
        self.restart_history.push(RestartEvent {
            pod_id: pod_id.to_string(),
            timestamp_ns: now_ns,
            reason: reason.to_string(),
            success: true,
        });

        if let Some(pod) = self.pods.get_mut(pod_id) {
            pod.restarts += 1;
        }
    }

    pub fn can_perform_maintenance(&self) -> bool {
        let healthy = self.get_healthy_pod_count();
        self.pdb.can_disrupt(healthy, 1)
    }

    pub fn rolling_restart_plan(&self) -> Vec<String> {
        let mut pods: Vec<_> = self.pods.keys().cloned().collect();
        pods.sort();
        pods
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pod_health_creation() {
        let pod = PodHealth::new("agent-1".to_string());
        assert_eq!(pod.state, PodState::Pending);
        assert!(!pod.ready);
        assert!(!pod.is_healthy());
    }

    #[test]
    fn test_pod_readiness_check() {
        let mut pod = PodHealth::new("agent-1".to_string());
        pod.record_readiness_check(true, 1000);
        assert_eq!(pod.state, PodState::Running);
        assert!(pod.ready);
        assert!(pod.is_healthy());
    }

    #[test]
    fn test_pod_failure_threshold() {
        let mut pod = PodHealth::new("agent-1".to_string());
        for i in 0..3 {
            pod.record_readiness_check(false, 1000 + i as u64);
        }
        assert_eq!(pod.state, PodState::Failed);
        assert!(!pod.is_healthy());
    }

    #[test]
    fn test_liveness_probe_restart_trigger() {
        let mut probe = LivenessProbe::new("agent-1".to_string());
        assert!(!probe.record_result(false, 1000));
        assert!(!probe.record_result(false, 2000));
        assert!(probe.record_result(false, 3000)); // 3rd failure triggers restart
    }

    #[test]
    fn test_readiness_probe_state() {
        let mut probe = ReadinessProbe::new("agent-1".to_string());
        assert!(!probe.is_ready);
        probe.record_result(true);
        assert!(probe.is_ready);
        probe.record_result(false);
        assert!(!probe.is_ready);
    }

    #[test]
    fn test_pdb_safety_calculation() {
        let pdb = PodDisruptionBudget::new(12);
        assert_eq!(pdb.min_available, 8); // 2/3 of 12
        assert_eq!(pdb.max_unavailable, 4); // 1/3 of 12
        assert!(pdb.can_disrupt(9, 1)); // 9 - 1 = 8 >= 8
        assert!(!pdb.can_disrupt(8, 1)); // 8 - 1 = 7 < 8
    }

    #[test]
    fn test_failover_manager_registration() {
        let mut manager = FailoverManager::new(12);
        manager.register_pod("agent-1".to_string());
        manager.register_pod("agent-2".to_string());
        assert_eq!(manager.pods.len(), 2);
    }

    #[test]
    fn test_failover_manager_liveness() {
        let mut manager = FailoverManager::new(12);
        manager.register_pod("agent-1".to_string());
        assert!(!manager.check_liveness("agent-1", true, 1000));
        assert!(manager.check_liveness("agent-1", false, 2000));
        assert!(manager.check_liveness("agent-1", false, 3000));
    }

    #[test]
    fn test_failover_manager_ready_pods() {
        let mut manager = FailoverManager::new(12);
        manager.register_pod("agent-1".to_string());
        manager.register_pod("agent-2".to_string());
        manager.check_readiness("agent-1", true);
        manager.check_readiness("agent-2", false);
        let ready = manager.get_ready_pods();
        assert_eq!(ready.len(), 1);
        assert!(ready.contains(&"agent-1".to_string()));
    }
}
