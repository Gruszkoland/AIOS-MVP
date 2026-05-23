#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weryfikacja - sprawdzenie czy konwersja się powiodła
"""
import os

folders_to_check = {
    r"C:\Users\adiha\Desktop\Dokumentacja\System Operacyjny Agentów AI": [
        "PLAN dla stworzenia systemu operacyjnego.md",
        "Plan od Grock dla systemu operacyjnego.md",
        "Poprawki do naprawy od gemini i grocka .md",
        "Poprawki do planu.md",
    ],
    r"C:\Users\adiha\Desktop\Dokumentacja\_BIEZACE": [
        "Autonomicznego Agenta Lead Generation (LeadGen).md",
        "Diagnoza funkcji niezbędnych do systemu agentów z osobowością.md",
        "Grosk Dashbord.md",
        "Zapisane zmiany VSCODE.md",
    ],
    r"C:\Users\adiha\Desktop\Dokumentacja\Ważne dokumenty": [
        "Adrian Halicki CV.md",
    ]
}

verified = 0
missing = 0

print("✅ WERYFIKACJA KONWERSJI")
print("=" * 70)

for folder, files in folders_to_check.items():
    folder_name = os.path.basename(folder)
    print(f"\n📂 {folder_name}/")
    
    for filename in files:
        full_path = os.path.join(folder, filename)
        
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"  ✅ {filename} ({size} bytes)")
            verified += 1
        else:
            print(f"  ❌ BRAKUJE: {filename}")
            missing += 1

print(f"\n📊 PODSUMOWANIE:")
print(f"  Zweryfikowano: {verified}/9")
print(f"  Brakuje: {missing}")

if missing == 0:
    print(f"\n🎉 100% SUKCES - Wszystkie pliki skonwertowane!")
else:
    print(f"\n⚠️  Problemy: {missing} plików nie znaleziono")
