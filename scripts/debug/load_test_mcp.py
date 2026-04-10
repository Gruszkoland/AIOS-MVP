#!/usr/bin/env python3
"""
Load Testing: MCP Agent Swarm Performance
Tests concurrent request handling across 6 agents
"""

import asyncio
import time
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import os

BASE_URLS = {
    'Router': 'http://localhost:9001',
    'Guardian': 'http://localhost:9002',
    'Healer': 'http://localhost:9003',
    'Genesis': 'http://localhost:9004',
    'Oracle': 'http://localhost:9005',
    'Vortex': 'http://localhost:9006'
}

class LoadTester:
    def __init__(self):
        self.results = {agent: [] for agent in BASE_URLS}
        self.errors = {agent: [] for agent in BASE_URLS}
        self.start_time = None
        self.end_time = None

    def test_health_endpoint(self, agent_name, url):
        """Test single health endpoint"""
        try:
            start = time.time()
            response = requests.get(f"{url}/health", timeout=5)
            elapsed = time.time() - start

            if response.status_code == 200:
                return {
                    'agent': agent_name,
                    'status': 'success',
                    'elapsed_ms': elapsed * 1000,
                    'response_size': len(response.text)
                }
            else:
                return {
                    'agent': agent_name,
                    'status': 'error',
                    'code': response.status_code,
                    'elapsed_ms': elapsed * 1000
                }
        except Exception as e:
            return {
                'agent': agent_name,
                'status': 'exception',
                'error': str(e)
            }

    def run_concurrent_load(self, requests_per_agent=10, workers=12):
        """Run concurrent requests across all agents"""
        print(f"\n[LOAD TEST] Starting: {requests_per_agent} requests/agent, {workers} workers")
        print("=" * 70)

        self.start_time = time.time()

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []

            # Submit all requests
            for agent_name, url in BASE_URLS.items():
                for i in range(requests_per_agent):
                    future = executor.submit(self.test_health_endpoint, agent_name, url)
                    futures.append(future)

            # Collect results
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                agent = result['agent']

                if result['status'] == 'success':
                    self.results[agent].append(result)
                else:
                    self.errors[agent].append(result)

                completed += 1
                if completed % 20 == 0:
                    print(f"  [{completed}/{len(futures)}] requests completed...")

        self.end_time = time.time()

    def print_results(self):
        """Print detailed results"""
        print("\n[RESULTS] Performance Summary")
        print("=" * 70)

        total_requests = sum(len(self.results[a]) + len(self.errors[a]) for a in BASE_URLS)
        total_success = sum(len(self.results[a]) for a in BASE_URLS)
        total_errors = sum(len(self.errors[a]) for a in BASE_URLS)

        print(f"Total Requests: {total_requests}")
        print(f"Successful: {total_success} ({100*total_success/max(total_requests,1):.1f}%)")
        print(f"Failed: {total_errors} ({100*total_errors/max(total_requests,1):.1f}%)")
        print(f"Duration: {self.end_time - self.start_time:.2f}s")
        print(f"RPS: {total_success / (self.end_time - self.start_time):.1f}")

        print("\n[AGENT METRICS]")
        print("-" * 70)
        print(f"{'Agent':<15} {'Success':<10} {'Avg(ms)':<12} {'Min(ms)':<10} {'Max(ms)':<10}")
        print("-" * 70)

        for agent_name in BASE_URLS:
            results = self.results[agent_name]
            errors = self.errors[agent_name]

            if results:
                latencies = [r['elapsed_ms'] for r in results]
                avg_lat = sum(latencies) / len(latencies)
                min_lat = min(latencies)
                max_lat = max(latencies)
                success_rate = len(results) / (len(results) + len(errors))

                print(f"{agent_name:<15} {success_rate*100:>7.1f}%  {avg_lat:>10.2f}  {min_lat:>8.2f}  {max_lat:>8.2f}")
            else:
                print(f"{agent_name:<15} {'0.0%':>7} {'N/A':>10} {'N/A':>8} {'N/A':>8}")

        # Process resource check
        print("\n[SYSTEM RESOURCES]")
        print("-" * 70)

        try:
            python_procs = [p for p in psutil.process_iter(['pid', 'name', 'memory_info'])
                          if 'python' in p.info['name'].lower()]

            total_mem = sum(p.info['memory_info'].rss for p in python_procs) / (1024*1024)
            print(f"Python Processes: {len(python_procs)}")
            print(f"Total Memory: {total_mem:.1f} MB")
            print(f"Memory per Agent: {total_mem/len(python_procs):.1f} MB")

            if total_mem > 100:
                print("⚠️  WARNING: Memory usage above 100MB threshold")
            else:
                print("✅ Memory usage within acceptable range")
        except Exception as e:
            print(f"Could not get resource info: {e}")

        # Detailed errors
        if total_errors > 0:
            print("\n[ERRORS]")
            print("-" * 70)
            for agent_name in BASE_URLS:
                if self.errors[agent_name]:
                    print(f"{agent_name}: {len(self.errors[agent_name])} errors")
                    for err in self.errors[agent_name][:3]:  # Show first 3
                        print(f"  - {err}")

if __name__ == "__main__":
    tester = LoadTester()

    # Phase 1: Light load (10 requests per agent)
    print("\n[PHASE 1] Light Load Test")
    tester.run_concurrent_load(requests_per_agent=10, workers=12)
    tester.print_results()

    # Phase 2: Medium load (30 requests per agent)
    print("\n\n[PHASE 2] Medium Load Test")
    tester2 = LoadTester()
    tester2.run_concurrent_load(requests_per_agent=30, workers=24)
    tester2.print_results()

    # Phase 3: High load (50 requests per agent)
    print("\n\n[PHASE 3] High Load Test")
    tester3 = LoadTester()
    tester3.run_concurrent_load(requests_per_agent=50, workers=36)
    tester3.print_results()

    print("\n[CONCLUSION] All load tests completed ✅")
