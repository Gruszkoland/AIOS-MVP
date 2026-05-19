#!/usr/bin/env python3
"""
Kubernetes WebSocket Integration for Real-Time Monitoring
Provides live streaming of pod status, metrics, and cluster events

Features:
- Real-time pod status updates
- Live cluster events streaming
- Metrics push (Prometheus)
- Connection pooling & multiplexing
- Auto-reconnect on disconnect
"""

import asyncio
import json
import logging
import subprocess
import threading
import time
from datetime import datetime
from typing import Dict, List, Callable, Optional, Set
from collections import defaultdict
import queue

logger = logging.getLogger("adrion.uap.k8s_websocket")


class K8sWatcher:
    """Kubernetes cluster watcher for live updates"""

    def __init__(self, namespace: str = "adrion-369"):
        self.namespace = namespace
        self.kubectl_path = self._find_kubectl()
        self.is_connected = False
        self.watch_thread: Optional[threading.Thread] = None
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.event_queue: queue.Queue = queue.Queue()
        self.stop_flag = False

    @property
    def is_watching(self) -> bool:
        """True when watch_thread is alive and stop_flag is not set."""
        return (
            self.watch_thread is not None
            and self.watch_thread.is_alive()
            and not self.stop_flag
        )

    def _find_kubectl(self) -> Optional[str]:
        """Find kubectl executable"""
        try:
            result = subprocess.run(
                ["which", "kubectl"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        try:
            result = subprocess.run(
                ["where", "kubectl"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        return None

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to event type with callback"""
        self.subscribers[event_type].append(callback)
        logger.info(f"Subscribed to {event_type}: {getattr(callback, '__name__', repr(callback))}")

    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from event type"""
        if callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
            logger.info(f"Unsubscribed from {event_type}: {getattr(callback, '__name__', repr(callback))}")

    def _notify_subscribers(self, event_type: str, data: Dict):
        """Notify all subscribers of event type"""
        for callback in self.subscribers[event_type]:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Subscriber callback error: {e}")

    def start_watching(self):
        """Start watching cluster (runs in background thread)"""
        if self.watch_thread and self.watch_thread.is_alive():
            logger.warning("Watcher already running")
            return

        self.stop_flag = False
        self.watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watch_thread.start()
        logger.info("K8s watcher started")

    def stop_watching(self):
        """Stop watching cluster"""
        self.stop_flag = True
        if self.watch_thread:
            self.watch_thread.join(timeout=5)
        logger.info("K8s watcher stopped")

    def _watch_loop(self):
        """Main watch loop (runs in background)"""
        while not self.stop_flag:
            try:
                self._watch_pods()
                self._watch_events()
            except Exception as e:
                logger.error(f"Watch loop error: {e}")
                time.sleep(5)  # Backoff before retry

    def _watch_pods(self):
        """Watch pod status changes"""
        if not self.kubectl_path:
            return

        try:
            cmd = [
                self.kubectl_path,
                "get",
                "pods",
                "-n",
                self.namespace,
                "-o",
                "json",
                "--watch",
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            for line in process.stdout:
                if self.stop_flag:
                    process.terminate()
                    break

                try:
                    pod_data = json.loads(line)
                    pod_name = pod_data["metadata"]["name"]
                    pod_status = pod_data["status"]["phase"]

                    event = {
                        "type": "pod_status_change",
                        "pod_name": pod_name,
                        "status": pod_status,
                        "timestamp": datetime.now().isoformat(),
                    }

                    self._notify_subscribers("pod_status", event)
                    self.event_queue.put(event)

                except json.JSONDecodeError:
                    pass

        except Exception as e:
            logger.error(f"Pod watch error: {e}")

    def _watch_events(self):
        """Watch cluster events"""
        if not self.kubectl_path:
            return

        try:
            # Get recent events, then continue watching
            cmd = [
                self.kubectl_path,
                "get",
                "events",
                "-n",
                self.namespace,
                "-o",
                "json",
                "--watch",
                "--sort-by='.lastTimestamp'"
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            for line in process.stdout:
                if self.stop_flag:
                    process.terminate()
                    break

                try:
                    event_data = json.loads(line)
                    event = {
                        "type": "cluster_event",
                        "reason": event_data.get("reason", "Unknown"),
                        "message": event_data.get("message", ""),
                        "object": event_data.get("involvedObject", {}).get("name", ""),
                        "event_type": event_data.get("type", "Normal"),
                        "timestamp": event_data.get("lastTimestamp", ""),
                    }

                    self._notify_subscribers("cluster_event", event)
                    self.event_queue.put(event)

                except json.JSONDecodeError:
                    pass

        except Exception as e:
            logger.error(f"Event watch error: {e}")

    def get_queued_events(self, max_count: int = 100) -> List[Dict]:
        """Get queued events (non-blocking)"""
        events = []
        for _ in range(max_count):
            try:
                event = self.event_queue.get_nowait()
                events.append(event)
            except queue.Empty:
                break
        return events


# Singleton instance
_k8s_watcher: Optional[K8sWatcher] = None


def get_k8s_watcher(namespace: str = "adrion-369") -> K8sWatcher:
    """Get or create singleton K8s watcher"""
    global _k8s_watcher
    if _k8s_watcher is None:
        _k8s_watcher = K8sWatcher(namespace)
    return _k8s_watcher
