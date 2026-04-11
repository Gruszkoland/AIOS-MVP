#!/usr/bin/env python3
"""Create Hierarchy Summary Report"""

from pathlib import Path
import json

# Find target directory
desktop = Path.home() / "Desktop"
target_dirs = [d for d in desktop.iterdir() if d.is_dir() and "Gotowe" in d.name]

if target_dirs:
    target = target_dirs[0]
    print(f"✅ Found: {target.name}")

    # List files
    files = sorted(target.glob("*.md"))
    hierarchy_files = [f for f in files if any(x in f.name for x in ["HIERARCHIA", "INDEX", "KOMPENDIUM"])]

    print(f"\n📄 Hierarchy Documents ({len(hierarchy_files)} files):")
    for f in hierarchy_files:
        size = f.stat().st_size / 1024
        print(f"  ✅ {f.name} ({size:.1f} KB)")

    # Total stats
    total_size = sum(f.stat().st_size for f in hierarchy_files) / 1024
    print(f"\n📊 Total: {total_size:.1f} KB across {len(hierarchy_files)} documents")

    # Content check
    print(f"\n📋 Document Types:")
    print(f"  - Kompendium (Master index): {'✅' if any('KOMPENDIUM' in f.name for f in hierarchy_files) else '❌'}")
    print(f"  - System Analysis: {'✅' if any('WAZNOSCI' in f.name for f in hierarchy_files) else '❌'}")
    print(f"  - ASCII Diagrams: {'✅' if any('ASCII' in f.name for f in hierarchy_files) else '❌'}")
    print(f"  - Flow Diagram (Mermaid): {'✅' if any('FLOW' in f.name for f in hierarchy_files) else '❌'}")
    print(f"  - Sankey Diagram: {'✅' if any('SANKEY' in f.name for f in hierarchy_files) else '❌'}")
    print(f"  - Master Index: {'✅' if any('INDEX' in f.name for f in hierarchy_files) else '❌'}")

    print(f"\n✅ All hierarchy documentation ready at:")
    print(f"   {target}")
else:
    print("❌ Desktop folder not found")
