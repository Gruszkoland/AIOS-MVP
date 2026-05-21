#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Globalna Konwersja — Dokumentacja + 01_PROJEKTY_KOD
Wyklucza: Obsydian-synchronizacja, .1_Projekty, 07_ARCHIWUM
"""
import os
import shutil
from pathlib import Path
from collections import defaultdict
import sys

ROOT = r"C:\Users\adiha\Desktop\Dokumentacja"

# Wykluczone TOP-LEVEL foldery
EXCLUDED_TOP_FOLDERS = {
    'Obsydian-synchronizacja dokumentów',
    'Obsydian-synchronizacja dokumentĂłw',  # UTF-8 variant
    '.1_Projekty',
    '07_ARCHIWUM',
    '.1_RAPORTY_WDRAŻANIA',
}

# Wykluczone pliki
EXCLUDED_FILES = {
    'zegarki i dane kontaktowe.rtf',
    'desktop.ini',
}

# Rozszerzenia do konwersji
TARGET_EXTENSIONS = {'.txt', '.gdoc', '.docx', '.gsheet'}

def should_exclude_path(dirpath):
    """Sprawdź czy ścieżka powinna być pominięta"""
    rel_path = os.path.relpath(dirpath, ROOT)
    parts = rel_path.split(os.sep)
    
    # Sprawdzaj tylko pierwszy folder (top-level)
    if parts and parts[0] in EXCLUDED_TOP_FOLDERS:
        return True
    
    return False

def convert_files(root_path):
    """Rekursywnie konwertuj pliki"""
    stats = {
        'total': 0,
        'converted': 0,
        'errors': 0,
        'skipped': 0,
        'by_ext': defaultdict(int),
    }
    
    conversion_log = []
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Sprawdź czy pominąć cały folder
        if should_exclude_path(dirpath):
            dirnames[:] = []  # Nie schodzić w głąb
            continue
        
        rel_path = os.path.relpath(dirpath, root_path)
        if rel_path == '.':
            rel_path = '(główny folder)'
        
        folder_converted = 0
        
        for filename in filenames:
            if filename in EXCLUDED_FILES:
                stats['skipped'] += 1
                continue
            
            _, ext = os.path.splitext(filename)
            
            if ext.lower() in TARGET_EXTENSIONS:
                src = os.path.join(dirpath, filename)
                dst = src.rsplit('.', 1)[0] + '.md'
                
                stats['total'] += 1
                stats['by_ext'][ext] += 1
                
                try:
                    # Sprawdź czy .md już istnieje
                    if os.path.exists(dst):
                        stats['skipped'] += 1
                        conversion_log.append(f"  ⏭️  Pominięto (już istnieje): {filename}")
                        continue
                    
                    # Konwertuj
                    shutil.copy2(src, dst)
                    stats['converted'] += 1
                    folder_converted += 1
                    conversion_log.append(f"  ✅ {filename} → {os.path.basename(dst)}")
                    
                except Exception as e:
                    stats['errors'] += 1
                    conversion_log.append(f"  ❌ BŁĄD: {filename} — {str(e)}")
        
        if folder_converted > 0:
            print(f"\n📂 {rel_path}")
            for line in conversion_log[-folder_converted:]:
                print(line)
    
    return stats

if __name__ == '__main__':
    print("🚀 GLOBALNA KONWERSJA — Dokumentacja + 01_PROJEKTY_KOD")
    print("=" * 80)
    print(f"📍 Katalog: {ROOT}")
    print(f"⏭️  Wyłączeni: Obsydian-synchronizacja, .1_Projekty, 07_ARCHIWUM")
    print("=" * 80)
    
    stats = convert_files(ROOT)
    
    print(f"\n\n📊 PODSUMOWANIE KONWERSJI:")
    print(f"  Wszystkie do konwersji: {stats['total']}")
    print(f"  Skonwertowane: {stats['converted']}")
    print(f"  Pominięte (istniejące): {stats['skipped']}")
    print(f"  Błędy: {stats['errors']}")
    
    print(f"\n📈 ROZKŁAD PO ROZSZERZENIACH:")
    for ext, count in sorted(stats['by_ext'].items()):
        if count > 0:
            print(f"  {ext:8} → {count:4} plików")
    
    print(f"\n{'✅ KONWERSJA GOTOWA!' if stats['errors'] == 0 else '⚠️  KONWERSJA Z BŁĘDAMI!'}")
    print("=" * 80)
