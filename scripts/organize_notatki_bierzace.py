#!/usr/bin/env python3
"""
ADRION 369 - Organize Notatki bierzące files to Genesis Record
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Source and destination
source_folder = r'C:\Users\adiha\Desktop\Notatki bierzące'
genesis_root = r'C:\Users\adiha\162 demencje w schemacie 369\Genesis Record'

# File mapping to destination folders
file_mapping = {
    '📋 CHECKLIST WDROŻENIA ADRION 369 v4.0.txt': r'02_STRATEGY_PLANS\Deployment_Planning',
    '🚀 Efekty, Skutki i Konsekwencje Wykonanej Pracy.txt': r'10_RAPORTY_DZIALANIA_SYSTEMU\Business_Impact',
    'Całarozmowa naprawy.txt': r'10_RAPORTY_DZIALANIA_SYSTEMU\Session_Reports',
    'Cloude Complete OpenRouter Deployment Package for ADRION 369.txt': r'03_TECHNICAL_SPECS\Deployment_Packages',
    'Główne częstotliwości Solfeggio i ich działanie.md': r'10_RAPORTY_DZIALANIA_SYSTEMU\Research_Articles',
    'MASTER ORCHESTRATOR (ADRION 369 v4.0).txt': r'03_TECHNICAL_SPECS\System_Architecture',
    'NADRZEDNY KODEKS.html': r'10_RAPORTY_DZIALANIA_SYSTEMU\Governance',
    'OS 369 -Architektura Całkowitego Przejęcia Systemu Android.md': r'03_TECHNICAL_SPECS\Architecture_Mobile',
    'Raport z Analizy systemu .txt': r'10_RAPORTY_DZIALANIA_SYSTEMU\System_Analysis',
    'Ustawienia osobiste la master orkiestrato 4.0.txt': r'10_RAPORTY_DZIALANIA_SYSTEMU\Personal_Settings'
}

print("=" * 80)
print("🎯 ADRION 369 - Reorganizacja Notatki bierzące → Genesis Record")
print("=" * 80)

copied = 0
failed = 0

# Create destination folders if not exist
for target_rel in set(file_mapping.values()):
    target_path = os.path.join(genesis_root, target_rel)
    os.makedirs(target_path, exist_ok=True)
    print(f"✅ Folder: {target_rel}")

print("\n📋 Kopiowanie plików:\n")

# Copy files
for filename, target_rel in file_mapping.items():
    source_file = os.path.join(source_folder, filename)
    target_folder = os.path.join(genesis_root, target_rel)
    target_file = os.path.join(target_folder, filename)

    if os.path.exists(source_file):
        try:
            shutil.copy2(source_file, target_file)
            file_size = os.path.getsize(source_file) / 1024  # KB
            print(f"✅ {filename}")
            print(f"   → {target_rel} ({file_size:.1f} KB)")
            copied += 1
        except Exception as e:
            print(f"❌ Błąd: {filename} - {e}")
            failed += 1
    else:
        print(f"⚠️  Nie znaleziono: {filename}")
        failed += 1

print("\n" + "=" * 80)
print("📊 PODSUMOWANIE OPERACJI")
print("=" * 80)
print(f"✅ Skopiowanych: {copied}")
print(f"❌ Błędów: {failed}")
print(f"📁 Lokalizacja: {genesis_root}")
print(f"⏰ Data: {datetime.now().isoformat()}")
print("=" * 80)
