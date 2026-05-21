#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Globalny skaner dokumentacji — zlicza pliki do konwersji
"""
import os
from pathlib import Path
from collections import defaultdict

# Główny folder
ROOT = r"C:\Users\adiha\Desktop\Dokumentacja"

# Wyłączenia
EXCLUDED_FOLDERS = {
    'Ważne dokumenty',
    '.1_RAPORTY_WDRAŻANIA',
    'Historie Życia (ZDJECIA)',
    'Kontakty i Profile Psychologiczne',
    'Google AI Studio',
    'Gemini Work Flow',
}

EXCLUDED_FILES = {
    'zegarki i dane kontaktowe.rtf',
    'desktop.ini',
}

# Foldery już przetworzane
ALREADY_PROCESSED = {
    'System Operacyjny Agentów AI',
    '_BIEZACE',
    '💭 Filozofia w Jedności',
}

# Rozszerzenia do konwersji
TARGET_EXTENSIONS = {'.txt', '.gdoc', '.gsheet', '.docx', '.doc'}

def scan_folder(root_path):
    """Skanuj rekursywnie całą strukturę"""
    stats = {
        'total_files': 0,
        'convertible_files': 0,
        'by_extension': defaultdict(int),
        'by_folder': defaultdict(int),
        'excluded_files': 0,
        'excluded_folders': 0,
    }
    
    files_list = []
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Filtruj wyłączone foldery
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_FOLDERS and d not in ALREADY_PROCESSED]
        
        rel_path = os.path.relpath(dirpath, root_path)
        folder_count = 0
        
        for filename in filenames:
            stats['total_files'] += 1
            
            if filename in EXCLUDED_FILES:
                stats['excluded_files'] += 1
                continue
            
            _, ext = os.path.splitext(filename)
            stats['by_extension'][ext] += 1
            
            if ext.lower() in TARGET_EXTENSIONS:
                stats['convertible_files'] += 1
                folder_count += 1
                files_list.append({
                    'path': os.path.join(dirpath, filename),
                    'name': filename,
                    'folder': rel_path,
                    'ext': ext
                })
        
        if folder_count > 0:
            stats['by_folder'][rel_path] = folder_count
    
    return stats, files_list


if __name__ == '__main__':
    print("🔍 SKANOWANIE GLOBALNEJ DOKUMENTACJI")
    print("=" * 70)
    
    stats, files = scan_folder(ROOT)
    
    print(f"\n📊 STATYSTYKA SKANOWANIA:")
    print(f"  Łącznie plików: {stats['total_files']}")
    print(f"  Pliki do konwersji: {stats['convertible_files']}")
    print(f"  Wykluczone pliki: {stats['excluded_files']}")
    
    print(f"\n📈 ROZKŁAD PO ROZSZERZENIACH:")
    for ext, count in sorted(stats['by_extension'].items()):
        if count > 0:
            target = "✅ DO KONWERSJI" if ext.lower() in TARGET_EXTENSIONS else "⏭️  POMINIĘTE"
            print(f"  {ext:12} — {count:4} plików  {target}")
    
    print(f"\n📁 TOP FOLDERY Z PLIKAMI DO KONWERSJI:")
    for folder, count in sorted(stats['by_folder'].items(), key=lambda x: x[1], reverse=True)[:15]:
        if count > 0:
            print(f"  {count:3} plików — {folder}")
    
    print(f"\n✨ RAZEM DO KONWERSJI: {stats['convertible_files']} plików")
    print("=" * 70)
