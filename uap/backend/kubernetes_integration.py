#!/usr/bin/env python3
"""
Kubernetes Integration Module for UAP (Unified Admin Panel)
Provides cluster monitoring, pod management, and service discovery

Features:
- Real-time cluster status
- Pod lifecycle management
- Service discovery and health checks
- Metrics aggregation from Prometheus
- Event streaming for dashboard updates
"""

import json
import logging
import subprocess
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests

logger = logging.getLogger("adrion.uap.kubernetes")

class KubernetesIntegration:
    """Kubernetes cluster integration for UAP"""

    def __init__(self):
        self.namespace = "adrion-369"
        self.kubectl_path = self._find_kubectl()
        self.prometheus_url = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
        self.loki_url = os.getenv("LOKI_URL", "http://localhost:3100")
        self.connected = self._check_cluster_connection()

    def _find_kubectl(self) -> Optional[str]:
        """Find kubectl executable"""
        try:
            result = subprocess.run(["which", "kubectl"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        # Try Windows path
        try:
            result = subprocess.run(["where", "kubectl"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        return None

    def _check_cluster_connection(self) -> bool:
        """Check if Kubernetes cluster is accessible"""
        if not self.kubectl_path:
            logger.warning("kubectl not found - Kubernetes integration disabled")
            return False

        try:
            result = subprocess.run(
                [self.kubectl_path, "cluster-info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Cluster connection check failed: {e}")
            return False

    def get_cluster_info(self) -> Dict[str, Any]:
        """Get cluster information and health status"""
        if not self.connected:
            return {"status": "disconnected", "error": "kubectl not available"}

        try:
            # Get cluster info
            result = subprocess.run(
                [self.kubectl_path, "cluster-info"],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Get node info
            nodes_result = subprocess.run(
                [self.kubectl_path, "get", "nodes", "-o", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )

            nodes = json.loads(nodes_result.stdout) if nodes_result.returncode == 0 else {}

            return {
                "status": "connected",
                "cluster_info": result.stdout[:200],
                "nodes": len(nodes.get("items", [])),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get cluster info: {e}")
            return {"status": "error", "error": str(e)}

    def get_pods_status(self) -> Dict[str, Any]:
        """Get pod status in ADRION namespace"""
        if not self.connected:
            return {"status": "disconnected"}

        try:
            result = subprocess.run(
                [self.kubectl_path, "get", "pods", "-n", self.namespace, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode != 0:
                return {"status": "error", "error": result.stderr}

            pods_data = json.loads(result.stdout)
            pods = pods_data.get("items", [])

            pod_summary = {
                "total": len(pods),
                "running": 0,
                "pending": 0,
                "failed": 0,
                "pods": []
            }

            for pod in pods:
                metadata = pod["metadata"]
                status = pod["status"]["phase"]

                if status == "Running":
                    pod_summary["running"] += 1
                elif status == "Pending":
                    pod_summary["pending"] += 1
                else:
                    pod_summary["failed"] += 1

                pod_summary["pods"].append({
                    "name": metadata["name"],
                    "status": status,
                    "ip": pod["status"].get("podIP", "N/A"),
                    "created": metadata.get("creationTimestamp"),
                    "ready": any(c.get("ready", False) for c in pod["status"].get("containerStatuses", []))
                })

            return {
                "status": "success",
                "namespace": self.namespace,
                "summary": pod_summary,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get pods status: {e}")
            return {"status": "error", "error": str(e)}

    def get_services(self) -> Dict[str, Any]:
        """Get services in ADRION namespace"""
        if not self.connected:
            return {"status": "disconnected"}

        try:
            result = subprocess.run(
                [self.kubectl_path, "get", "svc", "-n", self.namespace, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode != 0:
                return {"status": "error", "error": result.stderr}

            services_data = json.loads(result.stdout)
            services = services_data.get("items", [])

            service_list = []
            for svc in services:
                metadata = svc["metadata"]
                spec = svc["spec"]

                service_list.append({
                    "name": metadata["name"],
                    "type": spec.get("type", "ClusterIP"),
                    "cluster_ip": spec.get("clusterIP", "N/A"),
                    "external_ip": spec.get("loadBalancerIP", "N/A"),
                    "ports": [f"{p['port']}:{p['targetPort']}" for p in spec.get("ports", [])],
                    "selector": spec.get("selector", {}),
                    "created": metadata.get("creationTimestamp")
                })

            return {
                "status": "success",
                "namespace": self.namespace,
                "services": service_list,
                "count": len(service_list),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get services: {e}")
            return {"status": "error", "error": str(e)}

    def get_deployments(self) -> Dict[str, Any]:
        """Get deployments in ADRION namespace"""
        if not self.connected:
            return {"status": "disconnected"}

        try:
            result = subprocess.run(
                [self.kubectl_path, "get", "deployments", "-n", self.namespace, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode != 0:
                return {"status": "error", "error": result.stderr}

            deployments_data = json.loads(result.stdout)
            deployments = deployments_data.get("items", [])

            deployment_list = []
            for dep in deployments:
                metadata = dep["metadata"]
                spec = dep["spec"]
                status = dep["status"]

                deployment_list.append({
                    "name": metadata["name"],
                    "replicas": spec.get("replicas", 0),
                    "ready": status.get("readyReplicas", 0),
                    "updated": status.get("updatedReplicas", 0),
                    "available": status.get("availableReplicas", 0),
                    "image": spec["template"]["spec"]["containers"][0].get("image", "N/A") if spec.get("template", {}).get("spec", {}).get("containers") else "N/A",
                    "created": metadata.get("creationTimestamp")
                })

            return {
                "status": "success",
                "namespace": self.namespace,
                "deployments": deployment_list,
                "count": len(deployment_list),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get deployments: {e}")
            return {"status": "error", "error": str(e)}

    def get_pod_logs(self, pod_name: str, namespace: str = None, lines: int = 50) -> Dict[str, Any]:
        """Get logs from a specific pod"""
        if not self.connected:
            return {"status": "disconnected"}

        ns = namespace or self.namespace

        try:
            result = subprocess.run(
                [self.kubectl_path, "logs", "-n", ns, pod_name, f"--tail={lines}"],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode != 0:
                return {"status": "error", "error": result.stderr}

            return {
                "status": "success",
                "pod": pod_name,
                "namespace": ns,
                "logs": result.stdout,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get pod logs: {e}")
            return {"status": "error", "error": str(e)}

    def restart_pod(self, pod_name: str, namespace: str = None) -> Dict[str, Any]:
        """Restart a pod (delete to trigger restart)"""
        if not self.connected:
            return {"status": "disconnected"}

        ns = namespace or self.namespace

        try:
            result = subprocess.run(
                [self.kubectl_path, "delete", "pod", "-n", ns, pod_name],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode != 0:
                return {"status": "error", "error": result.stderr}

            return {
                "status": "restarting",
                "pod": pod_name,
                "namespace": ns,
                "message": f"Pod {pod_name} is restarting",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to restart pod: {e}")
            return {"status": "error", "error": str(e)}

    def get_metrics(self, metric: str = "cluster_health") -> Dict[str, Any]:
        """Get metrics from Prometheus"""
        if not self.prometheus_url:
            return {"status": "unavailable"}

        try:
            # Basic health check query
            queries = {
                "cluster_health": "up",
                "pod_count": "count(kube_pod_info{namespace='adrion-369'})",
                "cpu_usage": "sum(rate(container_cpu_usage_seconds_total{namespace='adrion-369'}[5m]))",
                "memory_usage": "sum(container_memory_usage_bytes{namespace='adrion-369'}) / 1024 / 1024"
            }

            query = queries.get(metric, "up")
            url = f"{self.prometheus_url}/api/v1/query?query={query}"

            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return {
                    "status": "success",
                    "metric": metric,
                    "data": response.json(),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"status": "error", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {"status": "error", "error": str(e)}

    def get_namespace_events(self) -> Dict[str, Any]:
        """Get recent events in ADRION namespace"""
        if not self.connected:
            return {"status": "disconnected"}

        try:
            result = subprocess.run(
                [self.kubectl_path, "get", "events", "-n", self.namespace, "-o", "json", "--sort-by='.lastTimestamp'"],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode != 0:
                return {"status": "error", "error": result.stderr}

            events_data = json.loads(result.stdout)
            events = events_data.get("items", [])[-10:]  # Last 10 events

            event_list = []
            for event in events:
                event_list.append({
                    "type": event["type"],
                    "reason": event["reason"],
                    "message": event["message"],
                    "object": event["involvedObject"]["name"],
                    "timestamp": event.get("lastTimestamp")
                })

            return {
                "status": "success",
                "namespace": self.namespace,
                "events": event_list,
                "count": len(event_list),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get namespace events: {e}")
            return {"status": "error", "error": str(e)}

# Create singleton instance
k8s_integration = KubernetesIntegration()
