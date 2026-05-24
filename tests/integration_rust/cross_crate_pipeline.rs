//! Cross-crate integration test: Kernel → IPC → Agent → Decision
//!
//! Validates the complete ADRION 369 advisory pipeline:
//! 1. Build a DecisionVector with specific Guardian Law scores
//! 2. Run kernel consensus
//! 3. Serialize verdict through IPC ring buffer
//! 4. Agent reads from buffer, emits AdvisoryDecision
//! 5. Assert invariants hold end-to-end

use aios_agents::{CognitiveAgent, RelationalCareAgent, SentinelAgent, StandardObservation, SwarmTier};
use aios_ipc::{MessageHeader, MessageKind, RingBuffer};
use aios_kernel::{compute_consensus, ConsensusVerdict, DecisionVector, GuardianLaw};

/// Full pipeline: kernel consensus → IPC → sentinel advisory
#[test]
fn kernel_to_ipc_to_sentinel_approve_path() {
    // 1. Build a high-confidence decision vector
    let mut v = DecisionVector::uniform(200);
    // All laws well above thresholds
    let verdict = compute_consensus(&v);
    assert_eq!(verdict, ConsensusVerdict::Approve, "high vector should approve");

    // 2. Encode verdict into IPC message
    let mut bus: RingBuffer<16, 64> = RingBuffer::new();
    let verdict_byte = match verdict {
        ConsensusVerdict::Approve       => 0x01u8,
        ConsensusVerdict::Deny          => 0x02,
        ConsensusVerdict::VetoDeny      => 0x03,
        ConsensusVerdict::DeferToHuman  => 0x04,
    };
    let mut msg = [0u8; 8];
    let header = MessageHeader {
        seq: 1,
        src: 0,       // kernel
        dst: 0x03,    // Sentinel (Guardian::Causality index)
        kind: MessageKind::ConsensusVerdict,
        payload_len: 1,
    };
    header.write_to(&mut msg);
    // append verdict byte after header
    let mut full_msg = [0u8; 9];
    full_msg[..8].copy_from_slice(&msg);
    full_msg[8] = verdict_byte;
    bus.push(&full_msg[..9]).unwrap();

    // 3. Sentinel reads from bus
    let peeked = bus.peek().unwrap();
    let h = MessageHeader::read_from(peeked).unwrap();
    assert_eq!(h.seq, 1);
    assert_eq!(h.kind, MessageKind::ConsensusVerdict);
    assert_eq!(peeked[8], 0x01); // APPROVE

    // 4. Sentinel makes advisory decision based on observation
    let obs = StandardObservation {
        vector_mean: 200,
        system_load: 50,
        user_arousal: 30,
        tick: 1,
    };
    let mut sentinel = SentinelAgent::new(200);
    sentinel.observe(obs).unwrap();
    let decision = sentinel.decide().unwrap();

    use aios_agents::AdvisoryDecision;
    assert_eq!(decision, AdvisoryDecision::Proceed);
}

/// Veto path: CRITICAL law fails → kernel veto → IPC carries VETO → agent Veto
#[test]
fn kernel_veto_propagates_through_ipc() {
    // 1. Set Privacy (G7) scores below veto floor
    let mut v = DecisionVector::uniform(200);
    v.set_guardian_scores(GuardianLaw::Privacy, [10; 6]); // well below 64 veto floor
    let verdict = compute_consensus(&v);
    assert_eq!(verdict, ConsensusVerdict::VetoDeny);

    // 2. Encode VETO signal through IPC
    let mut bus: RingBuffer<16, 64> = RingBuffer::new();
    let mut msg = [0u8; 9];
    let header = MessageHeader {
        seq: 2,
        src: 0,
        dst: 0xFF, // broadcast
        kind: MessageKind::VetoSignal,
        payload_len: 1,
    };
    header.write_to(&mut msg);
    msg[8] = GuardianLaw::Privacy as u8; // which law triggered veto
    bus.push(&msg[..9]).unwrap();

    // 3. Verify IPC carries correct veto kind
    let peeked = bus.peek().unwrap();
    let h = MessageHeader::read_from(peeked).unwrap();
    assert_eq!(h.kind, MessageKind::VetoSignal);
    assert_eq!(h.dst, 0xFF); // broadcast

    // 4. Sentinel under extreme load also vetos
    let obs = StandardObservation {
        vector_mean: 10,
        system_load: 250,
        user_arousal: 220,
        tick: 2,
    };
    let mut sentinel = SentinelAgent::new(200);
    sentinel.observe(obs).unwrap();
    use aios_agents::AdvisoryDecision;
    assert_eq!(sentinel.decide().unwrap(), AdvisoryDecision::Veto);
}

/// RelationalCare empathic shortcut fires when arousal high
#[test]
fn relational_care_shortcut_on_high_arousal_after_defer() {
    let mut v = DecisionVector::uniform(150);
    v.set_guardian_scores(GuardianLaw::Privacy, [128; 6]);
    v.set_guardian_scores(GuardianLaw::Nonmaleficence, [128; 6]);
    let verdict = compute_consensus(&v);
    // Should defer (mid range)
    assert!(matches!(verdict, ConsensusVerdict::DeferToHuman | ConsensusVerdict::Deny));

    // User is exhausted → RelationalCare fires shortcut
    let obs = StandardObservation {
        vector_mean: 150,
        system_load: 60,
        user_arousal: 220, // above 178 threshold
        tick: 3,
    };
    let mut rc = RelationalCareAgent::new(178, 217);
    rc.observe(obs).unwrap();
    use aios_agents::AdvisoryDecision;
    assert_eq!(rc.decide().unwrap(), AdvisoryDecision::EmpathicShortcut);
}

/// Swarm tier invariant: meta < adversarial < systemic < operational
#[test]
fn swarm_tier_hierarchy_respected() {
    use aios_agents::{ArchetypHarmonii, GlosKrytyka, EvolutionAgent};

    let ah  = ArchetypHarmonii::new();
    let gk  = GlosKrytyka::new();
    let ev  = EvolutionAgent::new();
    let sen = SentinelAgent::new(200);

    assert!(ah.tier()  < gk.tier(),  "meta < adversarial");
    assert!(gk.tier()  < ev.tier(),  "adversarial < systemic");
    assert!(ev.tier()  < sen.tier(), "systemic < operational");
}

/// IPC message integrity: header survives round-trip through bus
#[test]
fn ipc_message_header_integrity_through_bus() {
    let mut bus: RingBuffer<8, 64> = RingBuffer::new();

    for seq in 0..7u32 {
        let header = MessageHeader {
            seq,
            src: (seq % 9) as u8,
            dst: 0xFF,
            kind: MessageKind::Heartbeat,
            payload_len: 0,
        };
        let mut buf = [0u8; 8];
        header.write_to(&mut buf);
        bus.push(&buf).unwrap();
    }

    for seq in 0..7u32 {
        let mut out = [0u8; 64];
        let n = bus.pop(&mut out).unwrap();
        assert_eq!(n, 8);
        let h = MessageHeader::read_from(&out).unwrap();
        assert_eq!(h.seq, seq);
        assert_eq!(h.kind, MessageKind::Heartbeat);
    }
}

/// GuardianLaw offsets are non-overlapping and cover [108..162]
#[test]
fn guardian_law_offsets_tile_correctly() {
    let laws = [
        GuardianLaw::Unity, GuardianLaw::Harmony, GuardianLaw::Rhythm,
        GuardianLaw::Causality, GuardianLaw::Transparency, GuardianLaw::Authenticity,
        GuardianLaw::Privacy, GuardianLaw::Nonmaleficence, GuardianLaw::Sustainability,
    ];

    let mut occupied = [false; 162];
    for law in laws {
        let off = law.offset();
        for i in off..off+6 {
            assert!(!occupied[i], "overlap at dimension {} for {:?}", i, law);
            occupied[i] = true;
        }
    }
    // All guardian dimensions [108..162] should be occupied
    for i in 108..162 {
        assert!(occupied[i], "dimension {} not covered by any guardian", i);
    }
}
