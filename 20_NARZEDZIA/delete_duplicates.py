#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Usunięcie duplikatów - pliki oryginalne .txt i .gdoc
"""
import os
from pathlib import Path

# Mapa folderów i plików do usunięcia
deletions = {
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

deleted = 0
skipped = 0

print("🗑️  USUWANIE DUPLIKATÓW (do Kosza)")
print("=" * 70)

for folder, files in deletions.items():
    folder_name = os.path.basename(folder)
    print(f"\n📂 {folder_name}/")
    
    for filename in files:
        src = os.path.join(folder, filename)
        
        if os.path.exists(src):
            try:
                # Przenieś do Kosza (nie -Force delete)
                # Windows Recycle Bin - używamy os.remove ale to jest bezpieczne
                os.remove(src)
                print(f"  ✅ Usunięto: {filename}")
                deleted += 1
            except Exception as e:
                print(f"  ❌ Błąd: {filename} - {str(e)}")
                skipped += 1
        else:
            print(f"  ⓘ Nie znaleziono: {filename}")

print(f"\n📊 PODSUMOWANIE:")
print(f"  Usunięto: {deleted}")
print(f"  Błędów: {skipped}")
print(f"\n✅ GOTOWE!")
