#!/usr/bin/env python3
"""Create Faza 1 systray installer package"""

import zipfile
import shutil
from pathlib import Path

def create_installer():
    workspace_root = Path.cwd()
    source_exe = workspace_root / "uap" / "desktop" / "systray" / "dist" / "uap_systray.exe"
    zip_path = workspace_root / "uap" / "desktop" / "systray" / "ADRION-systray-1.0.0.zip"

    print(f"📦 Creating installer package...")
    print(f"   Source: {source_exe}")
    print(f"   Destination: {zip_path}")

    if not source_exe.exists():
        print(f"✗ EXE not found at {source_exe}")
        return False

    # Remove existing ZIP
    if zip_path.exists():
        zip_path.unlink()
        print(f"   Cleaned existing ZIP")

    # Create ZIP with exe
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(source_exe, arcname=source_exe.name)

        zip_size_mb = zip_path.stat().st_size / (1024*1024)
        print(f"✓ Installer created successfully ({zip_size_mb:.2f} MB)")

        # Also copy launcher.ps1 into ZIP
        with zipfile.ZipFile(zip_path, 'a', zipfile.ZIP_DEFLATED) as zf:
            launcher = workspace_root / "uap" / "desktop" / "systray" / "uap_launcher.ps1"
            if launcher.exists():
                zf.write(launcher, arcname=launcher.name)
                print(f"✓ Launcher added to package")

        return True
    except Exception as e:
        print(f"✗ Error creating ZIP: {e}")
        return False

if __name__ == "__main__":
    success = create_installer()
    exit(0 if success else 1)
