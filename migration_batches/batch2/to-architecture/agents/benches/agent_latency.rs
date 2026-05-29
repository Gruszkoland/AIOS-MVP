//! Agent decision latency benchmarks.

use aios_agents::{
    ArchetypHarmonii, EvolutionAgent, GlosKrytyka, RelationalCareAgent, SentinelAgent,
    CognitiveAgent, StandardObservation,
};
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn obs(load: u8, arousal: u8) -> StandardObservation {
    StandardObservation { vector_mean: 128, system_load: load, user_arousal: arousal, tick: 42 }
}

fn bench_sentinel(c: &mut Criterion) {
    c.bench_function("sentinel_observe_decide", |b| {
        let mut agent = SentinelAgent::new(200);
        b.iter(|| {
            agent.observe(black_box(obs(100, 50))).unwrap();
            black_box(agent.decide().unwrap());
        });
    });
}

fn bench_relational_care(c: &mut Criterion) {
    c.bench_function("relational_care_observe_decide", |b| {
        let mut agent = RelationalCareAgent::new(178, 217);
        b.iter(|| {
            agent.observe(black_box(obs(50, 200))).unwrap();
            black_box(agent.decide().unwrap());
        });
    });
}

fn bench_archetyp_harmonii(c: &mut Criterion) {
    let mut group = c.benchmark_group("archetyp_harmonii");
    group.bench_function("feed_cycle_mean", |b| {
        let mut ah = ArchetypHarmonii::new();
        b.iter(|| { ah.feed_cycle_mean(black_box(128)); });
    });
    group.bench_function("harmony_score", |b| {
        let mut ah = ArchetypHarmonii::new();
        for i in 0..16u8 { ah.feed_cycle_mean(100 + i); }
        b.iter(|| { black_box(ah.harmony_score()); });
    });
    group.bench_function("observe_decide", |b| {
        let mut ah = ArchetypHarmonii::new();
        b.iter(|| {
            ah.observe(black_box(obs(128, 64))).unwrap();
            black_box(ah.decide().unwrap());
        });
    });
    group.finish();
}

fn bench_glos_krytyka(c: &mut Criterion) {
    c.bench_function("glos_krytyka_observe_decide", |b| {
        let mut agent = GlosKrytyka::new();
        b.iter(|| {
            agent.observe(black_box(obs(0, 0))).unwrap();
            black_box(agent.decide().unwrap());
        });
    });
}

fn bench_evolution(c: &mut Criterion) {
    c.bench_function("evolution_commit_heuristic", |b| {
        let mut agent = EvolutionAgent::new();
        b.iter(|| { agent.commit_heuristic(black_box(0.05)); });
    });
}

criterion_group!(benches, bench_sentinel, bench_relational_care, bench_archetyp_harmonii, bench_glos_krytyka, bench_evolution);
criterion_main!(benches);
