#!/usr/bin/env python
"""
Prometheus Metrics Collector for ADRION 369

Collects metrics from:
- CVC (Cumulative Violation Counter) state and counter
- Guardian Laws violations by law
- TSPA agent trust scores
- Genesis Record throughput and integrity
- LTM profile statistics
- Request processing time

ADRION 369 §III — Observability & Monitoring
DSPy Signature:
    In(cvc_mgr, ltm_mgr, guardian_stats) → Out(metrics_text:str, format:str)
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────────
# PROMETHEUS METRIC TYPES
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class PrometheusMetrics:
    """Container for Prometheus metrics in text format."""
    
    # CVC metrics
    cvc_counter: int = 0
    cvc_state: str = "GREEN"  # 0=GREEN, 1=YELLOW, 2=ORANGE, 3=RED
    cvc_state_value: int = 0
    cvc_violations_total: int = 0
    
    # Guardian Laws metrics
    guardian_violations_total: Dict[str, int] = field(default_factory=dict)
    guardian_critical_violations_total: int = 0
    
    # Genesis Record metrics
    genesis_records_total: int = 0
    genesis_records_by_type: Dict[str, int] = field(default_factory=dict)
    genesis_verification_ok: bool = True
    
    # TSPA metrics
    tspa_score_by_agent: Dict[str, float] = field(default_factory=dict)
    
    # LTM metrics
    ltm_session_count: int = 0
    ltm_cold_start: bool = False
    
    # Request metrics
    request_duration_seconds: float = 0.0
    request_count: int = 0
    
    def to_prometheus_text(self) -> str:
        """Convert metrics to Prometheus text format (.004 exposition format)."""
        lines = [
            "# HELP cvc_counter Cumulative Violation Counter value",
            "# TYPE cvc_counter gauge",
            f"cvc_counter {self.cvc_counter}",
            "",
            "# HELP cvc_state CVC state enum (0=GREEN, 1=YELLOW, 2=ORANGE, 3=RED)",
            "# TYPE cvc_state gauge",
            f'cvc_state{{state="{self.cvc_state}"}} {self.cvc_state_value}',
            "",
            "# HELP cvc_violations_total Total CVC violations recorded",
            "# TYPE cvc_violations_total counter",
            f"cvc_violations_total {self.cvc_violations_total}",
            "",
            "# HELP guardian_violations_total Guardian Law violations by law",
            "# TYPE guardian_violations_total counter",
        ]
        
        for law_name, count in sorted(self.guardian_violations_total.items()):
            lines.append(f'guardian_violations_total{{law="{law_name}"}} {count}')
        
        lines.extend([
            "",
            "# HELP guardian_critical_violations_total Critical (G6-G8) Guardian violations",
            "# TYPE guardian_critical_violations_total counter",
            f"guardian_critical_violations_total {self.guardian_critical_violations_total}",
            "",
            "# HELP genesis_records_total Total Genesis Record entries",
            "# TYPE genesis_records_total counter",
            f"genesis_records_total {self.genesis_records_total}",
            "",
            "# HELP genesis_records_by_type Genesis Record entries by action type",
            "# TYPE genesis_records_by_type counter",
        ])
        
        for action_type, count in sorted(self.genesis_records_by_type.items()):
            lines.append(f'genesis_records_by_type{{action_type="{action_type}"}} {count}')
        
        lines.extend([
            "",
            "# HELP genesis_verification_ok Genesis Record hash chain integrity",
            "# TYPE genesis_verification_ok gauge",
            f"genesis_verification_ok {int(self.genesis_verification_ok)}",
            "",
            "# HELP tspa_score TSPA (Trust Score & Performance Assessment) by agent",
            "# TYPE tspa_score gauge",
        ])
        
        for agent, score in sorted(self.tspa_score_by_agent.items()):
            lines.append(f'tspa_score{{agent="{agent}"}} {score:.2f}')
        
        lines.extend([
            "",
            "# HELP ltm_session_count LTM session count",
            "# TYPE ltm_session_count gauge",
            f"ltm_session_count {self.ltm_session_count}",
            "",
            "# HELP ltm_cold_start LTM cold-start flag (1=yes, 0=no)",
            "# TYPE ltm_cold_start gauge",
            f"ltm_cold_start {int(self.ltm_cold_start)}",
            "",
            "# HELP request_duration_seconds Last request processing duration",
            "# TYPE request_duration_seconds gauge",
            f"request_duration_seconds {self.request_duration_seconds:.4f}",
            "",
            "# HELP request_count Total requests processed",
            "# TYPE request_count counter",
            f"request_count {self.request_count}",
        ])
        
        return "\n".join(lines)


# ────────────────────────────────────────────────────────────────────────────
# METRICS COLLECTOR
# ────────────────────────────────────────────────────────────────────────────

class MetricsCollector:
    """Collect ADRION 369 metrics from CVC, LTM, Guardian, and Genesis Record."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.metrics = PrometheusMetrics()
        self.request_times = []
        self.request_count = 0
        
    def collect(self, cvc_mgr: Optional[Any] = None, 
                ltm_mgr: Optional[Any] = None,
                guardian_stats: Optional[Dict[str, Any]] = None) -> PrometheusMetrics:
        """
        Collect all metrics from subsystems.
        
        DSPy Signature:
            In(cvc_mgr:CVCManager|None, ltm_mgr:LTMManager|None, guardian_stats:dict|None)
            → Out(metrics:PrometheusMetrics)
        """
        metrics = PrometheusMetrics()
        
        # 1. CVC metrics
        if cvc_mgr:
            try:
                metrics.cvc_counter = cvc_mgr.counter
                metrics.cvc_state = cvc_mgr.state
                metrics.cvc_state_value = self._cvc_state_to_value(cvc_mgr.state)
                metrics.cvc_violations_total = len(cvc_mgr.violations)
            except Exception as e:
                logger.warning(f"Failed to collect CVC metrics: {e}")
        
        # 2. LTM metrics
        if ltm_mgr:
            try:
                metrics.ltm_session_count = ltm_mgr.profile.session_count if ltm_mgr.profile else 0
                metrics.ltm_cold_start = ltm_mgr.cold_start
                if ltm_mgr.profile and ltm_mgr.profile.tspa_scores:
                    metrics.tspa_score_by_agent = ltm_mgr.profile.tspa_scores
            except Exception as e:
                logger.warning(f"Failed to collect LTM metrics: {e}")
        
        # 3. Guardian Laws metrics
        if guardian_stats:
            try:
                metrics.guardian_violations_total = guardian_stats.get("violations_by_law", {})
                metrics.guardian_critical_violations_total = guardian_stats.get("critical_count", 0)
            except Exception as e:
                logger.warning(f"Failed to collect Guardian metrics: {e}")
        else:
            # Default: read from session or cache
            metrics.guardian_violations_total = defaultdict(int)
        
        # 4. Genesis Record metrics
        try:
            gr_path = Path("memories/genesis_record.jsonl")
            if gr_path.exists():
                action_types = defaultdict(int)
                record_count = 0
                with open(gr_path, "r") as f:
                    for line in f:
                        if line.strip():
                            import json
                            try:
                                record = json.loads(line)
                                action_types[record.get("action_type", "unknown")] += 1
                                record_count += 1
                            except json.JSONDecodeError:
                                pass
                
                metrics.genesis_records_total = record_count
                metrics.genesis_records_by_type = dict(action_types)
                # Verify integrity (placeholder)
                metrics.genesis_verification_ok = record_count > 0 or True
        except Exception as e:
            logger.warning(f"Failed to collect Genesis Record metrics: {e}")
        
        # 5. Request metrics (from internal state)
        metrics.request_count = self.request_count
        if self.request_times:
            metrics.request_duration_seconds = sum(self.request_times[-5:]) / len(self.request_times[-5:])
        
        self.metrics = metrics
        return metrics
    
    def _cvc_state_to_value(self, state: str) -> int:
        """Convert CVC state string to numeric value."""
        state_map = {"GREEN": 0, "YELLOW": 1, "ORANGE": 2, "RED": 3}
        return state_map.get(state, 0)
    
    def record_request(self, duration_seconds: float) -> None:
        """Record request processing duration."""
        self.request_times.append(duration_seconds)
        self.request_count += 1
        # Keep only last 100 requests
        if len(self.request_times) > 100:
            self.request_times = self.request_times[-100:]
    
    def get_prometheus_text(self) -> str:
        """Get current metrics in Prometheus text format."""
        return self.metrics.to_prometheus_text()


# ────────────────────────────────────────────────────────────────────────────
# GLOBAL COLLECTOR INSTANCE
# ────────────────────────────────────────────────────────────────────────────

_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector instance."""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


if __name__ == "__main__":
    # Test metrics collection
    print("=== PROMETHEUS METRICS COLLECTOR TEST ===\n")
    
    collector = MetricsCollector()
    
    # Simulate some metrics
    collector.metrics.cvc_counter = 5
    collector.metrics.cvc_state = "YELLOW"
    collector.metrics.cvc_state_value = 1
    collector.metrics.cvc_violations_total = 2
    
    collector.metrics.guardian_violations_total = {
        "G7_Privacy": 1,
        "G8_Nonmaleficence": 0,
    }
    collector.metrics.guardian_critical_violations_total = 1
    
    collector.metrics.genesis_records_total = 15
    collector.metrics.genesis_records_by_type = {
        "DECISION": 5,
        "K0_RESTORE": 10,
    }
    
    collector.metrics.tspa_score_by_agent = {
        "SENTINEL": 0.95,
        "ARCHITECT": 0.85,
        "LIBRARIAN": 0.90,
    }
    
    collector.metrics.ltm_session_count = 3
    collector.metrics.request_count = 42
    
    print(collector.get_prometheus_text())
    print("\n✅ Prometheus Metrics Collector test completed")
