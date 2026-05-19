#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Usunięcie duplikatów z folderu 💭 Filozofia w Jedności
"""
import os
from pathlib import Path

root_folder = r"C:\Users\adiha\Desktop\Dokumentacja\💭 Filozofia w Jedności"

deleted = 0
skipped = 0

print("🗑️  USUWANIE DUPLIKATÓW — 💭 Filozofia w Jedności")
print("=" * 70)
print("")

# Rekurencyjnie przejdź przez wszystkie foldery
for dirpath, dirnames, filenames in os.walk(root_folder):
    relative_path = os.path.relpath(dirpath, root_folder)
    
    # Przetwórz pliki .txt i .gdoc
    for filename in filenames:
        if filename.endswith(('.txt', '.gdoc')):
            src = os.path.join(dirpath, filename)
            
            # Sprawdź czy istnieje odpowiadający .md
            base = src.rsplit('.', 1)[0]
            md_file = base + '.md'
            
            if os.path.exists(md_file):
                try:
                    os.remove(src)
                    if relative_path == '.':
                        folder_display = "(główny folder)"
                    else:
                        folder_display = relative_path
                    print(f"  ✅ Usunięto: {filename}")
                    deleted += 1
                except Exception as e:
                    print(f"  ❌ Błąd: {filename} - {str(e)}")
                    skipped += 1
            else:
                print(f"  ⚠️  Brak .md dla: {filename}")
                skipped += 1

print(f"\n{'='*70}")
print(f"📊 PODSUMOWANIE USUWANIA:")
print(f"  Usunięto: {deleted}")
print(f"  Błędów/Pominięto: {skipped}")
print(f"\n✅ USUWANIE GOTOWE!")
