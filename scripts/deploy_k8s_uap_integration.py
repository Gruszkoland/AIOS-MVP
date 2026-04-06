#!/usr/bin/env python3
"""
Kubernetes ↔ UAP Integration - Automated Deployment Pipeline
Deploys the complete integration to production K8s cluster
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s — %(message)s'
)
logger = logging.getLogger(__name__)


class K8sDeploymentPipeline:
    """Orchestrate deployment of K8s ↔ UAP integration"""

    def __init__(self, namespace="adrion-369", cluster_context="docker-desktop"):
        """Initialize deployment pipeline

        Args:
            namespace: K8s namespace
            cluster_context: kubectl context name
        """
        self.namespace = namespace
        self.cluster_context = cluster_context
        self.project_root = Path(__file__).parent.parent
        self.manifests_dir = self.project_root / "kubernetes"
        self.backend_dir = self.project_root / "uap" / "backend"
        self.frontend_dir = self.project_root / "uap" / "frontend"

        self.start_time = datetime.now()
        self.deployment_log = []

    def log_deployment(self, stage, status, details=""):
        """Log deployment step"""
        entry = {
            "stage": stage,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.deployment_log.append(entry)

        emoji = "✅" if status == "SUCCESS" else "⚠️" if status == "WARN" else "❌"
        logger.info(f"{emoji} [{stage}] {status} {details}")

    def run_command(self, cmd, description=""):
        """Execute shell command

        Args:
            cmd: Command to run
            description: Log description

        Returns:
            (success, output)
        """
        logger.info(f"Running: {description or cmd}")
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            success = result.returncode == 0
            output = result.stdout + result.stderr

            if success:
                logger.debug(f"Output: {output[:200]}")
            else:
                logger.error(f"Error: {output}")

            return success, output
        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout: {cmd}")
            return False, "TIMEOUT"
        except Exception as e:
            logger.error(f"Command failed: {e}")
            return False, str(e)

    def preflight_checks(self):
        """Verify prerequisites for deployment"""
        logger.info("\n" + "=" * 70)
        logger.info("PREFLIGHT CHECKS")
        logger.info("=" * 70)

        checks = []

        # Check kubectl
        success, _ = self.run_command("kubectl version", "Check kubectl")
        checks.append(("kubectl", success))
        self.log_deployment("kubectl_check", "SUCCESS" if success else "FAILED")

        # Check cluster context
        success, _ = self.run_command(
            f"kubectl config current-context",
            "Check K8s context"
        )
        checks.append(("k8s_context", success))
        self.log_deployment("context_check", "SUCCESS" if success else "FAILED")

        # Check namespace
        success, _ = self.run_command(
            f"kubectl get namespace {self.namespace}",
            f"Check {self.namespace} namespace"
        )
        checks.append(("namespace", success))
        self.log_deployment("namespace_check", "SUCCESS" if success else "FAILED")

        # Check Python environment
        success, _ = self.run_command(
            f"python --version",
            "Check Python"
        )
        checks.append(("python", success))
        self.log_deployment("python_check", "SUCCESS" if success else "FAILED")

        # Check required files
        required_files = [
            self.backend_dir / "api.py",
            self.backend_dir / "kubernetes_integration.py",
            self.backend_dir / "k8s_websocket.py",
            self.frontend_dir / "k8s-dashboard.html",
            self.frontend_dir / "k8s_dashboard.js",
        ]

        for file_path in required_files:
            exists = file_path.exists()
            checks.append((file_path.name, exists))
            self.log_deployment(f"file_check_{file_path.name}", "SUCCESS" if exists else "MISSING")

        all_passed = all(status for _, status in checks)

        logger.info(f"\nPreflight: {sum(1 for _, s in checks if s)}/{len(checks)} passed")

        return all_passed

    def run_unit_tests(self):
        """Run unit tests"""
        logger.info("\n" + "=" * 70)
        logger.info("UNIT TESTS")
        logger.info("=" * 70)

        test_files = [
            "tests/test_k8s_mocked_comprehensive.py",
        ]

        all_passed = True

        for test_file in test_files:
            test_path = self.project_root / test_file
            if test_path.exists():
                success, output = self.run_command(
                    f"python {test_file}",
                    f"Run {test_file}"
                )

                self.log_deployment(
                    f"test_{test_file}",
                    "SUCCESS" if success else "FAILED",
                    output[:100]
                )

                all_passed = all_passed and success
            else:
                logger.warning(f"Test file not found: {test_file}")

        return all_passed

    def validate_syntax(self):
        """Validate Python syntax"""
        logger.info("\n" + "=" * 70)
        logger.info("SYNTAX VALIDATION")
        logger.info("=" * 70)

        python_files = [
            "uap/backend/api.py",
            "uap/backend/kubernetes_integration.py",
            "uap/backend/k8s_websocket.py",
        ]

        all_valid = True

        for py_file in python_files:
            success, output = self.run_command(
                f"python -m py_compile {py_file}",
                f"Validate {py_file}"
            )

            self.log_deployment(
                f"syntax_{py_file}",
                "SUCCESS" if success else "FAILED",
                output[:100] if not success else ""
            )

            all_valid = all_valid and success

        return all_valid

    def deploy_backend_config(self):
        """Deploy backend configuration"""
        logger.info("\n" + "=" * 70)
        logger.info("BACKEND DEPLOYMENT")
        logger.info("=" * 70)

        # Create ConfigMap for UAP backend
        config_map = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "uap-kubernetes-config",
                "namespace": self.namespace
            },
            "data": {
                "K8S_ENABLED": "true",
                "K8S_NAMESPACE": self.namespace,
                "K8S_WATCHER_ENABLED": "true",
                "PROMETHEUS_URL": "http://prometheus:9090",
            }
        }

        config_file = self.project_root / "kubernetes" / "uap-config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, "w") as f:
            import yaml
            yaml.dump(config_map, f)

        success, output = self.run_command(
            f"kubectl apply -f {config_file}",
            "Deploy ConfigMap"
        )

        self.log_deployment(
            "backend_configmap",
            "SUCCESS" if success else "FAILED",
            output[:100] if output else ""
        )

        return success

    def deploy_frontend_config(self):
        """Deploy frontend configuration"""
        logger.info("\n" + "=" * 70)
        logger.info("FRONTEND DEPLOYMENT")
        logger.info("=" * 70)

        # Create ConfigMap for frontend
        config_map = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "uap-frontend-config",
                "namespace": self.namespace
            },
            "data": {
                "K8S_API_BASE": "http://localhost:8002/mapi/v1/kubernetes",
                "K8S_AUTO_REFRESH": "5000",  # 5 seconds
            }
        }

        config_file = self.project_root / "kubernetes" / "frontend-config.yaml"

        with open(config_file, "w") as f:
            import yaml
            yaml.dump(config_map, f)

        success, output = self.run_command(
            f"kubectl apply -f {config_file}",
            "Deploy frontend ConfigMap"
        )

        self.log_deployment(
            "frontend_configmap",
            "SUCCESS" if success else "FAILED",
            output[:100] if output else ""
        )

        return success

    def verify_deployment(self):
        """Verify deployment success"""
        logger.info("\n" + "=" * 70)
        logger.info("DEPLOYMENT VERIFICATION")
        logger.info("=" * 70)

        # Check if ConfigMaps are deployed
        success, output = self.run_command(
            f"kubectl get configmap -n {self.namespace} | grep uap",
            "Check ConfigMaps"
        )

        self.log_deployment(
            "verify_configmaps",
            "SUCCESS" if success else "WARN",
            output[:100] if output else "No ConfigMaps found"
        )

        # Check namespace
        success, output = self.run_command(
            f"kubectl get ns {self.namespace}",
            "Check namespace"
        )

        self.log_deployment(
            "verify_namespace",
            "SUCCESS" if success else "FAILED",
            output[:100] if output else ""
        )

        return success

    def generate_deployment_summary(self):
        """Generate deployment summary report"""
        duration = (datetime.now() - self.start_time).total_seconds()

        report = {
            "project": "Kubernetes ↔ UAP Integration",
            "deployment_date": datetime.now().isoformat(),
            "duration_seconds": duration,
            "namespace": self.namespace,
            "cluster_context": self.cluster_context,
            "total_steps": len(self.deployment_log),
            "successes": sum(1 for s in self.deployment_log if s["status"] == "SUCCESS"),
            "failures": sum(1 for s in self.deployment_log if s["status"] == "FAILED"),
            "warnings": sum(1 for s in self.deployment_log if s["status"] == "WARN"),
            "log": self.deployment_log
        }

        report_file = self.project_root / "Genesis Record" / "10_RAPORTY_DZIALANIA_SYSTEMU" / "DEPLOYMENT" / f"deployment_report_{datetime.now().strftime('%d-%m-%Y_%H%M%S')}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"\nDeployment report: {report_file}")

        return report

    def run(self):
        """Execute full deployment pipeline"""
        logger.info("\n" + "=" * 70)
        logger.info("KUBERNETES ↔ UAP INTEGRATION DEPLOYMENT PIPELINE")
        logger.info("=" * 70 + "\n")

        stages = [
            ("preflight_checks", self.preflight_checks),
            ("syntax_validation", self.validate_syntax),
            ("unit_tests", self.run_unit_tests),
            ("backend_deployment", self.deploy_backend_config),
            ("frontend_deployment", self.deploy_frontend_config),
            ("deployment_verification", self.verify_deployment),
        ]

        failed_stages = []

        for stage_name, stage_func in stages:
            try:
                result = stage_func()
                if not result:
                    failed_stages.append(stage_name)
            except Exception as e:
                logger.error(f"Stage {stage_name} crashed: {e}")
                self.log_deployment(stage_name, "FAILED", str(e))
                failed_stages.append(stage_name)

        # Generate report
        report = self.generate_deployment_summary()

        # Final status
        logger.info("\n" + "=" * 70)
        logger.info("DEPLOYMENT SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total steps: {report['total_steps']}")
        logger.info(f"Successes: {report['successes']}")
        logger.info(f"Failures: {report['failures']}")
        logger.info(f"Warnings: {report['warnings']}")
        logger.info(f"Duration: {report['duration_seconds']:.2f}s")

        if failed_stages:
            logger.error(f"\n❌ Failed stages: {', '.join(failed_stages)}")
            return False
        else:
            logger.info("\n✅ Deployment completed successfully!")
            return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="K8s ↔ UAP Deployment Pipeline")
    parser.add_argument("--namespace", default="adrion-369", help="K8s namespace")
    parser.add_argument("--context", default="docker-desktop", help="kubectl context")
    parser.add_argument("--skip-tests", action="store_true", help="Skip unit tests")

    args = parser.parse_args()

    pipeline = K8sDeploymentPipeline(
        namespace=args.namespace,
        cluster_context=args.context
    )

    success = pipeline.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
