#!/usr/bin/env python3
"""
ADRION 369 Kubernetes Deployment Script for Windows
Deploys all 12 microservices to Kubernetes cluster
"""

import subprocess
import sys
import time
from pathlib import Path

NAMESPACE = "adrion-369"
MANIFESTS = [
    "kubernetes/04-tier1/tier1-deployments.yaml",
    "kubernetes/05-core/core-deployments.yaml",
    "kubernetes/06-monitoring/monitoring-deployments.yaml",
    "kubernetes/07-networking/ingress-networking.yaml",
    "kubernetes/08-jobs/backup-jobs.yaml",
]

def log_info(msg):
    print(f"[INFO] {msg}")

def log_ok(msg):
    print(f"[OK] {msg}")

def log_err(msg):
    print(f"[ERROR] {msg}")

def run_kubectl(args):
    """Run kubectl command and return result"""
    try:
        result = subprocess.run(
            ["kubectl"] + args,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result
    except TimeoutExpired:
        log_err(f"kubectl timeout: {' '.join(args)}")
        return None
    except Exception as e:
        log_err(f"Exception running kubectl: {e}")
        return None

def main():
    log_info("ADRION 369 v4.0 - Kubernetes Deployment")
    log_info("=" * 60)
    
    # Check kubectl
    result = run_kubectl(["version", "--short"])
    if not result or result.returncode != 0:
        log_err("kubectl not available")
        return False
    log_ok("kubectl ready")
    
    # Deploy each manifest
    for manifest in MANIFESTS:
        manifest_path = Path(manifest)
        if not manifest_path.exists():
            log_err(f"Manifest not found: {manifest}")
            continue
        
        log_info(f"Deploying: {manifest}")
        result = run_kubectl(["apply", "-f", manifest])
        
        if result and result.returncode == 0:
            log_ok(f"Deployed: {manifest}")
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if any(kw in line for kw in ['created', 'configured', 'unchanged']):
                        print(f"  -> {line.strip()}")
        else:
            log_err(f"Failed to deploy {manifest}")
            if result and result.stderr:
                print(f"  stderr: {result.stderr[:200]}")
        
        time.sleep(2)
    
    # Status check
    log_info("Fetching deployment status...")
    result = run_kubectl(["get", "all", "-n", NAMESPACE])
    if result and result.returncode == 0:
        print("\nResources in namespace adrion-369:")
        print(result.stdout)
    else:
        log_err("Failed to get resources")
    
    log_info("=" * 60)
    log_ok("Deployment sequence complete!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
