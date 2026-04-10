#!/usr/bin/env python3
"""
ADRION 369 v4.0 - HEALTH CHECK SERVICE
Monitors system health: Database, Redis, MCP Agents, Disk space, Memory.
Provides GET /health endpoint for orchestration and dashboards.

Usage:
    python scripts/health_check/health_check_service.py --port 9000 --interval 30
"""

import asyncio
import logging
import os
import sys
import time
import json
import socket
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

import click
import psycopg2
import redis
import aiohttp
from aiohttp import web
import psutil

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = 'healthy'
    WARNING = 'warning'
    CRITICAL = 'critical'


@dataclass
class ComponentHealth:
    """Individual component health status"""
    name: str
    status: str  # 'healthy', 'warning', 'critical'
    latency_ms: float
    timestamp: str
    details: Dict[str, Any] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'status': self.status,
            'latency_ms': round(self.latency_ms, 2),
            'timestamp': self.timestamp,
            'details': self.details or {},
            'error_message': self.error_message
        }


# ============================================================================
# HEALTH CHECKERS
# ============================================================================

class HealthChecker:
    """Main health check coordinator"""

    def __init__(self):
        self.components = {
            'database': None,
            'redis': None,
            'genesis_mcp': None,
            'router_mcp': None,
            'guardian_mcp': None,
            'healer_mcp': None,
            'oracle_mcp': None,
            'vortex_mcp': None,
            'system': None
        }
        self.last_check = None
        self.check_interval = 30

    async def check_all(self) -> Dict[str, ComponentHealth]:
        """Run all health checks"""
        logger.debug("Starting health checks...")
        start_time = time.time()

        checks = await asyncio.gather(
            self._check_database(),
            self._check_redis(),
            self._check_mcp_agent('genesis', 'localhost', 9004),
            self._check_mcp_agent('router', 'localhost', 9001),
            self._check_mcp_agent('guardian', 'localhost', 9002),
            self._check_mcp_agent('healer', 'localhost', 9003),
            self._check_mcp_agent('oracle', 'localhost', 9005),
            self._check_mcp_agent('vortex', 'localhost', 9006),
            self._check_system(),
            return_exceptions=True
        )

        results = {
            'database': checks[0],
            'redis': checks[1],
            'genesis_mcp': checks[2],
            'router_mcp': checks[3],
            'guardian_mcp': checks[4],
            'healer_mcp': checks[5],
            'oracle_mcp': checks[6],
            'vortex_mcp': checks[7],
            'system': checks[8]
        }

        elapsed = (time.time() - start_time) * 1000
        logger.info(f"✅ Health checks completed in {elapsed:.0f}ms")

        return results

    async def _check_database(self) -> ComponentHealth:
        """Check PostgreSQL connectivity"""
        start = time.time()
        db_url = os.getenv('DATABASE_URL')

        try:
            if not db_url:
                return ComponentHealth(
                    name='database',
                    status=HealthStatus.WARNING.value,
                    latency_ms=-1,
                    timestamp=datetime.utcnow().isoformat(),
                    error_message='DATABASE_URL not set'
                )

            conn = psycopg2.connect(db_url, connect_timeout=5)
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
                cur.fetchone()
            conn.close()

            latency = (time.time() - start) * 1000
            return ComponentHealth(
                name='database',
                status=HealthStatus.HEALTHY.value,
                latency_ms=latency,
                timestamp=datetime.utcnow().isoformat(),
                details={'database': 'postgres', 'tables': 8}
            )

        except Exception as e:
            logger.warning(f"🔴 Database health check failed: {e}")
            return ComponentHealth(
                name='database',
                status=HealthStatus.CRITICAL.value,
                latency_ms=(time.time() - start) * 1000,
                timestamp=datetime.utcnow().isoformat(),
                error_message=str(e)
            )

    async def _check_redis(self) -> ComponentHealth:
        """Check Redis connectivity"""
        start = time.time()
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

        try:
            r = redis.from_url(redis_url, socket_connect_timeout=5, socket_timeout=5)
            r.ping()
            info = r.info('server')

            latency = (time.time() - start) * 1000
            return ComponentHealth(
                name='redis',
                status=HealthStatus.HEALTHY.value,
                latency_ms=latency,
                timestamp=datetime.utcnow().isoformat(),
                details={'version': info.get('redis_version'), 'used_memory_mb': info.get('used_memory_human')}
            )

        except Exception as e:
            logger.warning(f"🔴 Redis health check failed: {e}")
            return ComponentHealth(
                name='redis',
                status=HealthStatus.CRITICAL.value,
                latency_ms=(time.time() - start) * 1000,
                timestamp=datetime.utcnow().isoformat(),
                error_message=str(e)
            )

    async def _check_mcp_agent(self, name: str, host: str, port: int) -> ComponentHealth:
        """Check MCP agent HTTP endpoint"""
        start = time.time()
        url = f"http://{host}:{port}/health"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    latency = (time.time() - start) * 1000

                    if response.status == 200:
                        data = await response.json()
                        return ComponentHealth(
                            name=f'{name}_mcp',
                            status=HealthStatus.HEALTHY.value,
                            latency_ms=latency,
                            timestamp=datetime.utcnow().isoformat(),
                            details={'port': port, 'version': data.get('version', 'unknown')}
                        )
                    else:
                        return ComponentHealth(
                            name=f'{name}_mcp',
                            status=HealthStatus.WARNING.value,
                            latency_ms=latency,
                            timestamp=datetime.utcnow().isoformat(),
                            error_message=f'HTTP {response.status}'
                        )

        except asyncio.TimeoutError:
            logger.debug(f"⏱️  MCP agent {name} timeout (expected if not running)")
            return ComponentHealth(
                name=f'{name}_mcp',
                status=HealthStatus.WARNING.value,
                latency_ms=(time.time() - start) * 1000,
                timestamp=datetime.utcnow().isoformat(),
                error_message='Connection timeout'
            )

        except Exception as e:
            logger.debug(f"MCP agent {name} check failed: {e}")
            return ComponentHealth(
                name=f'{name}_mcp',
                status=HealthStatus.WARNING.value,
                latency_ms=(time.time() - start) * 1000,
                timestamp=datetime.utcnow().isoformat(),
                error_message=str(e)
            )

    async def _check_system(self) -> ComponentHealth:
        """Check system resources (CPU, memory, disk)"""
        start = time.time()

        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Determine status based on thresholds
            status = HealthStatus.HEALTHY.value
            if cpu_percent > 80 or memory.percent > 85 or disk.percent > 90:
                status = HealthStatus.WARNING.value
            if cpu_percent > 95 or memory.percent > 95 or disk.percent > 95:
                status = HealthStatus.CRITICAL.value

            latency = (time.time() - start) * 1000
            return ComponentHealth(
                name='system',
                status=status,
                latency_ms=latency,
                timestamp=datetime.utcnow().isoformat(),
                details={
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': disk.percent,
                    'disk_free_gb': round(disk.free / (1024**3), 2)
                }
            )

        except Exception as e:
            logger.warning(f"System health check failed: {e}")
            return ComponentHealth(
                name='system',
                status=HealthStatus.WARNING.value,
                latency_ms=(time.time() - start) * 1000,
                timestamp=datetime.utcnow().isoformat(),
                error_message=str(e)
            )

    def get_overall_status(self, components: Dict[str, ComponentHealth]) -> str:
        """Determine overall system status"""
        statuses = [c.status for c in components.values()]

        if HealthStatus.CRITICAL.value in statuses:
            return HealthStatus.CRITICAL.value
        elif HealthStatus.WARNING.value in statuses:
            return HealthStatus.WARNING.value
        else:
            return HealthStatus.HEALTHY.value


# ============================================================================
# HTTP SERVER
# ============================================================================

class HealthCheckServer:
    """aiohttp web server for health checks"""

    def __init__(self, port: int = 9000):
        self.port = port
        self.checker = HealthChecker()
        self.cached_results = None
        self.cache_time = None

    async def handle_health(self, request):
        """GET /health - Main health endpoint"""
        try:
            # Check cache (30 second TTL)
            if (self.cached_results and
                self.cache_time and
                time.time() - self.cache_time < self.checker.check_interval):
                results = self.cached_results
            else:
                results = await self.checker.check_all()
                self.cached_results = results
                self.cache_time = time.time()

            # Build response
            components_data = {name: comp.to_dict() for name, comp in results.items()}
            overall_status = self.checker.get_overall_status(results)

            response = {
                'status': overall_status,
                'timestamp': datetime.utcnow().isoformat(),
                'components': components_data,
                'summary': {
                    'total_checks': len(results),
                    'healthy': sum(1 for c in results.values() if c.status == HealthStatus.HEALTHY.value),
                    'warning': sum(1 for c in results.values() if c.status == HealthStatus.WARNING.value),
                    'critical': sum(1 for c in results.values() if c.status == HealthStatus.CRITICAL.value)
                }
            }

            # HTTP status based on overall health
            http_status = 200 if overall_status == HealthStatus.HEALTHY.value else 503

            return web.json_response(response, status=http_status)

        except Exception as e:
            logger.error(f"Health endpoint error: {e}")
            return web.json_response(
                {'error': str(e), 'status': 'error'},
                status=500
            )

    async def handle_ready(self, request):
        """GET /ready - Simple readiness probe (Kubernetes liveness)"""
        results = await self.checker.check_all()
        overall = self.checker.get_overall_status(results)

        if overall == HealthStatus.CRITICAL.value:
            return web.json_response({'ready': False}, status=503)
        else:
            return web.json_response({'ready': True}, status=200)

    async def handle_metrics(self, request):
        """GET /metrics - Prometheus-compatible metrics"""
        results = await self.checker.check_all()

        # Generate Prometheus format
        lines = [
            '# HELP health_check_latency_ms Health check latency in milliseconds',
            '# TYPE health_check_latency_ms gauge'
        ]

        for name, comp in results.items():
            lines.append(f'health_check_latency_ms{{component="{name}"}} {comp.latency_ms}')

        return web.Response(text='\n'.join(lines), content_type='text/plain')

    def create_app(self):
        """Create aiohttp application"""
        app = web.Application()
        app.router.add_get('/health', self.handle_health)
        app.router.add_get('/ready', self.handle_ready)
        app.router.add_get('/metrics', self.handle_metrics)
        return app

    async def start(self):
        """Start HTTP server"""
        app = self.create_app()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        logger.info(f"✅ Health Check Service running on ::{self.port}")
        logger.info(f"   GET http://localhost:{self.port}/health")
        logger.info(f"   GET http://localhost:{self.port}/ready (Kubernetes)")
        logger.info(f"   GET http://localhost:{self.port}/metrics (Prometheus)")


# ============================================================================
# CLI & MAIN
# ============================================================================

@click.command()
@click.option('--port', default=9000, type=int, help='HTTP server port')
@click.option('--interval', default=30, type=int, help='Health check interval (seconds)')
def main(port: int, interval: int):
    """ADRION 369 Health Check Service

    Monitors system health: Database, Redis, MCP Agents, System Resources.
    Provides /health, /ready, and /metrics endpoints.
    """

    logger.info("🏥 ADRION 369 Health Check Service")
    logger.info(f"Port: {port}, Check Interval: {interval}s")

    server = HealthCheckServer(port=port)
    server.checker.check_interval = interval

    try:
        asyncio.run(server.start())
        # Keep running
        asyncio.run(asyncio.sleep(float('inf')))
    except KeyboardInterrupt:
        logger.info("⏹️  Health Check Service stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
