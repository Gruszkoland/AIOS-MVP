#!/usr/bin/env python3
"""Build script for ADRION 369 UAP Systray"""
import sys
import os
from pathlib import Path

# Add PyInstaller to path
os.chdir(Path(__file__).parent)

import PyInstaller.main

spec_file = Path("uap_systray.spec").absolute()
print(f"\nBuilding with spec: {spec_file}")
print("=" * 60)

try:
    PyInstaller.main.run([
        str(spec_file),
        '--distpath=./dist',
        '--buildpath=./build',
        '--specpath=./'
    ])
    print("\n" + "=" * 60)
    print("✓ Build completed!")

    # Check output
    exe_path = Path("dist/uap_systray.exe")
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024*1024)
        print(f"✓ Executable created: dist/uap_systray.exe ({size_mb:.1f} MB)")
        sys.exit(0)
    else:
        print("✗ Executable not found in dist/")
        sys.exit(1)

except Exception as e:
    print(f"\n✗ Build failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
