#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Globalne Usuwanie Duplikatów — Dopasowanie do convert_all_global_recursive.py
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

TARGET_EXTENSIONS = {'.txt', '.gdoc', '.docx', '.gsheet'}

def should_exclude_path(dirpath):
    """Sprawdzaj czy ścieżka powinna być pominięta"""
    rel_path = os.path.relpath(dirpath, ROOT)
    parts = rel_path.split(os.sep)
    if parts and parts[0] in EXCLUDED_TOP_FOLDERS:
        return True
    return False

def delete_duplicates(root_path):
    """Usuń oryginalne pliki jeśli istnieją ich .md kopie"""
    stats = {
        'total_checked': 0,
        'deleted': 0,
        'missing_md': 0,
        'errors': 0,
    }
    
    delete_log = []
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        if should_exclude_path(dirpath):
            dirnames[:] = []
            continue
        
        rel_path = os.path.relpath(dirpath, ROOT)
        if rel_path == '.':
            rel_path = '(główny folder)'
        
        folder_deleted = 0
        
        for filename in filenames:
            if filename in EXCLUDED_FILES:
                continue
            
            _, ext = os.path.splitext(filename)
            
            if ext.lower() in TARGET_EXTENSIONS:
                src = os.path.join(dirpath, filename)
                base = src.rsplit('.', 1)[0]
                md_file = base + '.md'
                
                stats['total_checked'] += 1
                
                # Sprawdź czy .md istnieje
                if not os.path.exists(md_file):
                    stats['missing_md'] += 1
                    delete_log.append(f"  ⚠️  BRAKUJE .md: {filename}")
                    continue
                
                try:
                    os.remove(src)
                    stats['deleted'] += 1
                    folder_deleted += 1
                    delete_log.append(f"  ✅ Usunięto: {filename}")
                except Exception as e:
                    stats['errors'] += 1
                    delete_log.append(f"  ❌ BŁĄD: {filename} — {str(e)}")
        
        if folder_deleted > 0:
            print(f"\n📂 {rel_path}")
            for line in delete_log[-folder_deleted:]:
                print(line)
    
    return stats

if __name__ == '__main__':
    print("🗑️  GLOBALNE USUWANIE DUPLIKATÓW")
    print("=" * 80)
    
    stats = delete_duplicates(ROOT)
    
    print(f"\n\n📊 PODSUMOWANIE USUWANIA:")
    print(f"  Pliki do sprawdzenia: {stats['total_checked']}")
    print(f"  Usunięte: {stats['deleted']}")
    print(f"  Brakuje .md: {stats['missing_md']}")
    print(f"  Błędy: {stats['errors']}")
    
    if stats['errors'] == 0 and stats['missing_md'] == 0:
        print(f"\n✅ USUWANIE GOTOWE - Brak błędów!")
    else:
        print(f"\n⚠️  USUWANIE Z OSTRZEŻENIAMI")
    print("=" * 80)
