"""SessionCoordinator — Orchestrates parallel execution of autonomous agents

Manages:
- Queue-based inter-agent communication (Scout→Analyze→Bid→Track)
- Aggressive parallelization with configurable worker pools
- Agent lifecycle and failure handling
- Performance metrics and monitoring
"""

from __future__ import annotations

import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime

from arbitrage.agents.base_agent import BaseAutonomousAgent
from arbitrage.agents.scout_agent import ScoutAgent
from arbitrage.agents.analyze_agent import AnalyzeAgent
from arbitrage.agents.bid_agent import BidAgent
from arbitrage.agents.track_agent import TrackAgent

logger = logging.getLogger("adrion.agents.session_coordinator")


class SessionCoordinator:
    """Coordinates parallel execution of all autonomous agents."""

    def __init__(
        self,
        session_id: str,
        num_analyzers: int = 4,
        enable_rag: bool = False,
    ):
        """Initialize session coordinator.

        Args:
            session_id: Unique session identifier
            num_analyzers: Number of parallel analyzer workers (default: 4)
            enable_rag: Whether to enable RAG for analyzers (default: False)
        """
        self.session_id = session_id
        self.num_analyzers = num_analyzers
        self.enable_rag = enable_rag
        self.logger = logging.getLogger(f"adrion.coordinator.{session_id}")

        # Create agents
        self.scout = ScoutAgent()
        self.analyzers = [
            AnalyzeAgent(
                agent_id=f"analyze-{i:03d}",
                agent_name=f"Analyzer {i}",
                trust_score=0.88,
                use_rag=enable_rag,
            )
            for i in range(num_analyzers)
        ]
        self.bidder = BidAgent()
        self.tracker = TrackAgent()

        # Queues for inter-agent communication
        self.scout_queue = asyncio.Queue()          # Scout output
        self.analyze_queues = [asyncio.Queue() for _ in range(num_analyzers)]  # Per-analyzer inputs
        self.worthy_jobs_queue = asyncio.Queue()    # Analyzers → Bidder
        self.bid_queue = asyncio.Queue()            # Bidder output → Tracker

        # Results aggregation
        self.scout_results = []
        self.analysis_results = []
        self.bid_results = []
        self.tracking_results = []

        self.start_time = None
        self.end_time = None

    async def orchestrate(
        self,
        filters: Optional[Dict] = None,
        max_duration_seconds: int = 300,
    ) -> Dict:
        """Orchestrate full parallel pipeline.

        Pipeline sequence:
        1. Scout fetches jobs → feeds to analyzers
        2. N Analyzers process in parallel → signal bidder on worthy jobs
        3. Bidder creates/submits bids → signals tracker
        4. Tracker monitors continuously

        Args:
            filters: Scout filters (status, type, etc.)
            max_duration_seconds: Maximum execution time

        Returns:
            dict with aggregated results and metrics
        """
        self.start_time = datetime.utcnow()
        self.logger.info(
            "Starting orchestration: session_id=%s, analyzers=%d, duration_max=%ds",
            self.session_id,
            self.num_analyzers,
            max_duration_seconds,
        )

        try:
            # Create tasks for all agents
            scout_task = asyncio.create_task(self._run_scout(filters))
            analyzer_tasks = [
                asyncio.create_task(self._run_analyzer(i))
                for i in range(self.num_analyzers)
            ]
            bidder_task = asyncio.create_task(self._run_bidder())
            tracker_task = asyncio.create_task(self._run_tracker())

            # Wait for all tasks with timeout
            await asyncio.wait_for(
                asyncio.gather(
                    scout_task,
                    *analyzer_tasks,
                    bidder_task,
                    tracker_task,
                    return_exceptions=True,
                ),
                timeout=max_duration_seconds,
            )

            self.end_time = datetime.utcnow()
            duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

            self.logger.info(
                "Orchestration complete: duration=%.0fms, scout_results=%d, "
                "analysis_results=%d, bids=%d",
                duration_ms,
                len(self.scout_results),
                len(self.analysis_results),
                len(self.bid_results),
            )

            return self._aggregate_results()

        except asyncio.TimeoutError:
            self.logger.error("Orchestration exceeded max duration")
            return self._aggregate_results(timeout=True)
        except Exception as exc:
            self.logger.error("Orchestration failed: %s", exc)
            raise

    async def _run_scout(self, filters: Optional[Dict]) -> None:
        """Run scout agent: fetch and filter jobs.

        Queues jobs for analyzers to process.
        """
        self.logger.info("Scout: Starting job fetch")

        scout_input = {"filters": filters or {}}

        try:
            result = await self.scout.run_with_retry(scout_input)

            if result["success"]:
                jobs = result["result"].get("jobs_ready", [])
                self.scout_results.append(result["result"])

                self.logger.info("Scout: Queuing %d jobs to analyzers", len(jobs))

                # Distribute jobs round-robin to analyzers
                for idx, job in enumerate(jobs):
                    analyzer_queue = self.analyze_queues[idx % self.num_analyzers]
                    await analyzer_queue.put(job)

                # Signal analyzers that scout is done
                for queue in self.analyze_queues:
                    await queue.put(None)  # Sentinel

            else:
                self.logger.error("Scout failed: %s", result.get("error"))

        except Exception as exc:
            self.logger.error("Scout execution error: %s", exc)

    async def _run_analyzer(self, analyzer_idx: int) -> None:
        """Run analyzer agent: process jobs from queue.

        Processes jobs concurrently with other analyzers.
        Queues worthy jobs to bidder.
        """
        analyzer = self.analyzers[analyzer_idx]
        queue = self.analyze_queues[analyzer_idx]

        self.logger.debug("Analyzer %d: Starting", analyzer_idx)

        try:
            while True:
                # Get job from queue
                job = await queue.get()

                # Check for sentinel (end of jobs)
                if job is None:
                    self.logger.debug("Analyzer %d: End of jobs signal", analyzer_idx)
                    break

                self.logger.debug("Analyzer %d: Processing job %s", analyzer_idx, job.get("id"))

                # Analyze job
                try:
                    analysis = await analyzer.run_with_retry({"job": job})

                    if analysis["success"]:
                        analysis_result = analysis["result"]
                        self.analysis_results.append(analysis_result)

                        # If worthy, queue for bidding
                        if analysis_result.get("worthy"):
                            await self.worthy_jobs_queue.put({
                                "job": job,
                                "analysis": analysis_result,
                            })

                    else:
                        self.logger.warning("Analyzer %d: Analysis failed for %s",
                                          analyzer_idx, job.get("id"))

                except Exception as e:
                    self.logger.error(
                        "Analyzer %d: Processing error for job %s: %s",
                        analyzer_idx,
                        job.get("id"),
                        str(e),
                    )

        except Exception as exc:
            self.logger.error("Analyzer %d execution error: %s", analyzer_idx, exc)

    async def _run_bidder(self) -> None:
        """Run bidder agent: process worthy jobs.

        Creates and submits bids for worthy jobs from analyzers.
        """
        self.logger.info("Bidder: Starting bid processing")

        try:
            while True:
                # Try to get worthy job with timeout
                try:
                    worthy_job_data = await asyncio.wait_for(
                        self.worthy_jobs_queue.get(),
                        timeout=2.0,
                    )
                except asyncio.TimeoutError:
                    # No more jobs within timeout, check if Scout is done
                    if self.scout_results:  # Scout completed
                        self.logger.info("Bidder: No more worthy jobs, finishing")
                        break
                    continue

                job = worthy_job_data.get("job")
                analysis = worthy_job_data.get("analysis")

                self.logger.debug("Bidder: Creating bid for job %s", job.get("id"))

                try:
                    bid_result = await self.bidder.run_with_retry({
                        "job": job,
                        "analysis": analysis,
                    })

                    if bid_result["success"]:
                        self.bid_results.append(bid_result["result"])

                        # Queue for tracking
                        await self.bid_queue.put(bid_result["result"])

                    else:
                        self.logger.warning("Bidder: Bid creation failed for %s",
                                          job.get("id"))

                except Exception as e:
                    self.logger.error("Bidder: Processing error: %s", str(e))

        except Exception as exc:
            self.logger.error("Bidder execution error: %s", exc)

    async def _run_tracker(self) -> None:
        """Run tracker agent: monitor session health.

        Polls system health periodically.
        Doesn't consume bid queue directly (just monitors).
        """
        self.logger.info("Tracker: Starting health monitoring")

        check_interval = 5  # Check every 5 seconds
        max_checks = 30  # Max checks (150 seconds total)

        try:
            for check_num in range(max_checks):
                try:
                    tracking_result = await self.tracker.run_with_retry({
                        "session_id": self.session_id,
                        "check_xrp": True,
                        "check_limits": True,
                        "check_health": True,
                    })

                    if tracking_result["success"]:
                        self.tracking_results.append(tracking_result["result"])
                        status = tracking_result["result"].get("health_status")
                        self.logger.debug("Tracker: Health check %d - %s",
                                        check_num + 1, status)

                except Exception as e:
                    self.logger.warning("Tracker: Check failed: %s", str(e))

                # Wait before next check
                await asyncio.sleep(check_interval)

        except Exception as exc:
            self.logger.error("Tracker execution error: %s", exc)

    def _aggregate_results(self, timeout: bool = False) -> Dict:
        """Aggregate results from all agents.

        Returns:
            dict with comprehensive execution results and metrics
        """
        duration_ms = (
            (self.end_time - self.start_time).total_seconds() * 1000
            if self.start_time and self.end_time
            else 0.0
        )

        # Collect agent metrics
        agent_metrics = {
            "scout": self.scout.get_scout_stats(),
            "analyzers": [a.get_analyzer_stats() for a in self.analyzers],
            "bidder": self.bidder.get_bidder_stats(),
            "tracker": self.tracker.get_tracker_stats(),
        }

        # Calculate parallelization factor
        # If sequential: Scout time + sum(Analyzer times) + Bid time + Track time
        # Actual parallel: max of concurrent tasks
        parallel_factor = (
            len(self.analysis_results) / max(1, self.num_analyzers)
            if len(self.analysis_results) > 0
            else 1.0
        )

        return {
            "session_id": self.session_id,
            "status": "completed" if not timeout else "timeout",
            "duration_ms": round(duration_ms, 2),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "scout_results": self.scout_results,
            "analysis_results": self.analysis_results,
            "bid_results": self.bid_results,
            "tracking_results": self.tracking_results,
            "summary": {
                "jobs_processed": len(self.analysis_results),
                "jobs_worthy": sum(1 for r in self.analysis_results if r.get("worthy")),
                "bids_created": len(self.bid_results),
                "parallel_factor": round(parallel_factor, 2),
                "throughput_jobs_per_sec": round(
                    len(self.analysis_results) / (duration_ms / 1000)
                    if duration_ms > 0
                    else 0,
                    2,
                ),
            },
            "agent_metrics": agent_metrics,
        }
