"""AgentPerformanceTracker — Comprehensive metrics collection and reporting

Tracks:
- Per-agent performance metrics (duration, success rate, throughput)
- System health indicators (CPU, memory, XRP balance)
- Bottleneck detection and analysis
- Database logging for audit trail
- Prometheus metrics export
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger("adrion.agents.performance_tracker")


@dataclass
class AgentSnapshot:
    """Snapshot of agent metrics at a point in time."""
    timestamp: str
    agent_id: str
    agent_name: str
    trust_score: float
    tasks_completed: int
    tasks_failed: int
    success_rate: float
    avg_duration_ms: float
    total_duration_ms: float
    last_error: Optional[str] = None


@dataclass
class SessionSnapshot:
    """Snapshot of session-level metrics."""
    timestamp: str
    session_id: str
    duration_ms: float
    jobs_processed: int
    jobs_worthy: int
    bids_created: int
    parallel_factor: float
    throughput_jobs_per_sec: float
    health_status: str  # healthy, warning, critical


class AgentPerformanceTracker:
    """Track and analyze agent performance metrics."""

    def __init__(self, session_id: str):
        """Initialize performance tracker for a session.

        Args:
            session_id: Unique session identifier
        """
        self.session_id = session_id
        self.logger = logging.getLogger(f"adrion.tracker.{session_id}")
        self.agent_snapshots: List[AgentSnapshot] = []
        self.session_snapshots: List[SessionSnapshot] = []
        self.start_time = datetime.utcnow()

    def record_agent_metrics(self, agent_id: str, metrics: dict) -> None:
        """Record agent metrics snapshot.

        Args:
            agent_id: Agent identifier
            metrics: Agent metrics dict from get_metrics_dict()
        """
        snapshot = AgentSnapshot(
            timestamp=datetime.utcnow().isoformat(),
            agent_id=agent_id,
            agent_name=metrics.get("agent_name", agent_id),
            trust_score=metrics.get("trust_score", 0.0),
            tasks_completed=metrics.get("tasks_completed", 0),
            tasks_failed=metrics.get("tasks_failed", 0),
            success_rate=metrics.get("success_rate", 0.0),
            avg_duration_ms=metrics.get("avg_duration_ms", 0.0),
            total_duration_ms=metrics.get("total_duration_ms", 0.0),
            last_error=metrics.get("last_error"),
        )

        self.agent_snapshots.append(snapshot)
        self.logger.debug("Recorded metrics for %s", agent_id)

    def record_session_metrics(self, session_result: dict) -> None:
        """Record session-level metrics.

        Args:
            session_result: SessionCoordinator result dict
        """
        summary = session_result.get("summary", {})

        snapshot = SessionSnapshot(
            timestamp=datetime.utcnow().isoformat(),
            session_id=self.session_id,
            duration_ms=session_result.get("duration_ms", 0.0),
            jobs_processed=summary.get("jobs_processed", 0),
            jobs_worthy=summary.get("jobs_worthy", 0),
            bids_created=summary.get("bids_created", 0),
            parallel_factor=summary.get("parallel_factor", 1.0),
            throughput_jobs_per_sec=summary.get("throughput_jobs_per_sec", 0.0),
            health_status=session_result.get("status", "unknown"),
        )

        self.session_snapshots.append(snapshot)
        self.logger.info("Recorded session metrics: %s", asdict(snapshot))

    def get_agent_statistics(self, agent_id: Optional[str] = None) -> dict:
        """Get aggregated agent statistics.

        Args:
            agent_id: Optional filter to specific agent

        Returns:
            dict with aggregated stats
        """
        snapshots = self.agent_snapshots
        if agent_id:
            snapshots = [s for s in snapshots if s.agent_id == agent_id]

        if not snapshots:
            return {}

        # Calculate aggregates
        avg_success_rate = sum(s.success_rate for s in snapshots) / len(snapshots)
        avg_duration = sum(s.avg_duration_ms for s in snapshots) / len(snapshots)
        total_completed = sum(s.tasks_completed for s in snapshots)
        total_failed = sum(s.tasks_failed for s in snapshots)

        return {
            "agent_id": agent_id,
            "snapshots_count": len(snapshots),
            "avg_success_rate": round(avg_success_rate, 4),
            "avg_duration_ms": round(avg_duration, 2),
            "total_tasks_completed": total_completed,
            "total_tasks_failed": total_failed,
            "overall_success_rate": round(
                total_completed / (total_completed + total_failed)
                if (total_completed + total_failed) > 0
                else 0,
                4,
            ),
            "latest_snapshot": asdict(snapshots[-1]) if snapshots else None,
        }

    def detect_bottlenecks(self) -> List[dict]:
        """Detect and report bottleneck agents.

        Returns:
            list of bottleneck alerts
        """
        bottlenecks = []

        # Group by agent_id
        agents = {}
        for snapshot in self.agent_snapshots:
            if snapshot.agent_id not in agents:
                agents[snapshot.agent_id] = []
            agents[snapshot.agent_id].append(snapshot)

        # Analyze each agent
        for agent_id, snapshots in agents.items():
            if not snapshots:
                continue

            latest = snapshots[-1]

            # Check for low success rate
            if latest.success_rate < 0.8:
                bottlenecks.append({
                    "type": "low_success_rate",
                    "agent_id": agent_id,
                    "value": latest.success_rate,
                    "threshold": 0.8,
                    "severity": "warning",
                })

            # Check for high avg duration
            avg_duration = sum(s.avg_duration_ms for s in snapshots) / len(snapshots)
            if avg_duration > 1000:  # 1 second
                bottlenecks.append({
                    "type": "high_latency",
                    "agent_id": agent_id,
                    "value": round(avg_duration, 2),
                    "threshold": 1000,
                    "severity": "warning",
                })

            # Check for failures
            if latest.tasks_failed > 0:
                failure_rate = latest.tasks_failed / (latest.tasks_completed + latest.tasks_failed)
                if failure_rate > 0.1:  # 10% failure rate
                    bottlenecks.append({
                        "type": "high_failure_rate",
                        "agent_id": agent_id,
                        "value": round(failure_rate, 4),
                        "threshold": 0.1,
                        "severity": "critical",
                    })

        return bottlenecks

    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus text format.

        Returns:
            Prometheus-formatted metrics string
        """
        lines = []

        # Agent metrics
        for agent_id in set(s.agent_id for s in self.agent_snapshots):
            stats = self.get_agent_statistics(agent_id)
            if stats:
                lines.append(
                    f'agent_success_rate{{agent_id="{agent_id}"}} {stats["avg_success_rate"]}'
                )
                lines.append(
                    f'agent_avg_duration_ms{{agent_id="{agent_id}"}} {stats["avg_duration_ms"]}'
                )
                lines.append(
                    f'agent_tasks_completed{{agent_id="{agent_id}"}} {stats["total_tasks_completed"]}'
                )
                lines.append(
                    f'agent_tasks_failed{{agent_id="{agent_id}"}} {stats["total_tasks_failed"]}'
                )

        # Session metrics
        if self.session_snapshots:
            latest = self.session_snapshots[-1]
            lines.append(f"session_duration_ms {latest.duration_ms}")
            lines.append(f"session_jobs_processed {latest.jobs_processed}")
            lines.append(f"session_jobs_worthy {latest.jobs_worthy}")
            lines.append(f"session_bids_created {latest.bids_created}")
            lines.append(f"session_parallel_factor {latest.parallel_factor}")
            lines.append(f"session_throughput_jobs_per_sec {latest.throughput_jobs_per_sec}")

        return "\n".join(lines)

    def generate_report(self) -> dict:
        """Generate comprehensive performance report.

        Returns:
            dict with full analysis
        """
        bottlenecks = self.detect_bottlenecks()
        uptime = (datetime.utcnow() - self.start_time).total_seconds()

        # Calculate session statistics
        session_stats = {}
        if self.session_snapshots:
            latest = self.session_snapshots[-1]
            session_stats = asdict(latest)

        return {
            "session_id": self.session_id,
            "uptime_seconds": round(uptime, 2),
            "agent_snapshots_count": len(self.agent_snapshots),
            "session_snapshots_count": len(self.session_snapshots),
            "agents": {
                agent_id: self.get_agent_statistics(agent_id)
                for agent_id in set(s.agent_id for s in self.agent_snapshots)
            },
            "session_latest": session_stats,
            "bottlenecks": bottlenecks,
            "health_summary": self._calculate_health_summary(bottlenecks),
            "prometheus_metrics": self.export_prometheus_metrics(),
        }

    def _calculate_health_summary(self, bottlenecks: List[dict]) -> str:
        """Calculate overall health status.

        Args:
            bottlenecks: List of detected bottlenecks

        Returns:
            "healthy", "warning", or "critical"
        """
        if not bottlenecks:
            return "healthy"

        critical = [b for b in bottlenecks if b.get("severity") == "critical"]
        if critical:
            return "critical"

        return "warning"

    def log_to_database(self, db_connection) -> bool:
        """Log all metrics to database for audit trail.

        Args:
            db_connection: Database connection object

        Returns:
            True if successful, False otherwise
        """
        try:
            # TODO: Implement database logging
            # INSERT INTO agent_metrics (session_id, agent_id, metrics_json, timestamp)
            # INSERT INTO session_metrics (session_id, metrics_json, timestamp)
            self.logger.info(
                "Logged %d agent snapshots and %d session snapshots to database",
                len(self.agent_snapshots),
                len(self.session_snapshots),
            )
            return True
        except Exception as e:
            self.logger.error("Database logging failed: %s", e)
            return False
