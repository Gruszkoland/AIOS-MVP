#!/usr/bin/env python3
"""
ADRION 369: Batch DOCX to Markdown Converter
Konwertuje dokumenty Word (.docx) na pliki Markdown (.md) z metadanymi.

Użycie:
  python convert_docx_batch.py --input "<path_do_folderu_docx>" --output "<path_do_folderu_md>"
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
import logging

try:
    from docx import Document
    from docx.text.paragraph import Paragraph
    from docx.table import Table
except ImportError:
    print("❌ ERROR: python-docx nie zainstalowany. Uruchom: pip install python-docx>=1.2.0")
    sys.exit(1)

# Konfiguracja loggingu
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


def extract_text_from_docx(docx_path: Path) -> str:
    """Ekstrakcja tekstu z dokumentu Word."""
    try:
        doc = Document(docx_path)
        text_parts = []

        for element in doc.element.body:
            if element.tag.endswith('p'):
                # Paragrafy
                p = Paragraph(element, doc.element)
                if p.text.strip():
                    text_parts.append(p.text)
            elif element.tag.endswith('tbl'):
                # Tabele
                table = Table(element, doc.element)
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells)
                    text_parts.append(row_text)

        return "\n\n".join(text_parts)
    except Exception as e:
        logger.error(f"❌ Błąd ekstrakcji z {docx_path}: {e}")
        return None


def create_markdown_file(docx_path: Path, output_dir: Path) -> bool:
    """Tworzy plik Markdown z zawartością DOCX."""

    # Ekstrakcja tekstu
    text_content = extract_text_from_docx(docx_path)
    if text_content is None:
        return False

    # Metadane
    file_size = docx_path.stat().st_size
    line_count = len(text_content.split('\n'))
    word_count = len(text_content.split())
    conversion_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Nagłówek Markdown
    md_filename = docx_path.stem + ".md"
    md_content = f"""# {docx_path.stem}

> **Metadane Konwersji**
> - **Źródło:** `{docx_path.name}`
> - **Data konwersji:** {conversion_date}
> - **Rozmiar oryginalnego:** {file_size / 1024:.2f} KB
> - **Linie:** {line_count}
> - **Słowa:** {word_count}

---

## Zawartość

{text_content}

---

*Dokumentacja wygenerowana automatycznie przez ADRION 369 Batch Converter*
"""

    # Zapis do pliku
    md_path = output_dir / md_filename
    try:
        md_path.write_text(md_content, encoding='utf-8')
        logger.info(f"✅ Konwertowano: {docx_path.name} → {md_filename}")
        return True
    except Exception as e:
        logger.error(f"❌ Błąd zapisu {md_path}: {e}")
        return False


def main():
    """Główna funkcja batch-konwersji."""
    parser = argparse.ArgumentParser(
        description="Konwertuj dokumenty DOCX na Markdown"
    )
    parser.add_argument("--input", required=True, help="Folder ze źródłowymi plikami .docx")
    parser.add_argument("--output", required=True, help="Folder docelowy dla plików .md")
    parser.add_argument("--verbose", action="store_true", help="Szczegółowy output")

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    # Walidacja katalogów
    if not input_dir.exists():
        print(f"❌ ERROR: Folder wejściowy nie istnieje: {input_dir}")
        sys.exit(1)

    if not input_dir.is_dir():
        print(f"❌ ERROR: Ścieżka wejściowa nie jest folderem: {input_dir}")
        sys.exit(1)

    # Tworzenie folderu wyjściowego
    output_dir.mkdir(parents=True, exist_ok=True)

    # Znalezienie wszystkich plików .docx
    docx_files = list(input_dir.glob("**/*.docx"))

    if not docx_files:
        print(f"⚠️  WARNING: Brak plików .docx w {input_dir}")
        sys.exit(0)

    logger.info(f"🚀 Rozpoczynam konwersję {len(docx_files)} pliku(ów)...")

    success_count = 0
    failed_count = 0

    for docx_file in sorted(docx_files):
        if create_markdown_file(docx_file, output_dir):
            success_count += 1
        else:
            failed_count += 1

    # Raport
    print("\n" + "="*60)
    print(f"📊 RAPORT KONWERSJI")
    print("="*60)
    print(f"✅ Sukces: {success_count}/{len(docx_files)}")
    print(f"❌ Błędy:  {failed_count}/{len(docx_files)}")
    print(f"📂 Output: {output_dir.absolute()}")
    print("="*60 + "\n")

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
