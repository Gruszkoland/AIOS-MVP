#!/usr/bin/env python3
"""Copy ADRION project to Desktop"""

import shutil
import os
import sys
from pathlib import Path

def copy_project():
    source = Path(r"C:\Users\adiha\162 demencje w schemacie 369")
    dest = Path(r"C:\Users\adiha\Desktop\Gotowe Projekty do Wdrożenia\ADRION-v1.0-systray")

    # Create destination parent
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Remove if exists
    if dest.exists():
        print(f"Removing existing: {dest}")
        shutil.rmtree(dest, ignore_errors=True)

    # Exclude patterns
    exclude_patterns = {
        '.venv', '.git', '__pycache__', '.pytest_cache',
        'node_modules', '.vscode', 'dist', 'build', '.egg-info'
    }

    def ignore_func(dir_path, contents):
        ignored = []
        for item in contents:
            item_path = os.path.join(dir_path, item)
            # Check if any exclude pattern matches
            for pattern in exclude_patterns:
                if pattern in item or item.endswith('.pyc'):
                    ignored.append(item)
                    break
        return set(ignored)

    print(f"Copying {source} ...")
    print(f"       to {dest}")

    try:
        shutil.copytree(source, dest, ignore=ignore_func, dirs_exist_ok=True)
        print("✅ Copy completed successfully!")

        # Verify
        if dest.exists():
            size = sum(f.stat().st_size for f in dest.rglob('*') if f.is_file()) / (1024*1024)
            count = len(list(dest.rglob('*')))
            print(f"\n📊 Destination statistics:")
            print(f"   Path: {dest}")
            print(f"   Items: {count}")
            print(f"   Size: {size:.1f} MB")
            return 0
        else:
            print("❌ Destination not found after copy")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(copy_project())
