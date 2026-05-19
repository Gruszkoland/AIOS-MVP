from __future__ import annotations

import argparse
import html
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List
from zipfile import ZipFile
import xml.etree.ElementTree as ET


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

STOPWORDS = {
    "oraz", "jest", "jako", "ktore", "ktory", "ktora", "przez", "tego", "tegoz",
    "tego", "tego", "przy", "dla", "nad", "pod", "bez", "czy", "nie", "tak",
    "sie", "to", "ten", "ta", "to", "wraz", "oraz", "aby", "jego", "jej", "ich",
    "the", "and", "for", "with", "from", "that", "this", "into", "jestes", "zostal",
}


def extract_paragraphs(docx_path: Path) -> List[str]:
    with ZipFile(docx_path) as zf:
        xml_data = zf.read("word/document.xml")

    root = ET.fromstring(xml_data)
    paragraphs: List[str] = []

    for p in root.findall(".//w:body/w:p", NS):
        texts = [t.text or "" for t in p.findall(".//w:t", NS)]
        line = "".join(texts).strip()
        if line:
            paragraphs.append(html.unescape(line))

    return paragraphs


def clean_words(text: str) -> List[str]:
    words = re.findall(r"[A-Za-zÀ-ÿ0-9_\-]{4,}", text.lower())
    return [w for w in words if w not in STOPWORDS and not w.isdigit()]


def short_summary(paragraphs: List[str], max_sentences: int = 2) -> str:
    if not paragraphs:
        return "Brak tresci tekstowej do podsumowania."

    selected = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        selected.append(p)
        if len(selected) >= max_sentences:
            break

    if not selected:
        return "Brak tresci tekstowej do podsumowania."

    return " ".join(selected)


def classify(name: str) -> str:
    lowered = name.lower()
    if "gminy" in lowered or "jedności" in lowered or "jednosci" in lowered:
        return "Projekt Gminy Jednosci"
    if "protok" in lowered or "zabezpieczenie" in lowered or "sieć cienia" in lowered or "siec cienia" in lowered:
        return "Protokoly i Operacje"
    if "ewolucja" in lowered or "fizyka" in lowered or "symulacja" in lowered:
        return "Nauka Fizyka Ewolucja"
    return "Raporty i Symulacje"


def rel_link(root: Path, file_path: Path) -> str:
    rel = file_path.relative_to(root)
    target = str(rel).replace("\\", "/")
    encoded = target.replace(" ", "%20")
    return f"[{file_path.name}]({encoded})"


def generate(source_dir: Path, output_file: Path) -> None:
    files = sorted(source_dir.rglob("*.docx"), key=lambda p: str(p).lower())

    lines: List[str] = []
    lines.append("# JEDNOSC SUMMARIES")
    lines.append("")
    lines.append(f"Data generacji: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Zakres: {len(files)} plikow DOCX")
    lines.append("")

    for idx, file_path in enumerate(files, start=1):
        paragraphs = extract_paragraphs(file_path)
        first_text = " ".join(paragraphs[:8])
        keywords = [w for w, _ in Counter(clean_words(first_text)).most_common(8)]
        summary = short_summary(paragraphs, max_sentences=2)
        cluster = classify(file_path.name)

        lines.append(f"## {idx}. {file_path.name}")
        lines.append("")
        lines.append(f"- Lokalizacja: {rel_link(output_file.parent, file_path)}")
        lines.append(f"- Klaster: {cluster}")
        lines.append(f"- Liczba akapitow: {len(paragraphs)}")
        lines.append(f"- Slowa kluczowe: {', '.join(keywords) if keywords else 'brak'}")
        lines.append(f"- Streszczenie: {summary}")
        lines.append("")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate summaries for Jednosc DOCX files")
    parser.add_argument("--source-dir", default="docs/Jednosc_Source", help="Source directory with docx files")
    parser.add_argument("--output", default="docs/JEDNOSC_SUMMARIES.md", help="Output markdown file")
    args = parser.parse_args()

    generate(Path(args.source_dir), Path(args.output))
    print(f"Summaries written: {args.output}")
