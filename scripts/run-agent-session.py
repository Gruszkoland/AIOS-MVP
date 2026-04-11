#!/usr/bin/env python3
"""
Local autonomous agent session runner with metrics export

Runs a complete Session Coordinator orchestration and exports metrics
to the local Prometheus + Grafana stack.

Usage:
    python scripts/run-agent-session.py [--session-id SESSION_ID] [--num-analyzers N]
"""

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

try:
    from arbitrage.agents.session_coordinator import SessionCoordinator
    from arbitrage.agents.agent_tracker import AgentPerformanceTracker
except ImportError as e:
    logger.error(f"Failed to import agents: {e}")
    logger.error("Make sure you're in the project root directory")
    sys.exit(1)


async def run_session(session_id: str, num_analyzers: int = 4, enable_rag: bool = False):
    """Run autonomous agent session.

    Args:
        session_id: Unique session identifier
        num_analyzers: Number of parallel analyzer workers
        enable_rag: Whether to enable RAG enhancement
    """
    logger.info(f"Starting session {session_id} with {num_analyzers} analyzers")

    # Initialize coordinator
    coordinator = SessionCoordinator(
        session_id=session_id,
        num_analyzers=num_analyzers,
        enable_rag=enable_rag,
    )

    # Initialize tracker for metrics
    tracker = AgentPerformanceTracker(session_id)

    try:
        # Execute pipeline
        logger.info("Executing parallel orchestration pipeline...")
        result = await coordinator.orchestrate(
            filters={"status": "open", "min_value": 50},
            max_duration_seconds=60,  # Local: shorter timeout
        )

        # Record metrics
        logger.info("Recording performance metrics...")
        logger.info(f"Agent Metrics: {len(result['agent_metrics'])} agents tracked")

        for agent_name, agent_metrics in result["agent_metrics"].items():
            if isinstance(agent_metrics, dict):
                for agent_id_key, metrics_dict in agent_metrics.items():
                    tracker.record_agent_metrics(str(agent_id_key), metrics_dict)

        tracker.record_session_metrics(result)

        # Generate report
        report = tracker.generate_report()

        return result, report

    except Exception as e:
        logger.error(f"Session failed: {e}", exc_info=True)
        raise


def export_results(session_id: str, result: dict, report: dict):
    """Export results to JSON files and display summary.

    Args:
        session_id: Session identifier
        result: Orchestration result from SessionCoordinator
        report: Performance report from AgentPerformanceTracker
    """
    # Create results directory
    results_dir = Path("./reports/local-sessions")
    results_dir.mkdir(parents=True, exist_ok=True)

    # Export raw results
    results_file = results_dir / f"{session_id}_results.json"
    with open(results_file, "w") as f:
        json.dump(result, f, indent=2, default=str)
    logger.info(f"Results exported to {results_file}")

    # Export report
    report_file = results_dir / f"{session_id}_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"Report exported to {report_file}")

    # Display summary
    print_summary(result, report)


def print_summary(result: dict, report: dict):
    """Display execution summary in console.

    Args:
        result: Orchestration result
        report: Performance report
    """
    print("\n" + ("=" * 70))
    print(" AUTONOMOUS AGENT SESSION - EXECUTION SUMMARY ".center(70, "="))
    print("=" * 70 + "\n")

    # Pipeline summary
    summary = result.get("summary", {})
    print("PIPELINE EXECUTION:")
    print(f"  Duration:           {result.get('duration_ms', 0):.1f} ms")
    print(f"  Jobs Processed:     {summary.get('jobs_processed', 0)}")
    print(f"  Jobs Worthy:        {summary.get('jobs_worthy', 0)}")
    print(f"  Bids Created:       {summary.get('bids_created', 0)}")
    print(f"  Parallel Factor:    {summary.get('parallel_factor', 1.0):.2f}x")
    print(f"  Throughput:         {summary.get('throughput_jobs_per_sec', 0):.2f} jobs/sec")
    print()

    # Agent summary
    print("AGENT PERFORMANCE:")
    for agent_id, agent_report in report.get("agents", {}).items():
        if isinstance(agent_report, dict) and "latest_snapshot" in agent_report:
            snapshot = agent_report["latest_snapshot"]
            print(f"  {agent_id}:")
            print(f"    Success Rate:   {agent_report.get('avg_success_rate', 0):.1%}")
            print(f"    Avg Duration:   {agent_report.get('avg_duration_ms', 0):.1f} ms")
            print(f"    Tasks:          {agent_report.get('total_tasks_completed', 0)} ✓ "
                  f"{agent_report.get('total_tasks_failed', 0)} ✗")
    print()

    # Health status
    print("SYSTEM HEALTH:")
    print(f"  Status:             {report.get('health_summary', 'unknown').upper()}")
    print(f"  Bottlenecks:        {len(report.get('bottlenecks', []))} detected")
    if report.get("bottlenecks"):
        for bottleneck in report["bottlenecks"]:
            print(f"    - {bottleneck['type']}: {bottleneck['agent_id']} "
                  f"({bottleneck['severity'].upper()})")
    print()

    # Next steps
    print("MONITORING:")
    print("  Grafana Dashboard:  http://localhost:3000")
    print("  Prometheus:         http://localhost:9090")
    print()
    print("=" * 70 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run ADRION 369 autonomous agent session locally",
    )
    parser.add_argument(
        "--session-id",
        default=f"local-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        help="Session identifier (default: timestamp)",
    )
    parser.add_argument(
        "--num-analyzers",
        type=int,
        default=4,
        help="Number of parallel analyzer workers (default: 4)",
    )
    parser.add_argument(
        "--enable-rag",
        action="store_true",
        help="Enable RAG enhancement for analyzers",
    )

    args = parser.parse_args()

    logger.info("="*70)
    logger.info("ADRION 369 - LOCAL AUTONOMOUS AGENT SESSION")
    logger.info("="*70)

    try:
        # Run session
        result, report = asyncio.run(
            run_session(
                session_id=args.session_id,
                num_analyzers=args.num_analyzers,
                enable_rag=args.enable_rag,
            )
        )

        # Export and display results
        export_results(args.session_id, result, report)

        logger.info("Session completed successfully!")
        return 0

    except KeyboardInterrupt:
        logger.warning("Session interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Session failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
