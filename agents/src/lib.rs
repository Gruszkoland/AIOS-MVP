/// Criticality level — agents must NEVER block the kernel critical path.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AgentCriticality {
    /// Agent provides async suggestions only.
    Advisory,
    /// Agent may be consulted in soft real-time loops (~100ms budget).
    SoftRealtime,
    /// Kernel hard real-time path — LLM calls are FORBIDDEN here.
    HardRealtimeForbidden,
}

/// Minimal contract for all AIOS cognitive agents.
/// See: docs/rfcs/0001-cognitive-agent-trait.md
pub trait CognitiveAgent {
    type Observation;
    type Decision;
    type Error;

    fn name(&self) -> &'static str;
    fn criticality(&self) -> AgentCriticality;
    fn observe(&mut self, input: Self::Observation) -> Result<(), Self::Error>;
    fn decide(&mut self) -> Result<Self::Decision, Self::Error>;
}

/// Standard observation passed to every cognitive agent.
#[derive(Debug, Clone, Copy)]
pub struct StandardObservation {
    /// Snapshot of the 162D decision vector at observation time.
    pub vector_mean: u8,
    /// Current system load (0 = idle, 255 = saturated).
    pub system_load: u8,
    /// Monotonic tick counter.
    pub tick: u64,
}

/// Advisory decision emitted by a cognitive agent.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AdvisoryDecision {
    /// Agent recommends proceeding.
    Proceed,
    /// Agent recommends deferring to another agent or human.
    Defer,
    /// Agent raises a soft warning (logged, not blocking).
    Warn,
    /// Agent raises a hard veto (blocks if agent has veto power).
    Veto,
}

/// Concrete error type for agent operations.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AgentError {
    /// The agent has not yet received an observation.
    NoObservation,
    /// The observation was malformed or out of expected range.
    InvalidObservation,
}

/// A simple stateless sentinel guardian implementation.
pub struct SentinelGuardian {
    last: Option<StandardObservation>,
    /// Threshold above which system load triggers a veto.
    pub load_veto_threshold: u8,
}

impl SentinelGuardian {
    /// Creates a new `SentinelGuardian` with the given load veto threshold.
    pub const fn new(load_veto_threshold: u8) -> Self {
        Self { last: None, load_veto_threshold }
    }
}

impl CognitiveAgent for SentinelGuardian {
    type Observation = StandardObservation;
    type Decision    = AdvisoryDecision;
    type Error       = AgentError;

    fn name(&self) -> &'static str { "Sentinel" }

    fn criticality(&self) -> AgentCriticality { AgentCriticality::HardRealtimeForbidden }

    fn observe(&mut self, input: StandardObservation) -> Result<(), AgentError> {
        self.last = Some(input);
        Ok(())
    }

    fn decide(&mut self) -> Result<AdvisoryDecision, AgentError> {
        let obs = self.last.ok_or(AgentError::NoObservation)?;
        if obs.system_load >= self.load_veto_threshold {
            Ok(AdvisoryDecision::Veto)
        } else if obs.system_load > self.load_veto_threshold / 2 {
            Ok(AdvisoryDecision::Warn)
        } else {
            Ok(AdvisoryDecision::Proceed)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sentinel_proceeds_on_low_load() {
        let mut s = SentinelGuardian::new(200);
        s.observe(StandardObservation { vector_mean: 128, system_load: 50, tick: 0 }).unwrap();
        assert_eq!(s.decide().unwrap(), AdvisoryDecision::Proceed);
    }

    #[test]
    fn sentinel_vetos_on_overload() {
        let mut s = SentinelGuardian::new(200);
        s.observe(StandardObservation { vector_mean: 128, system_load: 250, tick: 1 }).unwrap();
        assert_eq!(s.decide().unwrap(), AdvisoryDecision::Veto);
    }

    #[test]
    fn sentinel_warns_in_mid_range() {
        let mut s = SentinelGuardian::new(200);
        s.observe(StandardObservation { vector_mean: 128, system_load: 150, tick: 2 }).unwrap();
        assert_eq!(s.decide().unwrap(), AdvisoryDecision::Warn);
    }

    #[test]
    fn no_observation_returns_error() {
        let mut s = SentinelGuardian::new(200);
        assert_eq!(s.decide(), Err(AgentError::NoObservation));
    }

    #[test]
    fn agent_name_is_correct() {
        let s = SentinelGuardian::new(200);
        assert_eq!(s.name(), "Sentinel");
    }

    #[test]
    fn criticality_is_hard_realtime_forbidden() {
        let s = SentinelGuardian::new(200);
        assert_eq!(s.criticality(), AgentCriticality::HardRealtimeForbidden);
    }
}
