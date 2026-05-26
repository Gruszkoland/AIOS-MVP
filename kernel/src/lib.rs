#![no_std]
#![deny(unsafe_op_in_unsafe_fn)]
#![warn(missing_docs)]

//! AIOS Kernel — deterministic `no_std` core.
//!
//! Implements the 162-dimensional decision topology from the ADRION 369
//! moral framework:
//!
//! ```text
//! D^162 = P^3 (Trinity) × H^6 (Hexagon) × G^9 (Guardian Laws)
//! ```
//!
//! # Layer overview
//!
//! | Layer | Axis | Count | Examples |
//! |-------|------|-------|---------|
//! | Trinity perspectives | P^3 | 3 | Material, Intellectual, Essential |
//! | Hexagon pipeline stages | H^6 | 6 | Inventory … Action — **NOT guardians** |
//! | Guardian Laws | G^9 | 9 | Unity … Sustainability (canonical) |
//!
//! G10 (Evolution) and G11 (RelationalCare) are runtime extensions active in
//! the Python layer — they are not part of the 162D tensor product.

// ─── Trinity perspectives (P^3, not guardians) ──────────────────────────────

/// The three top-level scoring perspectives.
/// These are **not** Guardian Laws — they form the P^3 axis of D^162.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum TrinityPerspective {
    /// P1 — Physical resources, energy, compute availability.
    Material = 0,
    /// P2 — Logical coherence, truth verification, elegance.
    Intellectual = 1,
    /// P3 — Mission alignment, ethics compliance.
    Essential = 2,
}

impl TrinityPerspective {
    /// Offset into a `DecisionVector` for this perspective's 54 dimensions.
    #[inline]
    pub const fn offset(self) -> usize {
        self as usize * 18
    }
}

// ─── Hexagon pipeline stages (H^6, not guardians) ───────────────────────────

/// The six sequential decision-pipeline stages.
/// These are **not** Guardian Laws — they form the H^6 axis of D^162.
/// Previously mislabelled as "6 Guardian Personas" in documentation.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum HexagonStage {
    /// H1 — Inventory: analyse available resources and assets.
    Inventory = 0,
    /// H2 — Empathy: assess stakeholder impact and social reality.
    Empathy = 1,
    /// H3 — Process: optimise workflow and execution.
    Process = 2,
    /// H4 — Debate: multi-perspective confrontation of results.
    Debate = 3,
    /// H5 — Healing: risk mitigation and crisis preparation.
    Healing = 4,
    /// H6 — Action: final recommendation and deployment plan.
    Action = 5,
}

impl HexagonStage {
    /// Offset into a `DecisionVector` for this stage's 27 dimensions.
    #[inline]
    pub const fn offset(self) -> usize {
        54 + self as usize * 9
    }
}

// ─── Guardian Laws (G^9, canonical) ─────────────────────────────────────────

/// The nine canonical Guardian Laws of ADRION 369 (G1–G9).
///
/// Each variant has two names:
/// - The **law name** (abstract ethical principle, used in GUARDIAN_LAWS_CANONICAL.json)
/// - The **persona alias** (operational agent that enforces it, used in LAWS.md)
///
/// G10 (Evolution) and G11 (RelationalCare) exist as runtime extensions in the
/// Python layer but are not represented here — they are outside the canonical 9.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum GuardianLaw {
    /// G1 — Unity (persona: Librarian). All actions serve system coherence.
    Unity = 0,
    /// G2 — Harmony (persona: SAP). Balance competing objectives; genuine analysis.
    Harmony = 1,
    /// G3 — Rhythm (persona: Auditor). Consistent cadence and timing.
    Rhythm = 2,
    /// G4 — Causality (persona: Sentinel). Every action has a traceable cause.
    Causality = 3,
    /// G5 — Transparency (persona: Architect). Decisions visible and auditable.
    Transparency = 4,
    /// G6 — Authenticity (persona: Healer). Outputs genuine, non-deceptive.
    Authenticity = 5,
    /// G7 — Privacy (persona: system-wide). CRITICAL — veto power.
    Privacy = 6,
    /// G8 — Nonmaleficence (persona: system-wide). CRITICAL — veto power.
    Nonmaleficence = 7,
    /// G9 — Sustainability (persona: system-wide). Long-term resource health.
    Sustainability = 8,
}

impl GuardianLaw {
    /// Returns the slice offset into a `DecisionVector` for this law (6 dims).
    #[inline]
    pub const fn offset(self) -> usize {
        108 + self as usize * 6
    }

    /// Severity-based criticality weight for consensus scoring.
    /// CRITICAL = 10, HIGH = 2, MEDIUM = 1.
    #[inline]
    pub const fn criticality(self) -> u32 {
        match self {
            GuardianLaw::Privacy | GuardianLaw::Nonmaleficence => 10, // CRITICAL
            GuardianLaw::Causality
            | GuardianLaw::Authenticity
            | GuardianLaw::Sustainability => 2, // HIGH
            _ => 1, // MEDIUM
        }
    }

    /// Whether this guardian holds hard veto power over any decision.
    #[inline]
    pub const fn has_veto(self) -> bool {
        matches!(self, GuardianLaw::Privacy | GuardianLaw::Nonmaleficence)
    }

    /// Human-readable persona alias for this law.
    pub const fn persona_alias(self) -> &'static str {
        match self {
            GuardianLaw::Unity => "Librarian",
            GuardianLaw::Harmony => "SAP",
            GuardianLaw::Rhythm => "Auditor",
            GuardianLaw::Causality => "Sentinel",
            GuardianLaw::Transparency => "Architect",
            GuardianLaw::Authenticity => "Healer",
            GuardianLaw::Privacy | GuardianLaw::Nonmaleficence | GuardianLaw::Sustainability => {
                "system-wide"
            }
        }
    }
}

// ─── Decision vector ─────────────────────────────────────────────────────────

/// A 162-dimensional fixed-size decision vector.
///
/// Layout:
/// - `[0..54]`    — Trinity × mode weights (3 perspectives × 18 dims each)
/// - `[54..108]`  — Hexagon × guardian weights (6 stages × 9 dims each)
/// - `[108..162]` — Guardian × stage scores (9 laws × 6 dims each)
#[derive(Clone, Copy)]
pub struct DecisionVector {
    data: [u8; 162],
}

impl DecisionVector {
    /// Creates a zeroed decision vector.
    #[inline]
    pub const fn zeroed() -> Self {
        Self { data: [0u8; 162] }
    }

    /// Creates a uniform vector with all weights set to `value`.
    #[inline]
    pub const fn uniform(value: u8) -> Self {
        Self { data: [value; 162] }
    }

    /// Returns the raw value at `index`.
    #[inline]
    pub fn get(&self, index: usize) -> u8 {
        self.data[index]
    }

    /// Sets the raw value at `index`.
    #[inline]
    pub fn set(&mut self, index: usize, value: u8) {
        self.data[index] = value;
    }

    /// Sets 6 scores for a given `GuardianLaw`.
    pub fn set_guardian_scores(&mut self, g: GuardianLaw, scores: [u8; 6]) {
        let off = g.offset();
        self.data[off..off + 6].copy_from_slice(&scores);
    }

    /// Sets 18 weights for a given `TrinityPerspective`.
    pub fn set_trinity_weights(&mut self, p: TrinityPerspective, weights: [u8; 18]) {
        let off = p.offset();
        self.data[off..off + 18].copy_from_slice(&weights);
    }

    /// Sets 9 weights for a given `HexagonStage`.
    pub fn set_hexagon_weights(&mut self, h: HexagonStage, weights: [u8; 9]) {
        let off = h.offset();
        self.data[off..off + 9].copy_from_slice(&weights);
    }

    /// L1 norm (sum of all 162 components).
    pub fn l1_norm(&self) -> u32 {
        self.data.iter().map(|&b| b as u32).sum()
    }

    /// Unweighted mean scaled to [0, 255].
    pub fn mean(&self) -> u8 {
        (self.l1_norm() / 162) as u8
    }

    /// Normalised f32 for a single dimension (0.0..=1.0).
    pub fn normalised(&self, index: usize) -> f32 {
        self.data[index] as f32 / 255.0
    }
}

// ─── Consensus engine ────────────────────────────────────────────────────────

/// Possible outcomes of the ADRION 369 consensus algorithm.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ConsensusVerdict {
    /// All guardians approve — action is permitted.
    Approve,
    /// Weighted score below threshold — action is denied.
    Deny,
    /// A veto-holding guardian (G7 Privacy or G8 Nonmaleficence) hard-blocked.
    VetoDeny,
    /// Score inconclusive — defer to human oversight.
    DeferToHuman,
}

/// Computes a weighted consensus verdict across all 9 canonical Guardian Laws.
#[must_use]
pub fn compute_consensus(v: &DecisionVector) -> ConsensusVerdict {
    const APPROVE_THRESHOLD: u32 = 178; // ~70% of 255
    const DENY_THRESHOLD: u32 = 76;     // ~30% of 255
    const VETO_FLOOR: u8 = 64;          // ~25% — hard veto floor

    const LAWS: [GuardianLaw; 9] = [
        GuardianLaw::Unity,
        GuardianLaw::Harmony,
        GuardianLaw::Rhythm,
        GuardianLaw::Causality,
        GuardianLaw::Transparency,
        GuardianLaw::Authenticity,
        GuardianLaw::Privacy,
        GuardianLaw::Nonmaleficence,
        GuardianLaw::Sustainability,
    ];

    let mut total_weighted: u64 = 0;
    let mut max_possible: u64 = 0;

    for law in LAWS {
        let off = law.offset();
        let scores = &v.data[off..off + 6];
        let sum: u32 = scores.iter().map(|&s| s as u32).sum();
        let mean6 = (sum / 6) as u8;

        if law.has_veto() && mean6 < VETO_FLOOR {
            return ConsensusVerdict::VetoDeny;
        }

        let w = law.criticality() as u64;
        total_weighted += sum as u64 * w;
        max_possible += 255 * 6 * w;
    }

    let ratio = (total_weighted * 255 / max_possible) as u32;

    if ratio >= APPROVE_THRESHOLD {
        ConsensusVerdict::Approve
    } else if ratio <= DENY_THRESHOLD {
        ConsensusVerdict::Deny
    } else {
        ConsensusVerdict::DeferToHuman
    }
}

// ─── Tests ───────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zeroed_vector_veto_fires() {
        let v = DecisionVector::zeroed();
        assert_eq!(compute_consensus(&v), ConsensusVerdict::VetoDeny);
    }

    #[test]
    fn uniform_high_is_approve() {
        let v = DecisionVector::uniform(220);
        assert_eq!(compute_consensus(&v), ConsensusVerdict::Approve);
    }

    #[test]
    fn veto_fires_on_privacy_law() {
        let mut v = DecisionVector::uniform(200);
        v.set_guardian_scores(GuardianLaw::Privacy, [10; 6]);
        assert_eq!(compute_consensus(&v), ConsensusVerdict::VetoDeny);
    }

    #[test]
    fn veto_fires_on_nonmaleficence_law() {
        let mut v = DecisionVector::uniform(200);
        v.set_guardian_scores(GuardianLaw::Nonmaleficence, [10; 6]);
        assert_eq!(compute_consensus(&v), ConsensusVerdict::VetoDeny);
    }

    #[test]
    fn no_veto_mid_range_defers() {
        let mut v = DecisionVector::zeroed();
        v.set_guardian_scores(GuardianLaw::Privacy, [128; 6]);
        v.set_guardian_scores(GuardianLaw::Nonmaleficence, [128; 6]);
        for law in [GuardianLaw::Unity, GuardianLaw::Harmony, GuardianLaw::Rhythm,
                    GuardianLaw::Causality, GuardianLaw::Transparency,
                    GuardianLaw::Authenticity, GuardianLaw::Sustainability] {
            v.set_guardian_scores(law, [80; 6]);
        }
        let verdict = compute_consensus(&v);
        assert!(matches!(verdict, ConsensusVerdict::DeferToHuman | ConsensusVerdict::Deny));
    }

    #[test]
    fn guardian_law_names_match_canonical() {
        assert_eq!(GuardianLaw::Unity.persona_alias(), "Librarian");
        assert_eq!(GuardianLaw::Harmony.persona_alias(), "SAP");
        assert_eq!(GuardianLaw::Rhythm.persona_alias(), "Auditor");
        assert_eq!(GuardianLaw::Causality.persona_alias(), "Sentinel");
        assert_eq!(GuardianLaw::Transparency.persona_alias(), "Architect");
        assert_eq!(GuardianLaw::Authenticity.persona_alias(), "Healer");
    }

    #[test]
    fn only_g7_g8_have_veto() {
        let veto_laws = [GuardianLaw::Privacy, GuardianLaw::Nonmaleficence];
        let non_veto = [
            GuardianLaw::Unity, GuardianLaw::Harmony, GuardianLaw::Rhythm,
            GuardianLaw::Causality, GuardianLaw::Transparency, GuardianLaw::Authenticity,
            GuardianLaw::Sustainability,
        ];
        for law in veto_laws { assert!(law.has_veto(), "{:?} should have veto", law); }
        for law in non_veto { assert!(!law.has_veto(), "{:?} should not have veto", law); }
    }

    #[test]
    fn criticality_weights_match_canonical() {
        assert_eq!(GuardianLaw::Privacy.criticality(), 10);
        assert_eq!(GuardianLaw::Nonmaleficence.criticality(), 10);
        assert_eq!(GuardianLaw::Causality.criticality(), 2);
        assert_eq!(GuardianLaw::Authenticity.criticality(), 2);
        assert_eq!(GuardianLaw::Sustainability.criticality(), 2);
        assert_eq!(GuardianLaw::Unity.criticality(), 1);
    }

    #[test]
    fn hexagon_stages_are_not_guardians_distinct_offsets() {
        assert_eq!(HexagonStage::Inventory.offset(), 54);
        assert_eq!(HexagonStage::Action.offset(), 99);
        assert_eq!(GuardianLaw::Unity.offset(), 108);
        assert_ne!(HexagonStage::Action.offset(), GuardianLaw::Unity.offset());
    }

    #[test]
    fn trinity_perspectives_are_not_guardians_distinct_offsets() {
        assert_eq!(TrinityPerspective::Material.offset(), 0);
        assert_eq!(TrinityPerspective::Essential.offset(), 36);
        assert_eq!(GuardianLaw::Unity.offset(), 108);
    }

    #[test]
    fn set_and_get_roundtrip() {
        let mut v = DecisionVector::zeroed();
        v.set(100, 77);
        assert_eq!(v.get(100), 77);
    }

    #[test]
    fn l1_norm_uniform() {
        let v = DecisionVector::uniform(1);
        assert_eq!(v.l1_norm(), 162);
    }

    #[test]
    fn normalised_bounds() {
        assert!((DecisionVector::uniform(255).normalised(0) - 1.0).abs() < 1e-6);
        assert!(DecisionVector::zeroed().normalised(0).abs() < 1e-6);
    }
}
