#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konwersja plików .txt i .gdoc na .md w folderach
"""
import shutil
import os
from pathlib import Path

# Mapa folderów i plików do konwersji
conversions = {
    r"C:\Users\adiha\Desktop\Dokumentacja\System Operacyjny Agentów AI": [
        "PLAN dla stworzenia systemu operacyjnego.txt",
        "Plan od Grock dla systemu operacyjnego.txt",
        "Poprawki do naprawy od gemini i grocka .txt",
        "Poprawki do planu.txt",
    ],
    r"C:\Users\adiha\Desktop\Dokumentacja\_BIEZACE": [
        "Autonomicznego Agenta Lead Generation (LeadGen).txt",
        "Diagnoza funkcji niezbędnych do systemu agentów z osobowością.txt",
        "Grosk Dashbord.txt",
        "Zapisane zmiany VSCODE.txt",
    ],
    r"C:\Users\adiha\Desktop\Dokumentacja\Ważne dokumenty": [
        "Adrian Halicki CV.gdoc",
    ]
}

converted = 0
failed = 0

print("🚀 KONWERSJA PLIKÓW → .md")
print("=" * 70)

for folder, files in conversions.items():
    if not os.path.exists(folder):
        print(f"⚠️  Folder nie istnieje: {folder}")
        continue
    
    folder_name = os.path.basename(folder)
    print(f"\n📂 {folder_name}/")
    
    for filename in files:
        src = os.path.join(folder, filename)
        
        # Zmień rozszerzenie na .md
        dst = src.rsplit('.', 1)[0] + '.md'
        dst_name = os.path.basename(dst)
        
        if os.path.exists(src):
            try:
                shutil.copy2(src, dst)
                print(f"  ✅ {filename} → {dst_name}")
                converted += 1
            except Exception as e:
                print(f"  ❌ {filename} - błąd: {str(e)}")
                failed += 1
        else:
            print(f"  ⚠️  Plik nie znaleziony: {filename}")

print(f"\n📊 PODSUMOWANIE:")
print(f"  Skonwertowanych: {converted}")
print(f"  Błędów: {failed}")
print(f"\n✅ GOTOWE!")
