//! AIOS agent swarm — cognitive agent traits and implementations.
//!
//! # Architecture
//!
//! ```text
//! AGENT SWARM (this crate)
//!   tier: meta        → ArchtypHarmonii
//!   tier: adversarial → GlosKrytyka
//!   tier: systemic    → Evolution, RelationalCare
//!   tier: operational → Librarian/SAP/Auditor/Sentinel/Architect/Healer/…
//!         ↓ every decision passes through:
//! ADRION 369 MATRIX (aios-kernel crate)
//!   9 immutable Guardian Laws — G1 Unity … G9 Sustainability
//! ```
//!
//! Personas are **not** Guardian Laws. They operate within the matrix.
//! Adding a persona never modifies `GuardianLaw` in `aios-kernel`.

// ─── Swarm tier ──────────────────────────────────────────────────────────────

/// Tier of an agent within the ADRION 369 swarm hierarchy.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
#[repr(u8)]
pub enum SwarmTier {
    /// Single meta-agent that sees all outputs and harmonizes the swarm.
    Meta = 0,
    /// Adversarial agents whose purpose is systematic critique.
    Adversarial = 1,
    /// Cross-session systemic processes (learning, care).
    Systemic = 2,
    /// Domain-specialist agents (Librarian, SAP, Sentinel …).
    Operational = 3,
}

// ─── Agent criticality ───────────────────────────────────────────────────────

/// Real-time scheduling class of a cognitive agent.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AgentCriticality {
    /// Pure observation — never on the execution path.
    Advisory,
    /// May influence execution within a soft deadline.
    SoftRealtime,
    /// Must never appear on the hard real-time kernel path.
    HardRealtimeForbidden,
}

// ─── Observation / Decision / Error ─────────────────────────────────────────

/// Standardised observation delivered to every cognitive agent each cycle.
#[derive(Debug, Clone, Copy)]
pub struct StandardObservation {
    /// Mean of the current 162D decision vector (proxy for overall alignment).
    pub vector_mean: u8,
    /// Estimated system load (0 = idle, 255 = saturated).
    pub system_load: u8,
    /// Estimated user EBDI arousal (0 = calm, 255 = overwhelmed).
    pub user_arousal: u8,
    /// Monotonic cycle counter.
    pub tick: u64,
}

/// Advisory output from a cognitive agent.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AdvisoryDecision {
    /// Agent recommends proceeding.
    Proceed,
    /// Agent recommends deferring.
    Defer,
    /// Soft warning — logged, not blocking.
    Warn,
    /// Hard veto — blocks if agent has veto authority.
    Veto,
    /// Empathic shortcut triggered (RelationalCare only).
    EmpathicShortcut,
}

/// Errors from agent operations.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AgentError {
    NoObservation,
    InvalidObservation,
    CritiqueTargetMissing,
}

// ─── Core trait ──────────────────────────────────────────────────────────────

/// Trait implemented by every ADRION 369 swarm agent.
pub trait CognitiveAgent {
    type Observation;
    type Decision;
    type Error;

    /// Static agent name (matches `personas.yml` key).
    fn name(&self) -> &'static str;

    /// Swarm tier of this agent.
    fn tier(&self) -> SwarmTier;

    /// Real-time scheduling class.
    fn criticality(&self) -> AgentCriticality;

    /// Receive an observation.
    fn observe(&mut self, input: Self::Observation) -> Result<(), Self::Error>;

    /// Emit a decision.
    fn decide(&mut self) -> Result<Self::Decision, Self::Error>;
}

// ─── Sentinel (operational) ──────────────────────────────────────────────────

/// Operational agent enforcing G4 Causality, G7 Privacy, G8 Nonmaleficence.
pub struct SentinelAgent {
    last: Option<StandardObservation>,
    pub load_veto_threshold: u8,
}

impl SentinelAgent {
    pub const fn new(load_veto_threshold: u8) -> Self {
        Self { last: None, load_veto_threshold }
    }
}

impl CognitiveAgent for SentinelAgent {
    type Observation = StandardObservation;
    type Decision    = AdvisoryDecision;
    type Error       = AgentError;

    fn name(&self) -> &'static str { "SENTINEL" }
    fn tier(&self) -> SwarmTier { SwarmTier::Operational }
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

// ─── RelationalCare (systemic) ───────────────────────────────────────────────

/// Systemic agent monitoring user attention economy.
/// Triggers EmpathicShortcut when user arousal exceeds threshold.
pub struct RelationalCareAgent {
    last: Option<StandardObservation>,
    /// Arousal level above which empathic shortcut is triggered (default: 178 ≈ 70%).
    pub arousal_threshold: u8,
    /// Token budget consumed ratio × 255 (warn at ~217 ≈ 85%).
    pub token_budget_warning: u8,
}

impl RelationalCareAgent {
    pub const fn new(arousal_threshold: u8, token_budget_warning: u8) -> Self {
        Self { last: None, arousal_threshold, token_budget_warning }
    }
}

impl CognitiveAgent for RelationalCareAgent {
    type Observation = StandardObservation;
    type Decision    = AdvisoryDecision;
    type Error       = AgentError;

    fn name(&self) -> &'static str { "RELATIONAL_CARE" }
    fn tier(&self) -> SwarmTier { SwarmTier::Systemic }
    fn criticality(&self) -> AgentCriticality { AgentCriticality::Advisory }

    fn observe(&mut self, input: StandardObservation) -> Result<(), AgentError> {
        self.last = Some(input);
        Ok(())
    }

    fn decide(&mut self) -> Result<AdvisoryDecision, AgentError> {
        let obs = self.last.ok_or(AgentError::NoObservation)?;
        if obs.user_arousal >= self.arousal_threshold {
            Ok(AdvisoryDecision::EmpathicShortcut)
        } else if obs.user_arousal > self.arousal_threshold / 2 {
            Ok(AdvisoryDecision::Warn)
        } else {
            Ok(AdvisoryDecision::Proceed)
        }
    }
}

// ─── ArchetypHarmonii (meta) ─────────────────────────────────────────────────

/// Meta-agent: swarm anchor and collective coherence guardian.
/// Receives aggregated swarm signals; emits Harmony_Score.
pub struct ArchetypHarmonii {
    /// Running mean of swarm-wide scores (0–255).
    swarm_mean_history: [u8; 16],
    head: usize,
    cycle: u64,
}

impl ArchetypHarmonii {
    pub const fn new() -> Self {
        Self { swarm_mean_history: [128u8; 16], head: 0, cycle: 0 }
    }

    /// Feed a new swarm-cycle mean into the rolling window.
    pub fn feed_cycle_mean(&mut self, mean: u8) {
        self.swarm_mean_history[self.head % 16] = mean;
        self.head = self.head.wrapping_add(1);
        self.cycle = self.cycle.wrapping_add(1);
    }

    /// Harmony score: 1.0 = perfect coherence, 0.0 = chaotic.
    /// Computed as 1 - (normalised standard deviation of rolling window).
    pub fn harmony_score(&self) -> f32 {
        let n = 16usize;
        let mean: f32 = self.swarm_mean_history.iter().map(|&v| v as f32).sum::<f32>() / n as f32;
        let variance: f32 = self.swarm_mean_history
            .iter()
            .map(|&v| { let d = v as f32 - mean; d * d })
            .sum::<f32>() / n as f32;
        let std_dev = variance.sqrt();
        // Normalise: max possible std_dev for u8 is ~127
        let normalised_std = std_dev / 127.0;
        (1.0 - normalised_std).max(0.0).min(1.0)
    }

    /// Returns true if swarm drift exceeds the ADRION 369 threshold (0.35).
    pub fn drift_detected(&self) -> bool {
        self.harmony_score() < 0.65
    }
}

impl CognitiveAgent for ArchetypHarmonii {
    type Observation = StandardObservation;
    type Decision    = AdvisoryDecision;
    type Error       = AgentError;

    fn name(&self) -> &'static str { "ARCHETYP_HARMONII" }
    fn tier(&self) -> SwarmTier { SwarmTier::Meta }
    fn criticality(&self) -> AgentCriticality { AgentCriticality::Advisory }

    fn observe(&mut self, input: StandardObservation) -> Result<(), AgentError> {
        self.feed_cycle_mean(input.vector_mean);
        Ok(())
    }

    fn decide(&mut self) -> Result<AdvisoryDecision, AgentError> {
        if self.drift_detected() {
            Ok(AdvisoryDecision::Warn)
        } else {
            Ok(AdvisoryDecision::Proceed)
        }
    }
}

impl Default for ArchetypHarmonii {
    fn default() -> Self { Self::new() }
}

// ─── GlosKrytyka (adversarial) ───────────────────────────────────────────────

/// Adversarial agent implementing the Socratic critique protocol.
/// Does not propose alternatives — only surfaces unverified assumptions.
pub struct GlosKrytyka {
    critique_count: u32,
}

impl GlosKrytyka {
    pub const fn new() -> Self { Self { critique_count: 0 } }

    /// Number of critique cycles completed.
    pub fn critique_count(&self) -> u32 { self.critique_count }
}

impl CognitiveAgent for GlosKrytyka {
    type Observation = StandardObservation;
    type Decision    = AdvisoryDecision;
    type Error       = AgentError;

    fn name(&self) -> &'static str { "GLOS_KRYTYKA" }
    fn tier(&self) -> SwarmTier { SwarmTier::Adversarial }
    fn criticality(&self) -> AgentCriticality { AgentCriticality::Advisory }

    fn observe(&mut self, _: StandardObservation) -> Result<(), AgentError> {
        self.critique_count = self.critique_count.saturating_add(1);
        Ok(())
    }

    /// Always defers — Głos Krytyka never approves unilaterally.
    /// Its "decision" is always to surface questions, represented as Defer.
    fn decide(&mut self) -> Result<AdvisoryDecision, AgentError> {
        Ok(AdvisoryDecision::Defer)
    }
}

impl Default for GlosKrytyka { fn default() -> Self { Self::new() } }

// ─── Evolution (systemic) ────────────────────────────────────────────────────

/// Systemic PME (Poor Man's Evolution) agent.
/// Transforms HIGH/CRITICAL errors into persistent heuristics.
/// Runs post-session, never on the real-time path.
pub struct EvolutionAgent {
    heuristics_learned: u32,
    last_tspa_delta: f32,
}

impl EvolutionAgent {
    pub const fn new() -> Self {
        Self { heuristics_learned: 0, last_tspa_delta: 0.0 }
    }

    /// Register a new validated heuristic.
    pub fn commit_heuristic(&mut self, improvement_delta: f32) {
        self.heuristics_learned = self.heuristics_learned.saturating_add(1);
        self.last_tspa_delta = improvement_delta;
    }

    /// Total heuristics learned across all sessions.
    pub fn heuristics_learned(&self) -> u32 { self.heuristics_learned }

    /// TSPA delta from last session (positive = improvement).
    pub fn last_tspa_delta(&self) -> f32 { self.last_tspa_delta }
}

impl CognitiveAgent for EvolutionAgent {
    type Observation = StandardObservation;
    type Decision    = AdvisoryDecision;
    type Error       = AgentError;

    fn name(&self) -> &'static str { "EVOLUTION" }
    fn tier(&self) -> SwarmTier { SwarmTier::Systemic }
    fn criticality(&self) -> AgentCriticality { AgentCriticality::Advisory }

    fn observe(&mut self, _: StandardObservation) -> Result<(), AgentError> { Ok(()) }

    fn decide(&mut self) -> Result<AdvisoryDecision, AgentError> {
        Ok(AdvisoryDecision::Proceed)
    }
}

impl Default for EvolutionAgent { fn default() -> Self { Self::new() } }

// ─── Tests ───────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    fn obs(load: u8, arousal: u8) -> StandardObservation {
        StandardObservation { vector_mean: 128, system_load: load, user_arousal: arousal, tick: 0 }
    }

    // ── Tier ordering ────────────────────────────────────────────────────────
    #[test]
    fn tier_ordering_meta_is_lowest() {
        assert!(SwarmTier::Meta < SwarmTier::Operational);
        assert!(SwarmTier::Adversarial < SwarmTier::Operational);
        assert!(SwarmTier::Systemic < SwarmTier::Operational);
    }

    // ── Sentinel ─────────────────────────────────────────────────────────────
    #[test]
    fn sentinel_proceeds_on_low_load() {
        let mut s = SentinelAgent::new(200);
        s.observe(obs(50, 0)).unwrap();
        assert_eq!(s.decide().unwrap(), AdvisoryDecision::Proceed);
    }

    #[test]
    fn sentinel_vetos_overload() {
        let mut s = SentinelAgent::new(200);
        s.observe(obs(250, 0)).unwrap();
        assert_eq!(s.decide().unwrap(), AdvisoryDecision::Veto);
    }

    #[test]
    fn sentinel_warns_mid_range() {
        let mut s = SentinelAgent::new(200);
        s.observe(obs(150, 0)).unwrap();
        assert_eq!(s.decide().unwrap(), AdvisoryDecision::Warn);
    }

    #[test]
    fn sentinel_tier_is_operational() {
        assert_eq!(SentinelAgent::new(200).tier(), SwarmTier::Operational);
    }

    // ── RelationalCare ───────────────────────────────────────────────────────
    #[test]
    fn relational_care_empathic_shortcut_on_high_arousal() {
        let mut rc = RelationalCareAgent::new(178, 217);
        rc.observe(obs(0, 200)).unwrap();
        assert_eq!(rc.decide().unwrap(), AdvisoryDecision::EmpathicShortcut);
    }

    #[test]
    fn relational_care_proceeds_on_calm_user() {
        let mut rc = RelationalCareAgent::new(178, 217);
        rc.observe(obs(0, 50)).unwrap();
        assert_eq!(rc.decide().unwrap(), AdvisoryDecision::Proceed);
    }

    #[test]
    fn relational_care_tier_is_systemic() {
        assert_eq!(RelationalCareAgent::new(178, 217).tier(), SwarmTier::Systemic);
    }

    // ── ArchetypHarmonii ─────────────────────────────────────────────────────
    #[test]
    fn archetyp_harmonii_stable_swarm_high_score() {
        let mut ah = ArchetypHarmonii::new();
        for _ in 0..16 { ah.feed_cycle_mean(200); }
        let score = ah.harmony_score();
        assert!(score > 0.95, "uniform swarm should score high: {}", score);
    }

    #[test]
    fn archetyp_harmonii_chaotic_swarm_triggers_warn() {
        let mut ah = ArchetypHarmonii::new();
        for i in 0..16u8 { ah.feed_cycle_mean(if i % 2 == 0 { 10 } else { 245 }); }
        assert_eq!(ah.decide().unwrap(), AdvisoryDecision::Warn);
    }

    #[test]
    fn archetyp_harmonii_drift_detected_below_threshold() {
        let mut ah = ArchetypHarmonii::new();
        for i in 0..16u8 { ah.feed_cycle_mean(if i % 2 == 0 { 10 } else { 245 }); }
        assert!(ah.drift_detected());
    }

    #[test]
    fn archetyp_harmonii_tier_is_meta() {
        assert_eq!(ArchetypHarmonii::new().tier(), SwarmTier::Meta);
    }

    #[test]
    fn archetyp_harmonii_meta_is_highest_priority() {
        assert!(ArchetypHarmonii::new().tier() < SentinelAgent::new(200).tier());
    }

    // ── GlosKrytyka ──────────────────────────────────────────────────────────
    #[test]
    fn glos_krytyka_always_defers() {
        let mut gk = GlosKrytyka::new();
        gk.observe(obs(100, 100)).unwrap();
        assert_eq!(gk.decide().unwrap(), AdvisoryDecision::Defer);
    }

    #[test]
    fn glos_krytyka_tier_is_adversarial() {
        assert_eq!(GlosKrytyka::new().tier(), SwarmTier::Adversarial);
    }

    #[test]
    fn glos_krytyka_counts_observations() {
        let mut gk = GlosKrytyka::new();
        for _ in 0..5 { gk.observe(obs(0, 0)).unwrap(); }
        assert_eq!(gk.critique_count(), 5);
    }

    // ── Evolution ────────────────────────────────────────────────────────────
    #[test]
    fn evolution_tracks_heuristics() {
        let mut ev = EvolutionAgent::new();
        assert_eq!(ev.heuristics_learned(), 0);
        ev.commit_heuristic(0.12);
        ev.commit_heuristic(0.08);
        assert_eq!(ev.heuristics_learned(), 2);
        assert!((ev.last_tspa_delta() - 0.08).abs() < 1e-6);
    }

    #[test]
    fn evolution_tier_is_systemic() {
        assert_eq!(EvolutionAgent::new().tier(), SwarmTier::Systemic);
    }
}

