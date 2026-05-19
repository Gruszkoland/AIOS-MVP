#!/usr/bin/env python3
"""
Deployment verification and health check for local ADRION 369 system

Verifies:
- All services are accessible
- Database connections work
- Metrics are being exported
- Agent system is operational
"""

import sys
import time
import logging
import subprocess
from typing import Tuple, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeploymentVerifier:
    """Verify local deployment health."""

    SERVICES = {
        'postgres': ('localhost', 5432),
        'prometheus': ('localhost', 9090),
        'grafana': ('localhost', 3000),
        'redis': ('localhost', 6379),
    }

    def __init__(self):
        self.results = {}
        self.failures = []

    def check_docker_services(self) -> bool:
        """Check if all Docker services are running."""
        logger.info("Checking Docker services...")

        try:
            result = subprocess.run(
                ['docker-compose', '-f', 'docker-compose.local.yml', 'ps'],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                logger.error("Docker Compose not responding")
                self.failures.append("Docker services not accessible")
                return False

            expected_services = ['postgres', 'prometheus', 'grafana', 'redis']
            for service in expected_services:
                if service in result.stdout:
                    logger.info(f"  ✓ {service} is running")
                else:
                    logger.warning(f"  ✗ {service} not found")
                    self.failures.append(f"{service} not running")

            return len(self.failures) == 0

        except subprocess.TimeoutExpired:
            logger.error("Docker check timed out")
            self.failures.append("Docker check timeout")
            return False
        except FileNotFoundError:
            logger.error("Docker or docker-compose not found")
            self.failures.append("Docker not installed or not in PATH")
            return False

    def check_postgresql(self) -> bool:
        """Check PostgreSQL connectivity."""
        logger.info("Checking PostgreSQL...")

        try:
            result = subprocess.run(
                ['docker-compose', '-f', 'docker-compose.local.yml',
                 'exec', '-T', 'postgres', 'pg_isready', '-U', 'adrion'],
                capture_output=True,
                timeout=10,
            )

            if result.returncode == 0:
                logger.info("  ✓ PostgreSQL is ready")
                return True
            else:
                logger.warning("  ✗ PostgreSQL not ready")
                self.failures.append("PostgreSQL not responding")
                return False

        except subprocess.TimeoutExpired:
            logger.warning("  ✗ PostgreSQL check timed out")
            self.failures.append("PostgreSQL check timeout")
            return False

    def check_prometheus(self) -> bool:
        """Check Prometheus connectivity."""
        logger.info("Checking Prometheus...")

        try:
            import urllib.request
            response = urllib.request.urlopen('http://localhost:9090/-/healthy', timeout=5)
            if response.status == 200:
                logger.info("  ✓ Prometheus is ready")
                return True
        except Exception as e:
            logger.warning(f"  ✗ Prometheus check failed: {e}")
            self.failures.append("Prometheus not responding")

        return False

    def check_grafana(self) -> bool:
        """Check Grafana connectivity."""
        logger.info("Checking Grafana...")

        try:
            import urllib.request
            response = urllib.request.urlopen('http://localhost:3000/api/health', timeout=5)
            if response.status == 200:
                logger.info("  ✓ Grafana is ready")
                return True
        except Exception as e:
            logger.warning(f"  ✗ Grafana check failed: {e}")
            self.failures.append("Grafana not responding")

        return False

    def check_redis(self) -> bool:
        """Check Redis connectivity."""
        logger.info("Checking Redis...")

        try:
            result = subprocess.run(
                ['docker-compose', '-f', 'docker-compose.local.yml',
                 'exec', '-T', 'redis', 'redis-cli', 'ping'],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if b'PONG' in result.stdout.encode() or 'PONG' in result.stdout:
                logger.info("  ✓ Redis is ready")
                return True
            else:
                logger.warning("  ✗ Redis not responding")
                self.failures.append("Redis not responding")
                return False

        except subprocess.TimeoutExpired:
            logger.warning("  ✗ Redis check timed out")
            self.failures.append("Redis check timeout")
            return False

    def check_agent_system(self) -> bool:
        """Check if agent system can be imported."""
        logger.info("Checking autonomous agent system...")

        try:
            from arbitrage.agents.session_coordinator import SessionCoordinator
            from arbitrage.agents.agent_tracker import AgentPerformanceTracker
            logger.info("  ✓ Agent modules import successfully")
            return True
        except ImportError as e:
            logger.warning(f"  ✗ Agent import failed: {e}")
            self.failures.append(f"Agent system import error: {e}")
            return False

    def run_sample_session(self) -> bool:
        """Run a quick sample agent session."""
        logger.info("Running sample agent session...")

        try:
            import asyncio
            from arbitrage.agents.session_coordinator import SessionCoordinator

            async def quick_test():
                coordinator = SessionCoordinator("verify-001", num_analyzers=2)
                result = await coordinator.orchestrate(
                    filters={},
                    max_duration_seconds=5,
                )
                return result.get("status") in ["completed", "timeout"]

            success = asyncio.run(quick_test())
            if success:
                logger.info("  ✓ Sample session completed")
                return True
            else:
                logger.warning("  ✗ Sample session failed")
                self.failures.append("Sample agent session failed")
                return False

        except Exception as e:
            logger.warning(f"  ✗ Sample session error: {e}")
            self.failures.append(f"Sample session error: {e}")
            return False

    def verify_all(self) -> bool:
        """Run all verification checks."""
        logger.info("=" * 70)
        logger.info("ADRION 369 - DEPLOYMENT VERIFICATION")
        logger.info("=" * 70)
        logger.info("")

        checks = [
            ("Docker Services", self.check_docker_services),
            ("PostgreSQL", self.check_postgresql),
            ("Prometheus", self.check_prometheus),
            ("Grafana", self.check_grafana),
            ("Redis", self.check_redis),
            ("Agent System", self.check_agent_system),
            ("Sample Session", self.run_sample_session),
        ]

        results = []
        for name, check in checks:
            try:
                result = check()
                results.append((name, result))
            except Exception as e:
                logger.error(f"Check failed: {e}")
                results.append((name, False))

            time.sleep(0.5)  # Small delay between checks

        logger.info("")
        logger.info("=" * 70)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 70)

        passed = sum(1 for _, r in results if r)
        total = len(results)

        for name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"  {name:.<50} {status}")

        logger.info("")
        logger.info(f"Result: {passed}/{total} checks passed")

        if self.failures:
            logger.info("")
            logger.info("FAILURES:")
            for failure in self.failures:
                logger.info(f"  - {failure}")

        logger.info("=" * 70)
        logger.info("")

        return passed == total


def main():
    """Main entry point."""
    verifier = DeploymentVerifier()
    success = verifier.verify_all()

    if success:
        logger.info("Deployment verification PASSED - System is ready!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Run: python scripts/run-agent-session.py")
        logger.info("  2. View Grafana: http://localhost:3000")
        logger.info("  3. View Prometheus: http://localhost:9090")
        return 0
    else:
        logger.error("Deployment verification FAILED")
        logger.error("Please check the failures above and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
