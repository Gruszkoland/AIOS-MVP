#!/usr/bin/env python3
"""Move hierarchy documentation to correct Desktop folder"""

import shutil
import os
from pathlib import Path

def move_hierarchy_docs():
    desktop = Path(r"C:\Users\adiha\Desktop")
    source_dir = desktop / "SPRAWOZDANIE I DIAGRAM"
    target_dir = None

    # Find target folder (handles Polish characters)
    for item in desktop.iterdir():
        if item.is_dir() and "Gotowe" in item.name and "Projekty" in item.name:
            target_dir = item
            break

    if not target_dir:
        print("❌ Target folder not found")
        return False

    print(f"✅ Target folder: {target_dir}")

    # Move hierarchy files
    hierarchy_files = []
    for pattern in ["*HIERARCHIA*", "*INDEX*", "*KOMPENDIUM*"]:
        hierarchy_files.extend(source_dir.glob(pattern + ".md"))

    if not hierarchy_files:
        print("❌ No hierarchy files found in source")
        return False

    print(f"📦 Found {len(hierarchy_files)} files to move:")

    for src_file in hierarchy_files:
        dst_file = target_dir / src_file.name
        try:
            shutil.copy2(src_file, dst_file)
            size = src_file.stat().st_size / 1024
            print(f"  ✅ {src_file.name} ({size:.1f} KB)")
        except Exception as e:
            print(f"  ❌ Failed to copy {src_file.name}: {e}")
            return False

    # Verify
    print(f"\n✅ All files copied to: {target_dir}")
    print(f"📊 Files in destination:")

    for f in target_dir.glob("*HIERARCHIA*"):
        size = f.stat().st_size / 1024
        print(f"   - {f.name} ({size:.1f} KB)")

    return True

if __name__ == "__main__":
    success = move_hierarchy_docs()
    exit(0 if success else 1)
