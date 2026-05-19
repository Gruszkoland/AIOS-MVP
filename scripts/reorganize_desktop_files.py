#!/usr/bin/env python3
"""
ADRION 369: Reorganize Desktop files to Genesis Record
Strukturyzacja plików z ADRION 369 - AI-AGENT-OS do Genesis Record

Structure:
- Phase 2 Implementation → 02_STRATEGY_PLANS + 10_RAPORTY_DZIALANIA_SYSTEMU
- v1.0-systray → 03_TECHNICAL_SPECS + 06_SECURITY_BACKUPS
- Architektura Infrastruktury → 03_TECHNICAL_SPECS
- Logika Mechanizmów → 03_TECHNICAL_SPECS
- Metody optymalizacji → 03_TECHNICAL_SPECS
- Raporty i diagramy → 10_RAPORTY_DZIALANIA_SYSTEMU
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("FILE_REORGANIZER")

# Source and destination paths
SOURCE_DIR = Path("c:\\Users\\adiha\\Desktop\\ADRION 369 - AI-AGENT-OS")
GENESIS_DIR = Path("c:\\Users\\adiha\\162 demencje w schemacie 369\\Genesis Record")

# Target structures
TARGETS = {
    "Phase 2 Implementation": {
        "source": SOURCE_DIR / "ADRION-369-Phase2-Apr8-2026",
        "destinations": {
            "02_STRATEGY_PLANS": "Phase2_Implementation",
            "10_RAPORTY_DZIALANIA_SYSTEMU": "Phase2_Reports"
        }
    },
    "v1.0 Systray": {
        "source": SOURCE_DIR / "ADRION-v1.0-systray",
        "destinations": {
            "03_TECHNICAL_SPECS": "v1.0_Deployment",
            "06_SECURITY_BACKUPS": "v1.0_Backups"
        }
    },
    "Architektura Infrastruktury": {
        "source": SOURCE_DIR / "Architektura Infrastruktury AI (BEZ OBAW)-20260407T151120Z-3-001",
        "destinations": {
            "03_TECHNICAL_SPECS": "Architektura_Infrastruktury"
        }
    },
    "Logika Mechanizmów": {
        "source": SOURCE_DIR / "Logika działania Mechanizmów Systemu-20260407T151125Z-3-001",
        "destinations": {
            "03_TECHNICAL_SPECS": "Logika_Mechanizmow"
        }
    },
    "Metody optymalizacji": {
        "source": SOURCE_DIR / "Metody optymalizacji i wizualizacji odpowiedzi AI-20260407T151116Z-3-001",
        "destinations": {
            "03_TECHNICAL_SPECS": "Metody_Optymalizacji"
        }
    },
    "Raporty i Diagramy": {
        "source": SOURCE_DIR / "SPRAWOZDANIE I DIAGRAM",
        "destinations": {
            "10_RAPORTY_DZIALANIA_SYSTEMU": "Sprawozdanie_Diagram"
        }
    }
}


def create_genesis_folder(folder_path: Path) -> bool:
    """Create folder in Genesis Record if needed."""
    try:
        folder_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Folder created/exists: {folder_path.name}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to create folder {folder_path}: {e}")
        return False


def organize_files(source: Path, dest: Path, category_name: str) -> int:
    """
    Organize files from source to destination.
    Returns: number of files copied
    """
    if not source.exists():
        logger.warning(f"⚠ Source folder not found: {source}")
        return 0

    count = 0
    try:
        # Create destination
        create_genesis_folder(dest)

        # Copy all files recursively
        for item in source.rglob("*"):
            if item.is_file():
                # Relative path from source
                rel_path = item.relative_to(source)
                target_path = dest / rel_path

                # Create parent dirs
                target_path.parent.mkdir(parents=True, exist_ok=True)

                try:
                    shutil.copy2(item, target_path)
                    count += 1
                    if count <= 10:  # Show first 10
                        logger.debug(f"  → {rel_path}")
                except Exception as e:
                    logger.warning(f"  ✗ Failed to copy {rel_path}: {e}")

        logger.info(f"✓ {category_name}: {count} files organized to {dest.name}/")
        return count

    except Exception as e:
        logger.error(f"✗ Error organizing {category_name}: {e}")
        return 0


def generate_index() -> str:
    """Generate index of organized files."""
    index = """# GENESIS RECORD - REORGANIZATION INDEX (2026-04-08)

## Summary
Desktop ADRION 369 files reorganized into Genesis Record structure.

## Organized Folders

### 02_STRATEGY_PLANS/
- **Phase2_Implementation/** - ADRION-369-Phase2-Apr8-2026 (Phase 2 Strategy & Planning)

### 03_TECHNICAL_SPECS/
- **v1.0_Deployment/** - ADRION-v1.0-systray (v1.0 Deployment & Configuration)
- **Architektura_Infrastruktury/** - Infrastructure architecture documentation
- **Logika_Mechanizmow/** - System mechanisms logic & design
- **Metody_Optymalizacji/** - Optimization & visualization methods

### 06_SECURITY_BACKUPS/
- **v1.0_Backups/** - v1.0 Security backups and archives

### 10_RAPORTY_DZIALANIA_SYSTEMU/
- **Phase2_Reports/** - Phase 2 Reports & Documentation
- **Sprawozdanie_Diagram/** - Reports & Diagrams (Raporty i Diagramy)

## File Structure Mapping

```
Desktop/ADRION 369 - AI-AGENT-OS/
├─ ADRION-369-Phase2-Apr8-2026/
│  └─ → Genesis Record/02_STRATEGY_PLANS/Phase2_Implementation/
│     → Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/Phase2_Reports/
│
├─ ADRION-v1.0-systray/
│  └─ → Genesis Record/03_TECHNICAL_SPECS/v1.0_Deployment/
│     → Genesis Record/06_SECURITY_BACKUPS/v1.0_Backups/
│
├─ Architektura Infrastruktury AI/
│  └─ → Genesis Record/03_TECHNICAL_SPECS/Architektura_Infrastruktury/
│
├─ Logika działania Mechanizmów/
│  └─ → Genesis Record/03_TECHNICAL_SPECS/Logika_Mechanizmow/
│
├─ Metody optymalizacji i wizualizacji/
│  └─ → Genesis Record/03_TECHNICAL_SPECS/Metody_Optymalizacji/
│
└─ SPRAWOZDANIE I DIAGRAM/
   └─ → Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/Sprawozdanie_Diagram/
```

## Reorganization Completed ✅
- Date: 2026-04-08
- Source: `c:\\Users\\adiha\\Desktop\\ADRION 369 - AI-AGENT-OS`
- Target: `Genesis Record/`
- Status: Complete

## How to Find Files
All files sorted into logical categories:
- Strategy & Planning → 02_STRATEGY_PLANS/
- Technical Specifications → 03_TECHNICAL_SPECS/
- Security & Backups → 06_SECURITY_BACKUPS/
- Reports & Operations → 10_RAPORTY_DZIALANIA_SYSTEMU/
"""
    return index


def main():
    """Main reorganization process."""
    logger.info("="*70)
    logger.info("GENESIS RECORD FILE REORGANIZATION")
    logger.info("="*70)

    total_files = 0
    completed = 0

    # Process each category
    for category_name, config in TARGETS.items():
        source = Path(config["source"])

        logger.info(f"\n📁 Processing: {category_name}")
        logger.info(f"   Source: {source.name}")

        for genesis_folder, subfolder_name in config["destinations"].items():
            dest = GENESIS_DIR / genesis_folder / subfolder_name

            count = organize_files(source, dest, category_name)
            total_files += count
            if count > 0:
                completed += 1

    # Generate and save index
    logger.info("\n" + "="*70)
    logger.info("Generating reorganization index...")

    index_content = generate_index()
    index_path = GENESIS_DIR / "10_RAPORTY_DZIALANIA_SYSTEMU" / "FILE_REORGANIZATION_INDEX_2026-04-08.md"

    try:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        logger.info(f"✓ Index saved: {index_path.name}")
    except Exception as e:
        logger.error(f"✗ Failed to save index: {e}")

    # Final summary
    logger.info("\n" + "="*70)
    logger.info(f"REORGANIZATION COMPLETE")
    logger.info(f"Total files organized: {total_files}")
    logger.info(f"Categories processed: {completed}/{len(TARGETS)}")
    logger.info(f"Index: {index_path.name}")
    logger.info("="*70 + "\n")

    return total_files > 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
