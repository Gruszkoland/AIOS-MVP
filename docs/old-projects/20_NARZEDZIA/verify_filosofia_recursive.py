#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weryfikacja konwersji w folderze 💭 Filozofia w Jedności
"""
import os

root_folder = r"C:\Users\adiha\Desktop\Dokumentacja\💭 Filozofia w Jedności"

verified = 0
missing_md = 0
remaining_old = 0

print("✅ WERYFIKACJA KONWERSJI — 💭 Filozofia w Jedności")
print("=" * 70)
print("")

# Szukaj wszystkich .md plików
md_count = 0
for dirpath, dirnames, filenames in os.walk(root_folder):
    for filename in filenames:
        if filename.endswith('.md'):
            md_count += 1

# Szukaj pozostałych .txt i .gdoc plików
for dirpath, dirnames, filenames in os.walk(root_folder):
    for filename in filenames:
        if filename.endswith(('.txt', '.gdoc')):
            remaining_old += 1
            src = os.path.join(dirpath, filename)
            print(f"  ⚠️  Pozostał: {filename}")

print(f"\n{'='*70}")
print(f"📊 PODSUMOWANIE WERYFIKACJI:")
print(f"  Pliki .md znalezione: {md_count}")
print(f"  Pozostałe .txt/.gdoc: {remaining_old}")

if remaining_old == 0:
    print(f"\n🎉 100% SUKCES - Wszystkie duplikaty usunięte!")
else:
    print(f"\n⚠️  Problemy: {remaining_old} plików starego formatu pozostało")
