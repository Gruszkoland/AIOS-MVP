#!/usr/bin/env python3
"""
ADR & ATAM Status Tracker — Auto-update monitoring JSON files
Runs via CI/CD pipeline to keep adoption metrics current
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON with error handling."""
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        print(f"⚠️  File not found: {path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {path}: {e}")
        return {}


def save_json(path: Path, data: Dict[str, Any]) -> None:
    """Save JSON with formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding='utf-8')
    print(f"✅ Saved: {path}")


def scan_adr_files(adr_dir: Path) -> Dict[str, Dict[str, Any]]:
    """Parse all ADR files and extract metadata."""
    adr_files = sorted(adr_dir.glob("ADR-*.md"))
    adr_data = {}
    
    for adr_file in adr_files:
        content = adr_file.read_text(encoding='utf-8')
        
        # Extract ADR ID from filename
        adr_id = adr_file.stem  # e.g., "ADR-001"
        
        # Parse status
        if "- [x] Accepted" in content:
            status = "accepted"
        elif "- [ ] Proposed" in content:
            status = "proposed"
        elif "- [x] Deprecated" in content:
            status = "deprecated"
        else:
            status = "unknown"
        
        adr_data[adr_id] = {
            "status": status,
            "file": str(adr_file)
        }
    
    return adr_data


def update_adr_adoption_status(adr_dir: Path, tracker_path: Path) -> None:
    """Update ADR-Adoption-Status.json."""
    print(f"📝 Updating ADR Adoption Status...")
    
    adr_data = scan_adr_files(adr_dir)
    
    # Load existing tracker
    tracker = load_json(tracker_path)
    if not tracker:
        print("⚠️  Creating new ADR Adoption Status tracker")
        tracker = {
            "reported_at": datetime.utcnow().isoformat() + "Z",
            "adr_summary": {
                "total_adrs": 0,
                "accepted": 0,
                "proposed": 0
            }
        }
    
    # Calculate counts
    accepted = sum(1 for data in adr_data.values() if data["status"] == "accepted")
    proposed = sum(1 for data in adr_data.values() if data["status"] == "proposed")
    total = len(adr_data)
    
    # Update metrics
    tracker["reported_at"] = datetime.utcnow().isoformat() + "Z"
    tracker["adr_summary"] = {
        "total_adrs": total,
        "accepted": accepted,
        "proposed": proposed,
        "deprecated": sum(1 for data in adr_data.values() if data["status"] == "deprecated"),
        "coverage_percentage": int(accepted * 100 / total) if total > 0 else 0
    }
    
    # Save
    save_json(tracker_path, tracker)
    print(f"  Total: {total} | Accepted: {accepted} | Proposed: {proposed}")


def update_atam_progress(atam_file: Path, tracker_path: Path) -> None:
    """Update ATAM-Progress.json based on documentation."""
    print(f"📝 Updating ATAM Progress...")
    
    tracker = load_json(tracker_path)
    if not tracker:
        tracker = {"reported_at": datetime.utcnow().isoformat() + "Z"}
    
    # Update timestamp
    tracker["reported_at"] = datetime.utcnow().isoformat() + "Z"
    
    # Check if ATAM findings exist
    if atam_file.exists():
        tracker["atam_status"] = "documentation_found"
    else:
        tracker["atam_status"] = "awaiting_documentation"
    
    save_json(tracker_path, tracker)


def update_tools_integration(tracking_file: Path) -> None:
    """Update Tools-Integration-Status.json."""
    print(f"📝 Updating Tools Integration Status...")
    
    tracker = load_json(tracking_file)
    if not tracker:
        return  # Skip if file doesn't exist (will be created manually)
    
    # Just update timestamp
    tracker["reported_at"] = datetime.utcnow().isoformat() + "Z"
    
    save_json(tracking_file, tracker)


def main():
    """Main entry point."""
    base_dir = Path(__file__).parent.parent.parent  # Project root
    
    # Paths
    adr_dir = base_dir / "docs" / "adr"
    atam_dir = base_dir / "docs" / "ARCHITECTURE"
    atam_file = atam_dir / "ATAM-Findings-2026.md"
    monitoring_dir = base_dir / "Genesis Record" / "10_RAPORTY_DZIALANIA_SYSTEMU" / "MONITORING"
    
    adr_status_file = monitoring_dir / "ADR-Adoption-Status.json"
    atam_progress_file = monitoring_dir / "ATAM-Progress.json"
    tools_integration_file = monitoring_dir / "Tools-Integration-Status.json"
    
    print("🔧 ADRION 369 Monitoring Status Updater")
    print("=" * 50)
    
    try:
        # Update trackers
        if adr_dir.exists():
            update_adr_adoption_status(adr_dir, adr_status_file)
        
        if atam_dir.exists():
            update_atam_progress(atam_file, atam_progress_file)
        
        if tools_integration_file.exists():
            update_tools_integration(tools_integration_file)
        
        print("\n✅ All monitoring trackers updated successfully")
        return 0
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
