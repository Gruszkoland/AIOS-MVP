#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rekursywna konwersja wszystkich .gdoc i .txt na .md 
w folderze 💭 Filozofia w Jedności i jego podfolderach
"""
import os
import shutil
from pathlib import Path

root_folder = r"C:\Users\adiha\Desktop\Dokumentacja\💭 Filozofia w Jedności"

converted = 0
failed = 0
processed_folders = set()

print("🚀 REKURSYWNA KONWERSJA — 💭 Filozofia w Jedności")
print("=" * 70)
print("")

# Rekurencyjnie przejdź przez wszystkie foldery
for dirpath, dirnames, filenames in os.walk(root_folder):
    # Pokazuj folderul tylko raz
    relative_path = os.path.relpath(dirpath, root_folder)
    if relative_path not in processed_folders:
        if dirpath != root_folder:
            print(f"\n📂 {relative_path}/")
        else:
            print(f"📂 (główny folder)")
        processed_folders.add(relative_path)
    
    # Przetwórz pliki .txt i .gdoc
    for filename in filenames:
        if filename.endswith(('.txt', '.gdoc')):
            src = os.path.join(dirpath, filename)
            # Zmień rozszerzenie na .md
            dst = src.rsplit('.', 1)[0] + '.md'
            dst_name = os.path.basename(dst)
            
            try:
                shutil.copy2(src, dst)
                print(f"  ✅ {filename} → {dst_name}")
                converted += 1
            except Exception as e:
                print(f"  ❌ {filename} - błąd: {str(e)}")
                failed += 1

print(f"\n{'='*70}")
print(f"📊 PODSUMOWANIE KONWERSJI:")
print(f"  Skonwertowanych: {converted}")
print(f"  Błędów: {failed}")
print(f"\n✅ KONWERSJA GOTOWA!")
