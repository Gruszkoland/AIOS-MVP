from __future__ import annotations

import argparse
import difflib
import html
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List
from zipfile import ZipFile
import xml.etree.ElementTree as ET


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


@dataclass
class DocData:
    path: Path
    paragraphs: List[str]


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


def load_docs(source_dir: Path) -> List[DocData]:
    matches = sorted(source_dir.glob("*Wizja Przysz*.docx"), key=lambda p: p.name)
    if len(matches) != 2:
        raise ValueError(
            f"Expected exactly 2 matching files in {source_dir}, found {len(matches)}"
        )

    return [DocData(path=m, paragraphs=extract_paragraphs(m)) for m in matches]


def choose_primary(a: DocData, b: DocData) -> DocData:
    # Prefer canonical filename without "(1)" unless alternative has much richer content.
    a_is_copy = "(1)" in a.path.stem
    b_is_copy = "(1)" in b.path.stem

    len_a = len(a.paragraphs)
    len_b = len(b.paragraphs)

    if a_is_copy and not b_is_copy:
        canonical, alt = b, a
    elif b_is_copy and not a_is_copy:
        canonical, alt = a, b
    else:
        canonical, alt = a, b

    canon_len = len(canonical.paragraphs)
    alt_len = len(alt.paragraphs)

    if canon_len == 0 and alt_len > 0:
        return alt

    if canon_len > 0 and alt_len >= int(canon_len * 1.1):
        return alt

    # Fallback on paragraph count if both names are ambiguous.
    if not (a_is_copy ^ b_is_copy):
        return a if len_a >= len_b else b

    return canonical


def build_report(a: DocData, b: DocData, primary: DocData) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    diff = list(
        difflib.unified_diff(
            a.paragraphs,
            b.paragraphs,
            fromfile=a.path.name,
            tofile=b.path.name,
            n=1,
            lineterm="",
        )
    )

    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

    diff_preview = diff[:220] if diff else ["(No textual differences detected)"]

    secondary = b if primary.path == a.path else a

    lines: List[str] = []
    lines.append("# Raport Porownania Wersji Dokumentu Wizja Przyszlosci")
    lines.append("")
    lines.append(f"Data analizy: {now}")
    lines.append("")
    lines.append("## Wejscie")
    lines.append("")
    lines.append(f"- {a.path}")
    lines.append(f"- {b.path}")
    lines.append("")
    lines.append("## Metryki")
    lines.append("")
    lines.append("| Plik | Liczba akapitow | Rozmiar (bajty) | Modyfikacja |")
    lines.append("|---|---:|---:|---|")
    for doc in (a, b):
        mtime = datetime.fromtimestamp(doc.path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        lines.append(
            f"| {doc.path.name} | {len(doc.paragraphs)} | {doc.path.stat().st_size} | {mtime} |"
        )

    lines.append("")
    lines.append("## Wynik porownania")
    lines.append("")
    lines.append(f"- Roznice wykryte: {'tak' if bool(diff) else 'nie'}")
    lines.append(f"- Linie dodane w diff: {added}")
    lines.append(f"- Linie usuniete w diff: {removed}")
    lines.append("")
    lines.append("## Rekomendacja wersji nadrzednej")
    lines.append("")
    lines.append(f"- Wersja nadrzedna: {primary.path.name}")
    lines.append(f"- Wersja pomocnicza: {secondary.path.name}")
    lines.append(
        "- Zasada wyboru: preferencja dla nazwy kanonicznej bez (1), z nadpisaniem tylko gdy druga wersja ma wyraznie bogatsza tresc."
    )
    lines.append("")
    lines.append("## Podglad roznic")
    lines.append("")
    lines.append("```diff")
    lines.extend(diff_preview)
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two Wizja Przyszlosci DOCX versions")
    parser.add_argument(
        "--source-dir",
        default="docs/Jednosc_Source",
        help="Directory with source DOCX files",
    )
    parser.add_argument(
        "--output",
        default=(
            "Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/REPORTS/"
            "Porownanie_Wersji_Wizja_Przyszlosci_02-04-2026.md"
        ),
        help="Output markdown report path",
    )

    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    output = Path(args.output)

    docs = load_docs(source_dir)
    a, b = docs[0], docs[1]
    primary = choose_primary(a, b)

    report = build_report(a, b, primary)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")

    print(f"Report written: {output}")
    print(f"Primary version: {primary.path.name}")


if __name__ == "__main__":
    main()
