"""
Phase 5B Deployment Monitoring
Real-time SLO monitoring during canary and progressive rollout
"""

import requests
import time
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any, List
import statistics

class DeploymentMonitor:
    """Monitors Phase 5B deployment metrics"""
    
    def __init__(self, endpoint: str, alert_threshold: float = 0.5):
        self.endpoint = endpoint
        self.alert_threshold = alert_threshold
        self.metrics_history: List[Dict[str, Any]] = []
    
    def fetch_metrics(self) -> Dict[str, Any]:
        """Fetch current metrics from endpoint"""
        try:
            # Fetch Prometheus metrics
            response = requests.get(f"{self.endpoint}/metrics", timeout=5)
            
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}"}
            
            # Parse metrics text format
            metrics = self._parse_prometheus_metrics(response.text)
            metrics["timestamp"] = datetime.utcnow().isoformat()
            
            return metrics
        
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def _parse_prometheus_metrics(self, text: str) -> Dict[str, Any]:
        """Parse Prometheus text format metrics"""
        metrics = {}
        
        for line in text.split('\n'):
            if line.startswith('#') or not line:
                continue
            
            parts = line.split(' ')
            if len(parts) >= 2:
                metric_name = parts[0]
                metric_value = parts[1]
                
                try:
                    metrics[metric_name] = float(metric_value)
                except ValueError:
                    pass
        
        return metrics
    
    def check_slos(self, metrics: Dict[str, Any]) -> Dict[str, bool]:
        """Check if metrics meet SLO thresholds"""
        slo_status = {}
        
        # Error rate SLO: < 0.1%
        error_rate = metrics.get("g4_errors_total", 0)
        slo_status["error_rate"] = error_rate < 0.001
        
        # P95 latency SLO: < 2s
        p95_latency = metrics.get("g4_latency_p95", 0)
        slo_status["p95_latency"] = p95_latency < 2000
        
        # Cache hit rate SLO: > 60%
        cache_hit_rate = metrics.get("g4_cache_hit_rate", 0)
        slo_status["cache_hit_rate"] = cache_hit_rate > 0.60
        
        # Circuit breaker SLO: CLOSED state
        cb_state = metrics.get("g4_circuit_breaker_state", "UNKNOWN")
        slo_status["circuit_breaker"] = cb_state == "CLOSED"
        
        return slo_status
    
    def alert_if_needed(self, slo_status: Dict[str, bool], metrics: Dict[str, Any]) -> None:
        """Alert if SLOs are breached"""
        
        failures = [k for k, v in slo_status.items() if not v]
        
        if failures:
            alert_msg = f"🚨 SLO BREACH: {', '.join(failures)}\n"
            alert_msg += f"   Error Rate: {metrics.get('g4_errors_total', 0):.4f}\n"
            alert_msg += f"   P95 Latency: {metrics.get('g4_latency_p95', 0):.0f}ms\n"
            alert_msg += f"   Cache Hit: {metrics.get('g4_cache_hit_rate', 0):.1%}\n"
            
            print(alert_msg, file=sys.stderr)
            
            if len(failures) >= 2:
                print("⚠️  Multiple SLO failures - consider rollback", file=sys.stderr)
    
    def monitor_duration(self, duration_seconds: int) -> None:
        """Monitor for specified duration"""
        
        start_time = time.time()
        interval = 5  # Check every 5 seconds
        
        print(f"Starting monitoring for {duration_seconds} seconds...")
        print(f"{'Timestamp':<25} {'Error%':<10} {'P95ms':<10} {'Cache%':<10} {'CB':<10} {'Status':<10}")
        print("-" * 85)
        
        while time.time() - start_time < duration_seconds:
            metrics = self.fetch_metrics()
            
            if "error" in metrics:
                print(f"❌ Fetch failed: {metrics['error']}")
                time.sleep(interval)
                continue
            
            # Store for analysis
            self.metrics_history.append(metrics)
            
            # Check SLOs
            slo_status = self.check_slos(metrics)
            
            # Alert if needed
            self.alert_if_needed(slo_status, metrics)
            
            # Display current state
            error_pct = metrics.get("g4_errors_total", 0) * 100
            p95_ms = metrics.get("g4_latency_p95", 0)
            cache_pct = metrics.get("g4_cache_hit_rate", 0) * 100
            cb_state = metrics.get("g4_circuit_breaker_state", "UNKNOWN")
            
            # All passing?
            all_pass = all(slo_status.values())
            status = "✓ PASS" if all_pass else "✗ FAIL"
            
            print(f"{datetime.utcnow().isoformat():<25} "
                  f"{error_pct:<10.3f} "
                  f"{p95_ms:<10.0f} "
                  f"{cache_pct:<10.1f} "
                  f"{cb_state:<10} "
                  f"{status:<10}")
            
            elapsed = time.time() - start_time
            remaining = duration_seconds - elapsed
            
            # Show progress
            if int(elapsed) % 30 == 0:
                print(f"[Progress: {int(elapsed)}s / {duration_seconds}s | "
                      f"Remaining: {int(remaining)}s]")
            
            time.sleep(interval)
        
        print("-" * 85)
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print monitoring summary"""
        
        if not self.metrics_history:
            print("No metrics collected")
            return
        
        print(f"\n{'MONITORING SUMMARY':<80}")
        print("=" * 80)
        
        # Calculate statistics
        error_rates = [m.get("g4_errors_total", 0) for m in self.metrics_history]
        latencies = [m.get("g4_latency_p95", 0) for m in self.metrics_history]
        cache_rates = [m.get("g4_cache_hit_rate", 0) for m in self.metrics_history]
        
        if error_rates:
            print(f"Error Rate:")
            print(f"  - Mean:   {statistics.mean(error_rates):.4f}")
            print(f"  - Median: {statistics.median(error_rates):.4f}")
            print(f"  - Max:    {max(error_rates):.4f}")
        
        if latencies:
            print(f"P95 Latency (ms):")
            print(f"  - Mean:   {statistics.mean(latencies):.0f}ms")
            print(f"  - Median: {statistics.median(latencies):.0f}ms")
            print(f"  - Max:    {max(latencies):.0f}ms")
        
        if cache_rates:
            print(f"Cache Hit Rate:")
            print(f"  - Mean:   {statistics.mean(cache_rates):.1%}")
            print(f"  - Median: {statistics.median(cache_rates):.1%}")
            print(f"  - Min:    {min(cache_rates):.1%}")
        
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Phase 5B Deployment Monitor")
    parser.add_argument("--endpoint", default="http://localhost:8000", help="API endpoint")
    parser.add_argument("--duration", type=int, default=300, help="Monitor duration (seconds)")
    parser.add_argument("--alert-threshold", type=float, default=0.5, help="Alert threshold")
    parser.add_argument("--output", help="Output file for metrics")
    
    args = parser.parse_args()
    
    monitor = DeploymentMonitor(args.endpoint, args.alert_threshold)
    
    try:
        monitor.monitor_duration(args.duration)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(monitor.metrics_history, f, indent=2)
            print(f"Metrics saved to {args.output}")
    
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
        monitor.print_summary()


if __name__ == "__main__":
    main()
