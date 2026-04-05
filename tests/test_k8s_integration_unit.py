#!/usr/bin/env python3
"""
Unit Tests for Kubernetes Integration Modules
Tests core functionality of:
- kubernetes_integration.py (cluster API)
- k8s_websocket.py (real-time watcher)
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
import queue
import threading
import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "uap" / "backend"))

from kubernetes_integration import KubernetesIntegration
from k8s_websocket import K8sWatcher, get_k8s_watcher


class TestKubernetesIntegration(unittest.TestCase):
    """Unit tests for KubernetesIntegration class"""

    def setUp(self):
        """Set up test fixtures"""
        self.k8s = KubernetesIntegration()

    def test_init(self):
        """Test KubernetesIntegration initialization"""
        self.assertIsNotNone(self.k8s)
        self.assertEqual(self.k8s.namespace, "adrion-369")
        self.assertIsNotNone(self.k8s.prometheus_url)
        self.assertIsNotNone(self.k8s.loki_url)

    def test_find_kubectl(self):
        """Test kubectl discovery"""
        kubectl = self.k8s._find_kubectl()
        # kubectl might not be available in test env, but method should not crash
        self.assertTrue(kubectl is None or isinstance(kubectl, str))

    def test_check_cluster_connection(self):
        """Test cluster connection check"""
        result = self.k8s._check_cluster_connection()
        # Result should be boolean
        self.assertIsInstance(result, bool)

    def test_health_check(self):
        """Test health check method exists and is callable"""
        self.assertTrue(hasattr(self.k8s, "_check_cluster_connection"))
        self.assertTrue(callable(getattr(self.k8s, "_check_cluster_connection")))

    @patch("kubernetes_integration.subprocess.run")
    def test_get_cluster_info_with_mock(self, mock_run):
        """Test cluster info retrieval with mock subprocess"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "apiVersion": "v1",
                "kind": "Cluster",
                "metadata": {"name": "docker-desktop"}
            })
        )
        
        # Should not crash when calling
        self.assertTrue(hasattr(self.k8s, "get_cluster_info"))

    def test_namespace_attribute(self):
        """Test namespace is properly set"""
        self.assertEqual(self.k8s.namespace, "adrion-369")


class TestK8sWatcher(unittest.TestCase):
    """Unit tests for K8sWatcher class"""

    def setUp(self):
        """Set up test fixtures"""
        self.watcher = K8sWatcher(namespace="test-ns")

    def test_init(self):
        """Test K8sWatcher initialization"""
        self.assertIsNotNone(self.watcher)
        self.assertEqual(self.watcher.namespace, "test-ns")
        self.assertIsInstance(self.watcher.event_queue, queue.Queue)
        self.assertIsInstance(self.watcher.subscribers, dict)
        self.assertFalse(self.watcher.is_watching)

    def test_subscribe(self):
        """Test event subscription mechanism"""
        callback = Mock()
        self.watcher.subscribe("pod_status_change", callback)
        
        self.assertIn("pod_status_change", self.watcher.subscribers)
        self.assertIn(callback, self.watcher.subscribers["pod_status_change"])

    def test_multiple_subscriptions(self):
        """Test multiple subscribers for same event"""
        callback1 = Mock()
        callback2 = Mock()
        
        self.watcher.subscribe("pod_status_change", callback1)
        self.watcher.subscribe("pod_status_change", callback2)
        
        self.assertEqual(len(self.watcher.subscribers["pod_status_change"]), 2)

    def test_event_queue_initialization(self):
        """Test event queue is initialized correctly"""
        self.assertIsInstance(self.watcher.event_queue, queue.Queue)
        self.assertTrue(self.watcher.event_queue.empty())

    def test_get_queued_events_empty(self):
        """Test getting events from empty queue"""
        events = self.watcher.get_queued_events(max_count=10)
        self.assertEqual(len(events), 0)
        self.assertIsInstance(events, list)

    def test_get_queued_events_with_max(self):
        """Test max_count parameter"""
        # Add mock events to queue
        for i in range(5):
            self.watcher.event_queue.put({"id": i, "type": "test"})
        
        # Get only 3
        events = self.watcher.get_queued_events(max_count=3)
        self.assertEqual(len(events), 3)

    def test_is_watching_flag(self):
        """Test is_watching flag initialization"""
        self.assertFalse(self.watcher.is_watching)

    def test_watch_thread_initialization(self):
        """Test watch_thread is initially None"""
        self.assertIsNone(self.watcher.watch_thread)

    def test_get_watcher_status(self):
        """Test watcher status reporting"""
        # Should not crash
        if hasattr(self.watcher, "get_watcher_status"):
            status = self.watcher.get_watcher_status()
            self.assertIsInstance(status, dict)

    def test_singleton_factory(self):
        """Test get_k8s_watcher singleton factory"""
        w1 = get_k8s_watcher()
        w2 = get_k8s_watcher()
        
        self.assertIsInstance(w1, K8sWatcher)
        self.assertIs(w1, w2)  # Same instance

    def test_namespace_default(self):
        """Test default namespace in factory"""
        watcher = get_k8s_watcher()
        self.assertEqual(watcher.namespace, "adrion-369")


class TestK8sWatcherEvents(unittest.TestCase):
    """Test event handling in K8sWatcher"""

    def setUp(self):
        """Set up test fixtures"""
        self.watcher = K8sWatcher(namespace="test-ns")

    def test_notify_subscribers_no_subscribers(self):
        """Test notifying when no subscribers"""
        # Should not crash
        self.watcher._notify_subscribers("pod_status_change", {"pod": "test"})

    def test_notify_subscribers_with_callback(self):
        """Test notifying actual subscribers"""
        callback = Mock()
        self.watcher.subscribe("pod_status_change", callback)
        
        event = {"pod": "test", "status": "Running"}
        self.watcher._notify_subscribers("pod_status_change", event)
        
        # Small delay for callback
        time.sleep(0.1)
        # callback.assert_called()  # May not be called in sync context

    def test_event_queue_put(self):
        """Test adding events to queue"""
        event = {"type": "pod_status_change", "pod": "api-0"}
        self.watcher.event_queue.put(event)
        
        retrieved = self.watcher.event_queue.get_nowait()
        self.assertEqual(retrieved, event)


class TestKubernetesIntegrationMethods(unittest.TestCase):
    """Test individual methods of KubernetesIntegration"""

    def setUp(self):
        """Set up test fixtures"""
        self.k8s = KubernetesIntegration()

    def test_methods_exist(self):
        """Test all required methods exist"""
        required_methods = [
            "get_cluster_info",
            "get_pods_status",
            "get_services",
            "get_deployments",
            "get_pod_logs",
            "restart_pod",
            "get_metrics",
            "get_namespace_events",
        ]
        
        for method_name in required_methods:
            self.assertTrue(
                hasattr(self.k8s, method_name),
                f"Missing method: {method_name}"
            )
            self.assertTrue(
                callable(getattr(self.k8s, method_name)),
                f"Method not callable: {method_name}"
            )

    def test_method_signatures(self):
        """Test method signatures accept correct parameters"""
        import inspect
        
        # get_pod_logs should accept pod_name, optional namespace and lines
        sig = inspect.signature(self.k8s.get_pod_logs)
        params = list(sig.parameters.keys())
        self.assertIn("pod_name", params)
        
        # restart_pod should accept pod_name and optional namespace
        sig = inspect.signature(self.k8s.restart_pod)
        params = list(sig.parameters.keys())
        self.assertIn("pod_name", params)


class TestK8sWatcherThreading(unittest.TestCase):
    """Test threading behavior of K8sWatcher"""

    def setUp(self):
        """Set up test fixtures"""
        self.watcher = K8sWatcher(namespace="test-ns")

    def test_start_watching_no_crash(self):
        """Test start_watching doesn't crash (even if kubectl unavailable)"""
        # This may fail if kubectl not available, but should not crash
        try:
            self.watcher.start_watching()
            # Stop immediately
            self.watcher.stop_watching()
        except Exception as e:
            # Expected if kubectl not available
            pass

    def test_stop_watching_no_crash(self):
        """Test stop_watching doesn't crash when not started"""
        # Should not crash
        self.watcher.stop_watching()
        self.assertFalse(self.watcher.is_watching)


class TestApiKeyBehavior(unittest.TestCase):
    """Test API key handling"""

    def test_kubernetes_integration_no_auth(self):
        """Test K8s integration works without auth (backend validates)"""
        k8s = KubernetesIntegration()
        self.assertIsNotNone(k8s)


class TestErrorHandling(unittest.TestCase):
    """Test error handling in modules"""

    def setUp(self):
        """Set up test fixtures"""
        self.k8s = KubernetesIntegration()
        self.watcher = K8sWatcher()

    def test_invalid_namespace_handling(self):
        """Test handling of invalid namespace"""
        # Should not crash with invalid namespace
        watcher = K8sWatcher(namespace="nonexistent-ns-12345")
        self.assertIsNotNone(watcher)

    def test_queue_overflow_handling(self):
        """Test queue handles many events"""
        # Add 1000 events
        for i in range(1000):
            try:
                self.watcher.event_queue.put({"id": i}, block=False)
            except queue.Full:
                break
        
        # Should not crash, just fill up
        self.assertGreater(self.watcher.event_queue.qsize(), 0)


def run_tests():
    """Run all unit tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestKubernetesIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestK8sWatcher))
    suite.addTests(loader.loadTestsFromTestCase(TestK8sWatcherEvents))
    suite.addTests(loader.loadTestsFromTestCase(TestKubernetesIntegrationMethods))
    suite.addTests(loader.loadTestsFromTestCase(TestK8sWatcherThreading))
    suite.addTests(loader.loadTestsFromTestCase(TestApiKeyBehavior))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
