#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skanowanie PDF w Desktop\Dokumentacja
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

def should_exclude_path(dirpath):
    rel_path = os.path.relpath(dirpath, ROOT)
    parts = rel_path.split(os.sep)
    if parts and parts[0] in EXCLUDED_TOP_FOLDERS:
        return True
    return False

def scan_pdfs(root_path):
    stats = {
        'total_pdf': 0,
        'by_folder': defaultdict(int),
        'largest': [],
    }
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        if should_exclude_path(dirpath):
            dirnames[:] = []
            continue
        
        rel_path = os.path.relpath(dirpath, ROOT)
        if rel_path == '.':
            rel_path = '(główny folder)'
        
        for filename in filenames:
            if filename.endswith('.pdf'):
                filepath = os.path.join(dirpath, filename)
                size = os.path.getsize(filepath)
                stats['total_pdf'] += 1
                stats['by_folder'][rel_path] += 1
                stats['largest'].append((rel_path, filename, size))
    
    stats['largest'].sort(key=lambda x: x[2], reverse=True)
    return stats

if __name__ == '__main__':
    print("🔍 SKANOWANIE PDF — C:\\Users\\adiha\\Desktop\\Dokumentacja")
    print("=" * 80)
    
    stats = scan_pdfs(ROOT)
    
    print(f"\n📊 STATYSTYKA PDF:")
    print(f"  Łącznie .pdf: {stats['total_pdf']}")
    
    print(f"\n📁 TOP FOLDERY Z PDF:")
    for folder, count in sorted(stats['by_folder'].items(), key=lambda x: x[1], reverse=True)[:20]:
        if count > 0:
            print(f"  {count:3} pdf — {folder}")
    
    print(f"\n📦 TOP 10 NAJWIĘKSZYCH PDF (mają szansę na ekstrakcję tekstu):")
    for i, (folder, name, size) in enumerate(stats['largest'][:10], 1):
        size_mb = size / (1024*1024)
        print(f"  {i}. {size_mb:6.1f} MB — {name[:60]}")
    
    print("\n" + "=" * 80)
