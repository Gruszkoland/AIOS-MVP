#!/usr/bin/env python3
"""
Grafana Dashboard & Configuration Sync Script
Synchronizes dashboards, alerts, and datasources from Git to Grafana instance
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s — %(levelname)s — %(message)s'
)


class GrafanaClient:
    """Grafana API Client"""
    
    def __init__(self, host: str, api_key: str, verify_ssl: bool = True):
        self.host = host.rstrip("/")
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> requests.Response:
        """Make HTTP request to Grafana API"""
        url = f"{self.host}/api/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(
                method,
                url,
                json=data,
                params=params,
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Grafana API error: {method} {url} — {e}")
            raise
    
    def get_dashboards(self, folder_id: Optional[int] = None) -> List[Dict]:
        """List all dashboards (optionally in a folder)"""
        params = {}
        if folder_id is not None:
            params["folderId"] = folder_id
        
        response = self._request("GET", "/search", params=params)
        return response.json()
    
    def get_dashboard(self, dashboard_id: str) -> Dict:
        """Get dashboard by ID"""
        response = self._request("GET", f"/dashboards/uid/{dashboard_id}")
        return response.json()
    
    def create_or_update_dashboard(
        self,
        dashboard: Dict,
        folder_id: int = 0,
        overwrite: bool = True
    ) -> Dict:
        """Create or update dashboard"""
        payload = {
            "dashboard": dashboard,
            "folderId": folder_id,
            "overwrite": overwrite
        }
        
        response = self._request("POST", "/dashboards/db", data=payload)
        return response.json()
    
    def delete_dashboard(self, dashboard_id: str) -> Dict:
        """Delete dashboard by ID"""
        response = self._request("DELETE", f"/dashboards/uid/{dashboard_id}")
        return response.json()
    
    def get_datasources(self) -> List[Dict]:
        """List all datasources"""
        response = self._request("GET", "/datasources")
        return response.json()
    
    def create_or_update_datasource(self, datasource: Dict) -> Dict:
        """Create or update datasource"""
        response = self._request("POST", "/datasources", data=datasource)
        return response.json()
    
    def get_alerts(self) -> List[Dict]:
        """Get alert rules (Prometheus alerting)"""
        response = self._request("GET", "/ruler/rules")
        return response.json()
    
    def create_or_update_alert_rule(self, alert_rule: Dict) -> Dict:
        """Create or update alert rule"""
        response = self._request("POST", "/ruler/rules", data=alert_rule)
        return response.json()
    
    def get_folders(self) -> List[Dict]:
        """List all folders"""
        response = self._request("GET", "/folders")
        return response.json()
    
    def create_folder(self, title: str, uid: Optional[str] = None) -> Dict:
        """Create new folder"""
        payload = {"title": title}
        if uid:
            payload["uid"] = uid
        
        response = self._request("POST", "/folders", data=payload)
        return response.json()


class DashboardSyncer:
    """Synchronize dashboards from filesystem to Grafana"""
    
    def __init__(self, client: GrafanaClient, verbose: bool = False):
        self.client = client
        self.verbose = verbose
    
    def sync_dashboards(
        self,
        dashboards_dir: Path,
        folder_id: int = 0,
        overwrite: bool = True
    ) -> Dict[str, any]:
        """Sync all dashboards from directory"""
        results = {
            "synced": [],
            "skipped": [],
            "failed": []
        }
        
        dashboards_dir = Path(dashboards_dir)
        if not dashboards_dir.exists():
            logger.error(f"Dashboards directory not found: {dashboards_dir}")
            return results
        
        # Find all dashboard JSON files
        dashboard_files = list(dashboards_dir.glob("*.json"))
        logger.info(f"Found {len(dashboard_files)} dashboard files")
        
        for dashboard_file in dashboard_files:
            try:
                with open(dashboard_file) as f:
                    dashboard_data = json.load(f)
                
                # Remove internal IDs to allow creation
                dashboard_data.pop("id", None)
                
                logger.info(f"Syncing dashboard: {dashboard_file.name}...")
                
                result = self.client.create_or_update_dashboard(
                    dashboard_data,
                    folder_id=folder_id,
                    overwrite=overwrite
                )
                
                if "id" in result:
                    results["synced"].append({
                        "name": dashboard_file.name,
                        "dashboard_id": result.get("id"),
                        "status": result.get("status")
                    })
                    logger.info(f"✅ Synced: {dashboard_file.name}")
                else:
                    results["failed"].append({
                        "name": dashboard_file.name,
                        "error": result.get("message", "Unknown error")
                    })
                    logger.error(f"❌ Failed: {dashboard_file.name} — {result}")
            
            except Exception as e:
                results["failed"].append({
                    "name": dashboard_file.name,
                    "error": str(e)
                })
                logger.error(f"❌ Error processing {dashboard_file.name}: {e}")
        
        return results
    
    def sync_datasources(self, datasources_file: Path) -> Dict[str, any]:
        """Sync datasources from JSON file"""
        results = {
            "synced": [],
            "skipped": [],
            "failed": []
        }
        
        if not datasources_file.exists():
            logger.warning(f"Datasources file not found: {datasources_file}")
            return results
        
        try:
            with open(datasources_file) as f:
                datasources_config = json.load(f)
            
            existing = {ds["name"]: ds["id"] for ds in self.client.get_datasources()}
            
            for datasource in datasources_config.get("datasources", []):
                try:
                    name = datasource["name"]
                    
                    if name in existing:
                        logger.info(f"Datasource already exists: {name}")
                        results["skipped"].append({"name": name})
                        continue
                    
                    logger.info(f"Creating datasource: {name}...")
                    result = self.client.create_or_update_datasource(datasource)
                    
                    results["synced"].append({
                        "name": name,
                        "datasource_id": result.get("id")
                    })
                    logger.info(f"✅ Created: {name}")
                
                except Exception as e:
                    results["failed"].append({
                        "name": datasource.get("name", "unknown"),
                        "error": str(e)
                    })
                    logger.error(f"❌ Error: {e}")
        
        except Exception as e:
            logger.error(f"Failed to sync datasources: {e}")
        
        return results


class MetricsExporter:
    """Export metrics about the sync operation"""
    
    @staticmethod
    def generate_report(
        sync_results: Dict,
        datasources_results: Dict,
        duration_seconds: float
    ) -> Dict:
        """Generate sync report"""
        total_dashboards = (
            len(sync_results["synced"]) +
            len(sync_results["failed"]) +
            len(sync_results["skipped"])
        )
        
        total_datasources = (
            len(datasources_results["synced"]) +
            len(datasources_results["failed"]) +
            len(datasources_results["skipped"])
        )
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration_seconds,
            "dashboards": {
                "total": total_dashboards,
                "synced": len(sync_results["synced"]),
                "failed": len(sync_results["failed"]),
                "skipped": len(sync_results["skipped"]),
                "success_rate": len(sync_results["synced"]) / total_dashboards if total_dashboards > 0 else 0
            },
            "datasources": {
                "total": total_datasources,
                "synced": len(datasources_results["synced"]),
                "failed": len(datasources_results["failed"]),
                "skipped": len(datasources_results["skipped"]),
                "success_rate": len(datasources_results["synced"]) / total_datasources if total_datasources > 0 else 0
            },
            "details": {
                "dashboards": sync_results,
                "datasources": datasources_results
            }
        }
        
        return report
    
    @staticmethod
    def print_report(report: Dict):
        """Pretty print sync report"""
        print("\n" + "="*80)
        print("🔄 GRAFANA SYNC REPORT")
        print("="*80)
        print(f"⏱️  Duration: {report['duration_seconds']:.2f}s")
        print(f"📅 Timestamp: {report['timestamp']}")
        
        print("\n📊 DASHBOARDS:")
        print(f"   Total: {report['dashboards']['total']}")
        print(f"   ✅ Synced: {report['dashboards']['synced']}")
        print(f"   ❌ Failed: {report['dashboards']['failed']}")
        print(f"   ⏭️  Skipped: {report['dashboards']['skipped']}")
        print(f"   📈 Success Rate: {report['dashboards']['success_rate']*100:.1f}%")
        
        print("\n🔌 DATASOURCES:")
        print(f"   Total: {report['datasources']['total']}")
        print(f"   ✅ Synced: {report['datasources']['synced']}")
        print(f"   ❌ Failed: {report['datasources']['failed']}")
        print(f"   ⏭️  Skipped: {report['datasources']['skipped']}")
        print(f"   📈 Success Rate: {report['datasources']['success_rate']*100:.1f}%")
        
        if report['details']['dashboards']['failed']:
            print("\n⚠️  FAILED DASHBOARDS:")
            for item in report['details']['dashboards']['failed']:
                print(f"   - {item['name']}: {item['error']}")
        
        if report['details']['datasources']['failed']:
            print("\n⚠️  FAILED DATASOURCES:")
            for item in report['details']['datasources']['failed']:
                print(f"   - {item['name']}: {item['error']}")
        
        print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Sync dashboards and datasources to Grafana"
    )
    
    parser.add_argument(
        "--host",
        required=True,
        help="Grafana host URL (e.g., https://grafana.example.com)"
    )
    
    parser.add_argument(
        "--api-key",
        required=True,
        help="Grafana API key (org admin token)"
    )
    
    parser.add_argument(
        "--dashboards-dir",
        type=Path,
        required=True,
        help="Directory containing dashboard JSON files"
    )
    
    parser.add_argument(
        "--datasources-file",
        type=Path,
        help="Datasources configuration JSON file"
    )
    
    parser.add_argument(
        "--folder-id",
        type=int,
        default=0,
        help="Grafana folder ID for dashboards (default: 0 = General)"
    )
    
    parser.add_argument(
        "--create-folder",
        help="Create folder with this name if it doesn't exist"
    )
    
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Don't overwrite existing dashboards"
    )
    
    parser.add_argument(
        "--no-ssl-verify",
        action="store_true",
        help="Disable SSL certificate verification"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--report-file",
        type=Path,
        help="Save report to JSON file"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        # Initialize Grafana client
        logger.info(f"🔗 Connecting to Grafana: {args.host}")
        client = GrafanaClient(
            host=args.host,
            api_key=args.api_key,
            verify_ssl=not args.no_ssl_verify
        )
        
        # Test connection
        client.get_datasources()
        logger.info("✅ Connected to Grafana")
        
        # Create folder if requested
        if args.create_folder:
            logger.info(f"📁 Creating folder: {args.create_folder}")
            try:
                folder = client.create_folder(args.create_folder)
                args.folder_id = folder.get("id", 0)
                logger.info(f"✅ Folder created with ID: {args.folder_id}")
            except Exception as e:
                logger.warning(f"⚠️  Folder creation failed (may already exist): {e}")
        
        # Initialize syncer
        import time
        start_time = time.time()
        
        syncer = DashboardSyncer(client, verbose=args.verbose)
        
        # Sync dashboards
        logger.info("📊 Syncing dashboards...")
        dashboard_results = syncer.sync_dashboards(
            dashboards_dir=args.dashboards_dir,
            folder_id=args.folder_id,
            overwrite=not args.no_overwrite
        )
        
        # Sync datasources
        datasource_results = {"synced": [], "failed": [], "skipped": []}
        if args.datasources_file:
            logger.info("🔌 Syncing datasources...")
            datasource_results = syncer.sync_datasources(args.datasources_file)
        
        # Generate report
        duration = time.time() - start_time
        report = MetricsExporter.generate_report(
            dashboard_results,
            datasource_results,
            duration
        )
        
        # Print report
        MetricsExporter.print_report(report)
        
        # Save report if requested
        if args.report_file:
            with open(args.report_file, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"📄 Report saved to: {args.report_file}")
        
        # Return exit code based on success
        total_failed = len(dashboard_results["failed"]) + len(datasource_results["failed"])
        if total_failed > 0:
            logger.warning(f"⚠️  {total_failed} items failed to sync")
            return 1
        
        logger.info("✅ Sync completed successfully!")
        return 0
    
    except Exception as e:
        logger.error(f"❌ Sync failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
