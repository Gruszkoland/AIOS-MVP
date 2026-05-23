#![no_std]
#![deny(unsafe_op_in_unsafe_fn)]
#![warn(missing_docs)]

//! AIOS Kernel — deterministic `no_std` core.
//!
//! Implements the 162-dimensional decision topology from the ADRION 369
//! moral framework (3 Principles × 6 Interpretation Modes × 9 Guardians).
//!
//! # Architecture
//! ```text
//! DecisionVector<162>
//!     ├─ Principle layer   [0..54]   — Life, Freedom, Dignity
//!     ├─ Mode layer        [54..108] — Analytical … Relational
//!     └─ Guardian layer    [108..162]— 9 specialist agents × 6 weights
//! ```
//!
//! All types implement `Copy` so they live on the stack — no allocator needed.

// ─── Principle layer (indices 0..54) ────────────────────────────────────────

/// The three top-level moral principles of ADRION 369.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum Principle {
    /// P1 — Protect and preserve life.
    Life = 0,
    /// P2 — Respect and promote freedom.
    Freedom = 1,
    /// P3 — Uphold inherent dignity.
    Dignity = 2,
}

impl Principle {
    /// Returns the slice offset into a `DecisionVector` for this principle.
    #[inline]
    pub const fn offset(self) -> usize {
        self as usize * 18  // 3 principles × 18 weights each = 54
    }
}

// ─── Interpretation-mode layer (indices 54..108) ─────────────────────────────

/// Six lenses through which each decision is evaluated.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum InterpretationMode {
    /// M1 — Logical deduction from first principles.
    Analytical = 0,
    /// M2 — Learned patterns from past decisions.
    Empirical = 1,
    /// M3 — Long-horizon risk modelling.
    Predictive = 2,
    /// M4 — Multi-stakeholder perspective integration.
    Contextual = 3,
    /// M5 — Moral intuition and value alignment.
    Normative = 4,
    /// M6 — Care ethics and relationship-based reasoning.
    Relational = 5,
}

impl InterpretationMode {
    /// Returns the slice offset into a `DecisionVector` for this mode.
    #[inline]
    pub const fn offset(self) -> usize {
        54 + self as usize * 9  // 6 modes × 9 weights each = 54
    }
}

// ─── Guardian layer (indices 108..162) ──────────────────────────────────────

/// The nine specialist Guardian agents, each with veto capability.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum Guardian {
    /// G1 — Librarian: knowledge integrity.
    Librarian = 0,
    /// G2 — SAP: situational awareness processor.
    Sap = 1,
    /// G3 — Auditor: compliance and logging.
    Auditor = 2,
    /// G4 — Sentinel: real-time threat detection.
    Sentinel = 3,
    /// G5 — Architect: structural coherence.
    Architect = 4,
    /// G6 — Healer: system recovery.
    Healer = 5,
    /// G7 — Oracle: probabilistic forecasting.
    Oracle = 6,
    /// G8 — Vortex: resource optimisation.
    Vortex = 7,
    /// G9 — Genesis: creative synthesis.
    Genesis = 8,
}

impl Guardian {
    /// Returns the slice offset into a `DecisionVector` for this guardian.
    #[inline]
    pub const fn offset(self) -> usize {
        108 + self as usize * 6  // 9 guardians × 6 mode-weights each = 54
    }

    /// Criticality score used in the weighted consensus calculation.
    ///
    /// Returns `10` for safety-critical guardians, `2` for high-impact, `1` for standard.
    #[inline]
    pub const fn criticality(self) -> u32 {
        match self {
            Guardian::Sentinel | Guardian::Auditor => 10,
            Guardian::Architect | Guardian::Healer => 2,
            _ => 1,
        }
    }

    /// Whether this guardian holds veto power over `DENY` decisions.
    #[inline]
    pub const fn has_veto(self) -> bool {
        matches!(self, Guardian::Sentinel | Guardian::Auditor | Guardian::Architect)
    }
}

// ─── Decision vector ─────────────────────────────────────────────────────────

/// A 162-dimensional fixed-size decision vector.
///
/// Dimensions are laid out as:
/// - `[0..54]`   — Principle × mode weights (3 × 18)
/// - `[54..108]` — Mode × guardian weights (6 × 9)
/// - `[108..162]`— Guardian × mode scores (9 × 6)
///
/// All values are in the range `[0, 255]` (u8) for compact storage.
/// Use `normalize()` to map them to `[0.0, 1.0]` f32 when needed.
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

    /// Creates a uniform decision vector with all weights set to `value`.
    #[inline]
    pub const fn uniform(value: u8) -> Self {
        Self { data: [value; 162] }
    }

    /// Returns the raw value at `index`. Panics in debug if out of range.
    #[inline]
    pub fn get(&self, index: usize) -> u8 {
        self.data[index]
    }

    /// Sets the raw value at `index`.
    #[inline]
    pub fn set(&mut self, index: usize, value: u8) {
        self.data[index] = value;
    }

    /// Sets all weights for a given `Principle` region (18 dimensions).
    pub fn set_principle_weights(&mut self, p: Principle, weights: [u8; 18]) {
        let off = p.offset();
        self.data[off..off + 18].copy_from_slice(&weights);
    }

    /// Sets all weights for a given `InterpretationMode` region (9 dimensions).
    pub fn set_mode_weights(&mut self, m: InterpretationMode, weights: [u8; 9]) {
        let off = m.offset();
        self.data[off..off + 9].copy_from_slice(&weights);
    }

    /// Sets all scores for a given `Guardian` region (6 dimensions).
    pub fn set_guardian_scores(&mut self, g: Guardian, scores: [u8; 6]) {
        let off = g.offset();
        self.data[off..off + 6].copy_from_slice(&scores);
    }

    /// Computes the L1 norm of the vector (sum of all components).
    pub fn l1_norm(&self) -> u32 {
        self.data.iter().map(|&b| b as u32).sum()
    }

    /// Computes the unweighted mean of all 162 components, scaled to [0, 255].
    pub fn mean(&self) -> u8 {
        (self.l1_norm() / 162) as u8
    }

    /// Returns a normalised f32 value for a single dimension (0.0..=1.0).
    pub fn normalised(&self, index: usize) -> f32 {
        self.data[index] as f32 / 255.0
    }
}

// ─── Consensus engine ────────────────────────────────────────────────────────

/// Possible outcomes of the ADRION consensus algorithm.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ConsensusVerdict {
    /// All guardians approve — action is permitted.
    Approve,
    /// Weighted score is too low — action is denied.
    Deny,
    /// A veto-holding guardian registered a hard block.
    VetoDeny,
    /// Score is inconclusive — defer to human oversight.
    DeferToHuman,
}

/// Computes a weighted consensus verdict from a `DecisionVector`.
///
/// Algorithm:
/// 1. For each guardian, sum its 6 mode-scores weighted by `Guardian::criticality()`.
/// 2. Accumulate into `total_weighted` and `max_possible`.
/// 3. Compute ratio = `total_weighted / max_possible`.
/// 4. If any veto guardian has mean score < `VETO_THRESHOLD` → `VetoDeny`.
/// 5. `ratio >= APPROVE_THRESHOLD` → `Approve`.
/// 6. `ratio <= DENY_THRESHOLD` → `Deny`.
/// 7. Otherwise → `DeferToHuman`.
pub fn compute_consensus(v: &DecisionVector) -> ConsensusVerdict {
    const APPROVE_THRESHOLD: u32 = 178;  // ~70% of 255
    const DENY_THRESHOLD: u32 = 76;      // ~30% of 255
    const VETO_FLOOR: u8 = 64;           // ~25% — hard veto floor

    let guardians = [
        Guardian::Librarian, Guardian::Sap, Guardian::Auditor,
        Guardian::Sentinel, Guardian::Architect, Guardian::Healer,
        Guardian::Oracle, Guardian::Vortex, Guardian::Genesis,
    ];

    let mut total_weighted: u64 = 0;
    let mut max_possible: u64 = 0;

    for g in guardians {
        let off = g.offset();
        let scores = &v.data[off..off + 6];
        let sum: u32 = scores.iter().map(|&s| s as u32).sum();
        let mean6 = (sum / 6) as u8;

        // Hard veto check for safety-critical guardians
        if g.has_veto() && mean6 < VETO_FLOOR {
            return ConsensusVerdict::VetoDeny;
        }

        let w = g.criticality() as u64;
        total_weighted += sum as u64 * w;
        max_possible += 255 * 6 * w;
    }

    // Scale ratio to 0..255
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
    fn zeroed_vector_is_deny() {
        let v = DecisionVector::zeroed();
        // All zeros — all guardians below veto floor (64), so first veto guardian fires
        assert_eq!(compute_consensus(&v), ConsensusVerdict::VetoDeny);
    }

    #[test]
    fn uniform_high_vector_is_approve() {
        let v = DecisionVector::uniform(220);
        assert_eq!(compute_consensus(&v), ConsensusVerdict::Approve);
    }

    #[test]
    fn uniform_low_vector_is_deny() {
        let v = DecisionVector::uniform(20);
        // Mean is 20 which is below veto floor for sentinel/auditor/architect
        assert_eq!(compute_consensus(&v), ConsensusVerdict::VetoDeny);
    }

    #[test]
    fn veto_fires_when_sentinel_scores_low() {
        let mut v = DecisionVector::uniform(200); // everyone high
        // Drag sentinel (G4, offset=108+3*6=126) down below veto floor
        v.set_guardian_scores(Guardian::Sentinel, [10, 10, 10, 10, 10, 10]);
        assert_eq!(compute_consensus(&v), ConsensusVerdict::VetoDeny);
    }

    #[test]
    fn no_veto_mid_range_defers() {
        // Set all veto guardians above veto floor, but overall score in middle range
        let mut v = DecisionVector::zeroed();
        // Veto guardians: Sentinel, Auditor, Architect — set to 128
        v.set_guardian_scores(Guardian::Sentinel, [128; 6]);
        v.set_guardian_scores(Guardian::Auditor, [128; 6]);
        v.set_guardian_scores(Guardian::Architect, [128; 6]);
        // Non-veto guardians — low
        v.set_guardian_scores(Guardian::Librarian, [80; 6]);
        v.set_guardian_scores(Guardian::Sap, [80; 6]);
        v.set_guardian_scores(Guardian::Healer, [80; 6]);
        v.set_guardian_scores(Guardian::Oracle, [80; 6]);
        v.set_guardian_scores(Guardian::Vortex, [80; 6]);
        v.set_guardian_scores(Guardian::Genesis, [80; 6]);
        let verdict = compute_consensus(&v);
        assert!(matches!(verdict, ConsensusVerdict::DeferToHuman | ConsensusVerdict::Deny));
    }

    #[test]
    fn principle_offset_is_correct() {
        assert_eq!(Principle::Life.offset(), 0);
        assert_eq!(Principle::Freedom.offset(), 18);
        assert_eq!(Principle::Dignity.offset(), 36);
    }

    #[test]
    fn mode_offset_is_correct() {
        assert_eq!(InterpretationMode::Analytical.offset(), 54);
        assert_eq!(InterpretationMode::Relational.offset(), 99);
    }

    #[test]
    fn guardian_offset_is_correct() {
        assert_eq!(Guardian::Librarian.offset(), 108);
        assert_eq!(Guardian::Genesis.offset(), 156);
    }

    #[test]
    fn guardian_criticality_weights() {
        assert_eq!(Guardian::Sentinel.criticality(), 10);
        assert_eq!(Guardian::Auditor.criticality(), 10);
        assert_eq!(Guardian::Architect.criticality(), 2);
        assert_eq!(Guardian::Healer.criticality(), 2);
        assert_eq!(Guardian::Oracle.criticality(), 1);
    }

    #[test]
    fn set_and_get_roundtrip() {
        let mut v = DecisionVector::zeroed();
        v.set(42, 99);
        assert_eq!(v.get(42), 99);
    }

    #[test]
    fn uniform_mean_is_value() {
        let v = DecisionVector::uniform(100);
        assert_eq!(v.mean(), 100);
    }

    #[test]
    fn l1_norm_uniform() {
        let v = DecisionVector::uniform(1);
        assert_eq!(v.l1_norm(), 162);
    }

    #[test]
    fn normalised_bounds() {
        let v = DecisionVector::uniform(255);
        let n = v.normalised(0);
        assert!((n - 1.0).abs() < 1e-6);
        let z = DecisionVector::zeroed();
        assert!(z.normalised(0).abs() < 1e-6);
    }
}
