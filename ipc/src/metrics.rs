//! Prometheus Metrics — Phase 3-3
//! Core metrics collection for consensus, latency, throughput, and agent health
//! Exports: DecisionLatency, ConsensusRounds, ThroughputCounter, AgentUptime, etc.

use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::fmt;

/// Latency bucket (P50, P99, P999)
#[derive(Debug, Clone, Copy)]
pub struct LatencyBucket {
    pub p50: u64,  // nanoseconds
    pub p99: u64,
    pub p999: u64,
}

impl LatencyBucket {
    pub fn new() -> Self {
        LatencyBucket {
            p50: 0,
            p99: 0,
            p999: 0,
        }
    }

    pub fn update(&mut self, samples: &[u64]) {
        if samples.is_empty() {
            return;
        }

        let mut sorted = samples.to_vec();
        sorted.sort_unstable();

        let len = sorted.len();
        self.p50 = sorted[len / 2];
        self.p99 = sorted[(len * 99) / 100];
        self.p999 = sorted[(len * 999) / 1000];
    }
}

impl fmt::Display for LatencyBucket {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "LatencyBucket(p50={}ns, p99={}ns, p999={}ns)",
            self.p50, self.p99, self.p999
        )
    }
}

/// Decision latency metrics
#[derive(Debug, Clone)]
pub struct DecisionLatency {
    pub samples: Vec<u64>,  // nanoseconds
    pub bucket: LatencyBucket,
    pub min_ns: u64,
    pub max_ns: u64,
}

impl DecisionLatency {
    pub fn new() -> Self {
        DecisionLatency {
            samples: Vec::new(),
            bucket: LatencyBucket::new(),
            min_ns: u64::MAX,
            max_ns: 0,
        }
    }

    pub fn record(&mut self, latency_ns: u64) {
        self.samples.push(latency_ns);
        self.min_ns = self.min_ns.min(latency_ns);
        self.max_ns = self.max_ns.max(latency_ns);

        // Update buckets every 100 samples or when buffer large
        if self.samples.len() >= 100 {
            self.bucket.update(&self.samples);
        }
    }

    pub fn mean(&self) -> u64 {
        if self.samples.is_empty() {
            return 0;
        }
        self.samples.iter().sum::<u64>() / self.samples.len() as u64
    }

    pub fn count(&self) -> usize {
        self.samples.len()
    }
}

/// Consensus round metrics
#[derive(Debug, Clone, Copy)]
pub struct ConsensusRound {
    pub round_id: u64,
    pub phase: u8,  // 0: pre-prepare, 1: prepare, 2: commit
    pub duration_ns: u64,
    pub participant_count: u32,
    pub success: bool,
}

impl ConsensusRound {
    pub fn new(round_id: u64, participant_count: u32) -> Self {
        ConsensusRound {
            round_id,
            phase: 0,
            duration_ns: 0,
            participant_count,
            success: false,
        }
    }
}

/// Throughput counter
#[derive(Debug, Clone)]
pub struct ThroughputCounter {
    pub decisions_total: Arc<AtomicU64>,
    pub decisions_success: Arc<AtomicU64>,
    pub decisions_failed: Arc<AtomicU64>,
    pub consensus_rounds: Arc<AtomicU64>,
}

impl ThroughputCounter {
    pub fn new() -> Self {
        ThroughputCounter {
            decisions_total: Arc::new(AtomicU64::new(0)),
            decisions_success: Arc::new(AtomicU64::new(0)),
            decisions_failed: Arc::new(AtomicU64::new(0)),
            consensus_rounds: Arc::new(AtomicU64::new(0)),
        }
    }

    pub fn record_decision(&self, success: bool) {
        self.decisions_total.fetch_add(1, Ordering::Relaxed);
        if success {
            self.decisions_success.fetch_add(1, Ordering::Relaxed);
        } else {
            self.decisions_failed.fetch_add(1, Ordering::Relaxed);
        }
    }

    pub fn record_consensus_round(&self) {
        self.consensus_rounds.fetch_add(1, Ordering::Relaxed);
    }

    pub fn throughput_decisions_per_sec(&self, duration_secs: f64) -> f64 {
        let total = self.decisions_total.load(Ordering::Relaxed);
        total as f64 / duration_secs
    }

    pub fn success_rate(&self) -> f64 {
        let total = self.decisions_total.load(Ordering::Relaxed);
        let success = self.decisions_success.load(Ordering::Relaxed);
        if total == 0 {
            return 1.0;
        }
        success as f64 / total as f64
    }
}

impl fmt::Display for ThroughputCounter {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "ThroughputCounter(total={}, success={}, failed={}, rounds={})",
            self.decisions_total.load(Ordering::Relaxed),
            self.decisions_success.load(Ordering::Relaxed),
            self.decisions_failed.load(Ordering::Relaxed),
            self.consensus_rounds.load(Ordering::Relaxed)
        )
    }
}

/// Agent uptime tracker
#[derive(Debug, Clone)]
pub struct AgentUptime {
    pub agent_id: u32,
    pub started_nanos: u64,
    pub total_downtime_ns: u64,
    pub restart_count: u32,
}

impl AgentUptime {
    pub fn new(agent_id: u32, started_nanos: u64) -> Self {
        AgentUptime {
            agent_id,
            started_nanos,
            total_downtime_ns: 0,
            restart_count: 0,
        }
    }

    pub fn uptime_ns(&self, now_nanos: u64) -> u64 {
        if now_nanos < self.started_nanos {
            return 0;
        }
        now_nanos - self.started_nanos - self.total_downtime_ns
    }

    pub fn uptime_percent(&self, now_nanos: u64) -> f64 {
        let total_time = now_nanos.saturating_sub(self.started_nanos);
        if total_time == 0 {
            return 100.0;
        }
        let up_time = self.uptime_ns(now_nanos);
        (up_time as f64 / total_time as f64) * 100.0
    }

    pub fn record_downtime(&mut self, downtime_ns: u64) {
        self.total_downtime_ns += downtime_ns;
        self.restart_count += 1;
    }
}

/// Byzantine fault metrics
#[derive(Debug, Clone, Copy)]
pub struct ByzantineFaultMetrics {
    pub suspected_byzantine: u32,
    pub confirmed_byzantine: u32,
    pub view_changes: u32,
    pub quorum_drops: u32,
}

impl ByzantineFaultMetrics {
    pub fn new() -> Self {
        ByzantineFaultMetrics {
            suspected_byzantine: 0,
            confirmed_byzantine: 0,
            view_changes: 0,
            quorum_drops: 0,
        }
    }

    pub fn byzantine_rate(&self) -> f64 {
        let total = self.suspected_byzantine.saturating_add(1);
        self.confirmed_byzantine as f64 / total as f64
    }
}

/// Rate limiter metrics
#[derive(Debug, Clone, Copy)]
pub struct RateLimiterMetrics {
    pub requests_allowed: u64,
    pub requests_rejected: u64,
    pub endpoints_tracked: u32,
    pub ips_tracked: u32,
}

impl RateLimiterMetrics {
    pub fn new() -> Self {
        RateLimiterMetrics {
            requests_allowed: 0,
            requests_rejected: 0,
            endpoints_tracked: 0,
            ips_tracked: 0,
        }
    }

    pub fn rejection_rate(&self) -> f64 {
        let total = self.requests_allowed.saturating_add(self.requests_rejected).saturating_add(1);
        self.requests_rejected as f64 / total as f64
    }
}

/// Prometheus exporter — collects all metrics
pub struct PrometheusExporter {
    pub latency: DecisionLatency,
    pub throughput: ThroughputCounter,
    pub agent_uptime: Vec<AgentUptime>,
    pub byzantine_faults: ByzantineFaultMetrics,
    pub rate_limiter: RateLimiterMetrics,
}

impl PrometheusExporter {
    pub fn new() -> Self {
        PrometheusExporter {
            latency: DecisionLatency::new(),
            throughput: ThroughputCounter::new(),
            agent_uptime: Vec::new(),
            byzantine_faults: ByzantineFaultMetrics::new(),
            rate_limiter: RateLimiterMetrics::new(),
        }
    }

    pub fn export_metrics(&self, duration_secs: f64) -> String {
        let mut output = String::new();

        // Decision latency metrics
        output.push_str("# HELP decision_latency_p50_ns Decision latency P50 (nanoseconds)\n");
        output.push_str("# TYPE decision_latency_p50_ns gauge\n");
        output.push_str(&format!("decision_latency_p50_ns {}\n", self.latency.bucket.p50));

        output.push_str("# HELP decision_latency_p99_ns Decision latency P99 (nanoseconds)\n");
        output.push_str("# TYPE decision_latency_p99_ns gauge\n");
        output.push_str(&format!("decision_latency_p99_ns {}\n", self.latency.bucket.p99));

        output.push_str("# HELP decision_latency_p999_ns Decision latency P999 (nanoseconds)\n");
        output.push_str("# TYPE decision_latency_p999_ns gauge\n");
        output.push_str(&format!("decision_latency_p999_ns {}\n", self.latency.bucket.p999));

        output.push_str("# HELP decision_latency_mean_ns Mean decision latency\n");
        output.push_str("# TYPE decision_latency_mean_ns gauge\n");
        output.push_str(&format!("decision_latency_mean_ns {}\n", self.latency.mean()));

        // Throughput metrics
        let throughput_dps = self.throughput.throughput_decisions_per_sec(duration_secs);
        output.push_str("# HELP decisions_per_second Throughput: decisions per second\n");
        output.push_str("# TYPE decisions_per_second gauge\n");
        output.push_str(&format!("decisions_per_second {}\n", throughput_dps));

        output.push_str("# HELP decisions_total Total decisions processed\n");
        output.push_str("# TYPE decisions_total counter\n");
        output.push_str(&format!(
            "decisions_total {}\n",
            self.throughput.decisions_total.load(std::sync::atomic::Ordering::Relaxed)
        ));

        output.push_str("# HELP decisions_success Total successful decisions\n");
        output.push_str("# TYPE decisions_success counter\n");
        output.push_str(&format!(
            "decisions_success {}\n",
            self.throughput.decisions_success.load(std::sync::atomic::Ordering::Relaxed)
        ));

        let success_rate = self.throughput.success_rate();
        output.push_str("# HELP decision_success_rate Success rate (0.0-1.0)\n");
        output.push_str("# TYPE decision_success_rate gauge\n");
        output.push_str(&format!("decision_success_rate {}\n", success_rate));

        output.push_str("# HELP consensus_rounds_total Total consensus rounds\n");
        output.push_str("# TYPE consensus_rounds_total counter\n");
        output.push_str(&format!(
            "consensus_rounds_total {}\n",
            self.throughput.consensus_rounds.load(std::sync::atomic::Ordering::Relaxed)
        ));

        // Byzantine fault metrics
        output.push_str("# HELP byzantine_suspected_count Suspected Byzantine agents\n");
        output.push_str("# TYPE byzantine_suspected_count gauge\n");
        output.push_str(&format!("byzantine_suspected_count {}\n", self.byzantine_faults.suspected_byzantine));

        output.push_str("# HELP byzantine_confirmed_count Confirmed Byzantine agents\n");
        output.push_str("# TYPE byzantine_confirmed_count gauge\n");
        output.push_str(&format!("byzantine_confirmed_count {}\n", self.byzantine_faults.confirmed_byzantine));

        let byzantine_rate = self.byzantine_faults.byzantine_rate();
        output.push_str("# HELP byzantine_confirmation_rate Byzantine confirmation rate\n");
        output.push_str("# TYPE byzantine_confirmation_rate gauge\n");
        output.push_str(&format!("byzantine_confirmation_rate {}\n", byzantine_rate));

        output.push_str("# HELP view_changes_total Total view changes triggered\n");
        output.push_str("# TYPE view_changes_total counter\n");
        output.push_str(&format!("view_changes_total {}\n", self.byzantine_faults.view_changes));

        output.push_str("# HELP quorum_drops_total Quorum drops detected\n");
        output.push_str("# TYPE quorum_drops_total counter\n");
        output.push_str(&format!("quorum_drops_total {}\n", self.byzantine_faults.quorum_drops));

        // Rate limiter metrics
        output.push_str("# HELP rate_limit_requests_allowed Requests allowed\n");
        output.push_str("# TYPE rate_limit_requests_allowed counter\n");
        output.push_str(&format!("rate_limit_requests_allowed {}\n", self.rate_limiter.requests_allowed));

        output.push_str("# HELP rate_limit_requests_rejected Requests rejected\n");
        output.push_str("# TYPE rate_limit_requests_rejected counter\n");
        output.push_str(&format!("rate_limit_requests_rejected {}\n", self.rate_limiter.requests_rejected));

        let rejection_rate = self.rate_limiter.rejection_rate();
        output.push_str("# HELP rate_limit_rejection_rate Rejection rate (0.0-1.0)\n");
        output.push_str("# TYPE rate_limit_rejection_rate gauge\n");
        output.push_str(&format!("rate_limit_rejection_rate {}\n", rejection_rate));

        // Agent uptime metrics
        for agent in &self.agent_uptime {
            let now_nanos = 1_000_000_000_000; // Mock current time for demo
            let uptime_pct = agent.uptime_percent(now_nanos);
            output.push_str(&format!("# HELP agent_uptime_percent{{agent_id=\"{}\"}} Agent uptime percentage\n", agent.agent_id));
            output.push_str("# TYPE agent_uptime_percent gauge\n");
            output.push_str(&format!("agent_uptime_percent{{agent_id=\"{}\"}} {}\n", agent.agent_id, uptime_pct));
        }

        output
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_latency_bucket_update() {
        let mut bucket = LatencyBucket::new();
        let samples = vec![100, 200, 300, 400, 500];
        bucket.update(&samples);
        assert_eq!(bucket.p50, 300);
    }

    #[test]
    fn test_decision_latency_record() {
        let mut latency = DecisionLatency::new();
        latency.record(100);
        latency.record(200);
        latency.record(300);
        assert_eq!(latency.count(), 3);
        assert_eq!(latency.min_ns, 100);
        assert_eq!(latency.max_ns, 300);
        assert_eq!(latency.mean(), 200);
    }

    #[test]
    fn test_throughput_counter() {
        let counter = ThroughputCounter::new();
        counter.record_decision(true);
        counter.record_decision(true);
        counter.record_decision(false);
        assert_eq!(counter.decisions_total.load(Ordering::Relaxed), 3);
        assert_eq!(counter.decisions_success.load(Ordering::Relaxed), 2);
        assert_eq!(counter.decisions_failed.load(Ordering::Relaxed), 1);
        let rate = counter.success_rate();
        assert!(rate > 0.66 && rate < 0.67);
    }

    #[test]
    fn test_throughput_per_sec() {
        let counter = ThroughputCounter::new();
        for _ in 0..100 {
            counter.record_decision(true);
        }
        let throughput = counter.throughput_decisions_per_sec(1.0);
        assert_eq!(throughput, 100.0);
    }

    #[test]
    fn test_agent_uptime() {
        let mut uptime = AgentUptime::new(1, 1000);
        uptime.record_downtime(100);
        assert_eq!(uptime.restart_count, 1);
        assert_eq!(uptime.total_downtime_ns, 100);

        let uptime_ns = uptime.uptime_ns(2000);
        assert_eq!(uptime_ns, 900); // 2000 - 1000 - 100
    }

    #[test]
    fn test_agent_uptime_percent() {
        let mut uptime = AgentUptime::new(1, 0);
        uptime.total_downtime_ns = 100;
        let percent = uptime.uptime_percent(1000);
        assert!(percent > 99.0 && percent < 100.0);
    }

    #[test]
    fn test_byzantine_fault_metrics() {
        let mut metrics = ByzantineFaultMetrics::new();
        metrics.suspected_byzantine = 2;
        metrics.confirmed_byzantine = 1;
        let rate = metrics.byzantine_rate();
        assert!(rate > 0.0 && rate <= 1.0);
    }

    #[test]
    fn test_rate_limiter_metrics() {
        let mut metrics = RateLimiterMetrics::new();
        metrics.requests_allowed = 90;
        metrics.requests_rejected = 10;
        let rate = metrics.rejection_rate();
        assert!(rate > 0.0 && rate < 1.0);
    }

    #[test]
    fn test_prometheus_exporter() {
        let mut exporter = PrometheusExporter::new();
        exporter.latency.record(100);
        exporter.latency.record(200);
        exporter.throughput.record_decision(true);

        let metrics = exporter.export_metrics(1.0);
        assert!(metrics.contains("decision_latency_p50_ns"));
        assert!(metrics.contains("decisions_per_second"));
        assert!(metrics.contains("# TYPE"));
        assert!(metrics.contains("# HELP"));
    }

    #[test]
    fn test_prometheus_exporter_with_agents() {
        let mut exporter = PrometheusExporter::new();
        exporter.agent_uptime.push(AgentUptime::new(1, 0));
        exporter.agent_uptime.push(AgentUptime::new(2, 0));

        let metrics = exporter.export_metrics(1.0);
        assert!(metrics.contains("agent_uptime_percent"));
        assert!(metrics.contains("agent_id=\"1\""));
        assert!(metrics.contains("agent_id=\"2\""));
    }
}
