pub mod failover;
pub mod k8s_failover;

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
