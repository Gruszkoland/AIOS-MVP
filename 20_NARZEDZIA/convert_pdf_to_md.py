#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konwersja PDF -> MD (ekstrakcja tekstu)
Jeśli PDF ma tekst: wstaw do .md
Jeśli PDF to obraz: stwórz .md z linkiem
"""
import os
import shutil
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

def extract_text_from_pdf(pdf_path):
    """Spróbuj ekstrahować tekst z PDF, jeśli nie ma PyPDF, zwróć None"""
    try:
        from pypdf import PdfReader
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text if text.strip() else None
        except Exception as e:
            return None
    except ImportError:
        return None

def convert_pdf_to_md(pdf_path, md_path, pdf_filename):
    """Konwertuj PDF na .md"""
    # Spróbuj ekstrahować tekst
    text = extract_text_from_pdf(pdf_path)
    
    if text:
        # PDF ma tekst — wstaw do .md
        md_content = f"""# {os.path.splitext(pdf_filename)[0]}

> **Źródło:** Automatically extracted from PDF
> **Lokalizacja oryginalnego pliku:** `{os.path.relpath(pdf_path, ROOT)}`

---

{text}

---

*Dokument skonwertowany automatycznie z PDF na Markdown {os.path.basename(pdf_path)}*
"""
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        return 'text_extracted'
    else:
        # PDF to obraz lub nie da się ekstrahować — stwórz link
        pdf_rel_path = os.path.relpath(pdf_path, ROOT)
        md_content = f"""# {os.path.splitext(pdf_filename)[0]}

> **Typ:** PDF (nie można automatycznie ekstrahować tekstu — prawdopodobnie obraz/skany)

## 📄 Oryginalny dokument

Plik PDF jest dostępny tutaj:
- **Plik:** `{pdf_filename}`
- **Ścieżka:** `{pdf_rel_path}`
- **Rozmiar:** {os.path.getsize(pdf_path) / (1024*1024):.1f} MB

---

> Aby otworzyć oryginalny plik PDF, przeciągnij do przeglądarki lub otwórz w Adobe Reader.

*Tworzony automatycznie: {os.path.basename(pdf_path)} -> .md link*
"""
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        return 'link_created'

def convert_all_pdfs(root_path):
    stats = {
        'total': 0,
        'text_extracted': 0,
        'link_created': 0,
        'errors': 0,
        'by_folder': defaultdict(lambda: {'extracted': 0, 'link': 0, 'error': 0}),
    }
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        if should_exclude_path(dirpath):
            dirnames[:] = []
            continue
        
        rel_path = os.path.relpath(dirpath, ROOT)
        if rel_path == '.':
            rel_path = '(główny folder)'
        
        folder_count = 0
        
        for filename in filenames:
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(dirpath, filename)
                md_path = pdf_path.rsplit('.', 1)[0] + '.md'
                
                # Sprawdź czy .md już istnieje
                if os.path.exists(md_path):
                    print(f"  ⏭️  Pominięto (już istnieje): {filename}")
                    continue
                
                try:
                    result = convert_pdf_to_md(pdf_path, md_path, filename)
                    stats['total'] += 1
                    folder_count += 1
                    
                    if result == 'text_extracted':
                        stats['text_extracted'] += 1
                        stats['by_folder'][rel_path]['extracted'] += 1
                        print(f"  ✅ TEKST: {filename}")
                    else:
                        stats['link_created'] += 1
                        stats['by_folder'][rel_path]['link'] += 1
                        print(f"  🔗 LINK: {filename}")
                except Exception as e:
                    stats['errors'] += 1
                    stats['by_folder'][rel_path]['error'] += 1
                    print(f"  ❌ BŁĄD: {filename} — {str(e)}")
        
        if folder_count > 0:
            print(f"\n📂 {rel_path} ({folder_count} konwersji)")

    return stats

if __name__ == '__main__':
    print("🚀 KONWERSJA PDF -> MD")
    print("=" * 80)
    
    stats = convert_all_pdfs(ROOT)
    
    print(f"\n\n📊 PODSUMOWANIE:")
    print(f"  Wszystkie PDF do konwersji: {stats['total']}")
    print(f"  ✅ Tekst ekstrahowany: {stats['text_extracted']}")
    print(f"  🔗 Linki utworzone: {stats['link_created']}")
    print(f"  ❌ Błędy: {stats['errors']}")
    
    if stats['errors'] == 0:
        print(f"\n✅ KONWERSJA GOTOWA - Brak błędów!")
    else:
        print(f"\n⚠️  {stats['errors']} błędów")
    print("=" * 80)
