//! IPC Ring Buffer throughput and latency benchmarks.
//! Sprint 2 target: <1µs per push+pop cycle.

use aios_ipc::RingBuffer;
use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};

fn bench_push_pop_cycle(c: &mut Criterion) {
    let mut group = c.benchmark_group("ring_buffer");
    group.throughput(Throughput::Elements(1));

    group.bench_function("push_pop_4b", |b| {
        let mut rb: RingBuffer<64, 256> = RingBuffer::new();
        let payload = [0xAD, 0x36, 0x90, 0x01u8];
        let mut out = [0u8; 256];
        b.iter(|| {
            rb.push(black_box(&payload)).unwrap();
            rb.pop(black_box(&mut out)).unwrap();
        });
    });

    group.bench_function("push_pop_64b", |b| {
        let mut rb: RingBuffer<64, 256> = RingBuffer::new();
        let payload = [0u8; 64];
        let mut out = [0u8; 256];
        b.iter(|| {
            rb.push(black_box(&payload)).unwrap();
            rb.pop(black_box(&mut out)).unwrap();
        });
    });

    group.bench_function("push_pop_255b", |b| {
        let mut rb: RingBuffer<64, 256> = RingBuffer::new();
        let payload = [0u8; 255];
        let mut out = [0u8; 256];
        b.iter(|| {
            rb.push(black_box(&payload)).unwrap();
            rb.pop(black_box(&mut out)).unwrap();
        });
    });

    group.finish();
}

fn bench_burst_throughput(c: &mut Criterion) {
    let mut group = c.benchmark_group("ring_buffer_burst");
    for batch_size in [8u64, 16, 32, 63] {
        group.throughput(Throughput::Elements(batch_size));
        group.bench_with_input(
            BenchmarkId::new("push_all_pop_all", batch_size),
            &batch_size,
            |b, &n| {
                let payload = [1u8; 32];
                let mut out = [0u8; 256];
                b.iter(|| {
                    let mut rb: RingBuffer<64, 256> = RingBuffer::new();
                    for _ in 0..n { rb.push(black_box(&payload)).unwrap(); }
                    for _ in 0..n { rb.pop(black_box(&mut out)).unwrap(); }
                });
            },
        );
    }
    group.finish();
}

fn bench_peek(c: &mut Criterion) {
    c.bench_function("ring_buffer_peek", |b| {
        let mut rb: RingBuffer<64, 256> = RingBuffer::new();
        rb.push(&[1u8; 8]).unwrap();
        b.iter(|| { let _ = black_box(rb.peek().unwrap()); });
    });
}

criterion_group!(benches, bench_push_pop_cycle, bench_burst_throughput, bench_peek);
criterion_main!(benches);
