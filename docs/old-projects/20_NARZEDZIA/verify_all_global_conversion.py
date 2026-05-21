#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Globalna Weryfikacja — Potwierdzenie kompletności konwersji
"""
import os
from pathlib import Path
from collections import defaultdict

ROOT = r"C:\Users\adiha\Desktop\Dokumentacja"

EXCLUDED_TOP_FOLDERS = {
    'Obsydian-synchronizacja dokumentów',
    'Obsydian-synchronizacja dokumentĂłw',
    '.1_Projekty',
    '07_ARCHIWUM',
    '.1_RAPORTY_WDRAŻANIA',
}

EXCLUDED_FILES = {
    'zegarki i dane kontaktowe.rtf',
    'desktop.ini',
}

OLD_EXTENSIONS = {'.txt', '.gdoc', '.docx', '.gsheet'}

def should_exclude_path(dirpath):
    """Sprawdzaj czy ścieżka powinna być pominięta"""
    rel_path = os.path.relpath(dirpath, ROOT)
    parts = rel_path.split(os.sep)
    if parts and parts[0] in EXCLUDED_TOP_FOLDERS:
        return True
    return False

def verify_conversion(root_path):
    """Weryfikuj konwersję — policz .md pliki i pozostałe stare formaty"""
    stats = {
        'md_found': 0,
        'old_format_remaining': 0,
        'remaining_by_ext': defaultdict(int),
        'by_folder': defaultdict(lambda: {'md': 0, 'old': 0}),
    }
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        if should_exclude_path(dirpath):
            dirnames[:] = []
            continue
        
        rel_path = os.path.relpath(dirpath, ROOT)
        if rel_path == '.':
            rel_path = '(główny folder)'
        
        for filename in filenames:
            if filename in EXCLUDED_FILES:
                continue
            
            _, ext = os.path.splitext(filename)
            
            if ext.lower() == '.md':
                stats['md_found'] += 1
                stats['by_folder'][rel_path]['md'] += 1
            elif ext.lower() in OLD_EXTENSIONS:
                stats['old_format_remaining'] += 1
                stats['remaining_by_ext'][ext] += 1
                stats['by_folder'][rel_path]['old'] += 1
    
    return stats

if __name__ == '__main__':
    print("✅ GLOBALNA WERYFIKACJA KONWERSJI")
    print("=" * 80)
    
    stats = verify_conversion(ROOT)
    
    print(f"\n📊 STATYSTYKA WERYFIKACJI:")
    print(f"  .md pliki znalezione: {stats['md_found']}")
    print(f"  Pozostałe stare formaty: {stats['old_format_remaining']}")
    
    if stats['old_format_remaining'] > 0:
        print(f"\n⚠️  POZOSTAŁE PLIKI (do ręcznego sprawdzenia):")
        for ext, count in sorted(stats['remaining_by_ext'].items()):
            print(f"  {ext:8} → {count:4} plików")
        
        print(f"\n  Foldery z pozostałymi plikami:")
        for folder, counts in sorted(stats['by_folder'].items()):
            if counts['old'] > 0:
                print(f"    {counts['old']} plików w: {folder}")
    
    if stats['old_format_remaining'] == 0:
        print(f"\n🎉 100% SUKCES - WSZYSTKIE DUPLIKATY USUNIĘTE!")
    else:
        print(f"\n⚠️  {stats['old_format_remaining']} plików pozostało")
    
    print("=" * 80)
