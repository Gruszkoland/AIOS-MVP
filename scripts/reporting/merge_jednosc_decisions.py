#!/usr/bin/env python3
"""
merge_jednosc_decisions.py

ADRION 369 — scala MAP + REVIEW CHECKLIST decisions w finalną mapę produkcyjną.

Wejście:
    docs/JEDNOSC_162D_MAP.md          — pełna tabela 17 pozycji (v2 classifier)
    docs/JEDNOSC_162D_REVIEW_CHECKLIST.md — decyzje eksperckie dla 6 pozycji REVIEW

Wyjście:
    docs/JEDNOSC_162D_FINAL.md        — mapa produkcyjna: 17 pozycji ze statusem

Logika merge:
    OK  → source=AUTO-APPROVED, status=FINAL  (bez zmian)
    REVIEW:
        [x] APPROVED-WSTEPNIE    → source=PRE-APPROVED, status=FINAL
        [x] KEEP + [x] APPROVED  → source=KEEP, status=FINAL
        [x] CHANGE + prawo_docelowe wypełnione → source=CHANGE, status=FINAL (nowe prawo)
        [x] CHANGE + prawo_docelowe puste      → source=CHANGE, status=PENDING_TARGET
        brak checkboxów                         → source=UNRESOLVED, status=PENDING_DECISION

Użycie:
    python scripts/reporting/merge_jednosc_decisions.py
    python scripts/reporting/merge_jednosc_decisions.py --map docs/MAP.md --output docs/FINAL.md
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DEFAULT_MAP = "docs/JEDNOSC_162D_MAP.md"
DEFAULT_CHECKLIST = "docs/JEDNOSC_162D_REVIEW_CHECKLIST.md"
DEFAULT_OUTPUT = "docs/JEDNOSC_162D_FINAL.md"

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class MapEntry:
    filename: str
    perspektywa: str
    tryb: str
    prawo: str
    triada: str
    confidence: float
    signal: float
    review_tag: str   # OK | REVIEW
    uzasadnienie: str


@dataclass
class ChecklistDecision:
    filename: str
    obecne_prawo: str
    obecna_triada: str
    confidence: float
    signal: float
    rec_decision: str    # KEEP | CHANGE (automatyczna)
    suggested_prawo: str
    suggested_triada: str
    expert_keep: bool
    expert_change: bool
    prawo_docelowe: str   # wypełnione przez eksperta
    triada_docelowa: str
    pre_approved: bool    # Status: [x] APPROVED-WSTEPNIE
    model_suggested: bool # Status: [ ] APPROVED-MODEL-SUGGESTED


@dataclass
class FinalEntry:
    filename: str
    perspektywa: str
    tryb: str
    prawo: str
    triada: str
    confidence: float
    signal: float
    source: str   # AUTO-APPROVED | PRE-APPROVED | KEEP | CHANGE | UNRESOLVED | MISSING
    status: str   # FINAL | PENDING_DECISION | PENDING_TARGET
    uzasadnienie: str


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

_DOC_LINK_RE = re.compile(r'\[(.+?)\]\(')


def _extract_filename(cell: str) -> str:
    """Wyciąga nazwę pliku z komórki Markdown: '[name.docx](ścieżka)' → 'name.docx'."""
    m = _DOC_LINK_RE.search(cell)
    return m.group(1).strip() if m else cell.strip()


_MAP_ROW_RE = re.compile(
    r'^\|\s*\d+\s*\|'          # # (numer)
    r'\s*(\[.*?\]\(.*?\))\s*\|' # Dokument (link)
    r'\s*(\w+)\s*\|'            # Perspektywa
    r'\s*(\w+)\s*\|'            # Tryb
    r'\s*(G\d)\s*\|'            # Prawo
    r'\s*(\w+)\s*\|'            # Triada
    r'\s*([\d.]+)\s*\|'         # Confidence
    r'\s*([\d.]+)\s*\|'         # Signal
    r'\s*(\w+)\s*\|'            # Review (OK|REVIEW)
    r'\s*(.+?)\s*\|'            # Uzasadnienie
)


def parse_map(path: Path) -> list[MapEntry]:
    """Parsuje JEDNOSC_162D_MAP.md → lista MapEntry (17 pozycji)."""
    entries: list[MapEntry] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = _MAP_ROW_RE.match(line)
            if m:
                doc_cell, persp, tryb, prawo, triada, conf_s, sig_s, review, uzas = m.groups()
                entries.append(MapEntry(
                    filename=_extract_filename(doc_cell),
                    perspektywa=persp.strip(),
                    tryb=tryb.strip(),
                    prawo=prawo.strip(),
                    triada=triada.strip(),
                    confidence=float(conf_s),
                    signal=float(sig_s),
                    review_tag=review.strip(),
                    uzasadnienie=uzas.strip(),
                ))
    return entries


def _get_field(lines: list[str], key: str) -> str:
    """Wyciąga wartość pola '- {key}: {wartość}' z listy linii."""
    prefix = f"- {key}:"
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix):].strip()
    return ""


def parse_checklist(path: Path) -> dict[str, ChecklistDecision]:
    """Parsuje JEDNOSC_162D_REVIEW_CHECKLIST.md → dict {filename: ChecklistDecision}."""
    decisions: dict[str, ChecklistDecision] = {}
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # Rozbij na sekcje: ### N. filename\n...następna sekcja
    sections = re.split(r'\n###\s+\d+\.\s+', content)
    for sec in sections[1:]:
        lines = sec.strip().splitlines()
        if not lines:
            continue

        filename = lines[0].strip()

        obecna = _get_field(lines, "Obecna klasyfikacja")
        parts = [p.strip() for p in obecna.split("/")]
        obecne_prawo = parts[0] if parts else ""
        obecna_triada = parts[1] if len(parts) > 1 else ""

        conf_s = _get_field(lines, "Confidence")
        sig_s = _get_field(lines, "Signal")
        try:
            confidence = float(conf_s)
        except ValueError:
            confidence = 0.0
        try:
            signal = float(sig_s)
        except ValueError:
            signal = 0.0

        rec_decision = _get_field(lines, "Rekomendacja automatyczna")
        suggested_prawo = _get_field(lines, "Sugerowane prawo docelowe")
        suggested_triada = _get_field(lines, "Sugerowana triada docelowa")
        prawo_docelowe = _get_field(lines, "Prawo docelowe (jesli CHANGE)")
        triada_docelowa = _get_field(lines, "Triada docelowa (jesli CHANGE)")
        status_val = _get_field(lines, "Status")

        # Parsuj checkboxy decyzji eksperta
        decyzja_line = ""
        for line in lines:
            if line.strip().startswith("- Decyzja eksperta:"):
                decyzja_line = line
                break

        expert_keep = "[x] KEEP" in decyzja_line
        expert_change = "[x] CHANGE" in decyzja_line
        pre_approved = "APPROVED-WSTEPNIE" in status_val
        model_suggested = "APPROVED-MODEL-SUGGESTED" in status_val

        decisions[filename] = ChecklistDecision(
            filename=filename,
            obecne_prawo=obecne_prawo,
            obecna_triada=obecna_triada,
            confidence=confidence,
            signal=signal,
            rec_decision=rec_decision,
            suggested_prawo=suggested_prawo,
            suggested_triada=suggested_triada,
            expert_keep=expert_keep,
            expert_change=expert_change,
            prawo_docelowe=prawo_docelowe,
            triada_docelowa=triada_docelowa,
            pre_approved=pre_approved,
            model_suggested=model_suggested,
        )

    return decisions


# ---------------------------------------------------------------------------
# Merge logic
# ---------------------------------------------------------------------------

_TRIAD_FOR_LAW: dict[str, str] = {
    "G1": "Unity", "G2": "Unity", "G3": "Unity",
    "G4": "Truth", "G5": "Truth", "G6": "Truth",
    "G7": "Goodness", "G8": "Goodness", "G9": "Goodness",
}


def merge(
    map_entries: list[MapEntry],
    decisions: dict[str, ChecklistDecision],
) -> list[FinalEntry]:
    """Scala MAP + CHECKLIST → lista FinalEntry ze statusem FINAL lub PENDING."""
    results: list[FinalEntry] = []

    for e in map_entries:
        if e.review_tag == "OK":
            # Pozycja automatycznie zatwierdzona — bez zmian
            results.append(FinalEntry(
                filename=e.filename,
                perspektywa=e.perspektywa,
                tryb=e.tryb,
                prawo=e.prawo,
                triada=e.triada,
                confidence=e.confidence,
                signal=e.signal,
                source="AUTO-APPROVED",
                status="FINAL",
                uzasadnienie=e.uzasadnienie,
            ))
            continue

        # Pozycja REVIEW — szukaj decyzji w checkliście
        dec = decisions.get(e.filename)

        if dec is None:
            results.append(FinalEntry(
                filename=e.filename,
                perspektywa=e.perspektywa,
                tryb=e.tryb,
                prawo=e.prawo,
                triada=e.triada,
                confidence=e.confidence,
                signal=e.signal,
                source="MISSING",
                status="PENDING_DECISION",
                uzasadnienie=e.uzasadnienie,
            ))
            continue

        if dec.pre_approved or (dec.expert_keep and not dec.expert_change):
            # KEEP — zachowaj bieżącą klasyfikację
            if dec.pre_approved:
                source = "PRE-APPROVED"
            elif dec.model_suggested:
                source = "MODEL-SUGGESTED"
            else:
                source = "KEEP"
            results.append(FinalEntry(
                filename=e.filename,
                perspektywa=e.perspektywa,
                tryb=e.tryb,
                prawo=e.prawo,
                triada=e.triada,
                confidence=e.confidence,
                signal=e.signal,
                source=source,
                status="FINAL",
                uzasadnienie=e.uzasadnienie,
            ))

        elif dec.expert_change:
            # CHANGE — użyj prawa docelowego eksperta (lub modelu jako fallback)
            target_prawo = dec.prawo_docelowe.strip() or dec.suggested_prawo or e.prawo
            target_triada = (
                dec.triada_docelowa.strip()
                or dec.suggested_triada
                or _TRIAD_FOR_LAW.get(target_prawo, e.triada)
            )
            # Status FINAL tylko gdy ekspert podał konkretne prawo docelowe;
            # w przeciwnym przypadku: PENDING_TARGET (brak potwierdzenia przez eksperta)
            has_expert_target = bool(dec.prawo_docelowe.strip())
            results.append(FinalEntry(
                filename=e.filename,
                perspektywa=e.perspektywa,
                tryb=e.tryb,
                prawo=target_prawo,
                triada=target_triada,
                confidence=e.confidence,
                signal=e.signal,
                source="MODEL-SUGGESTED" if dec.model_suggested else "CHANGE",
                status="FINAL" if has_expert_target else "PENDING_TARGET",
                uzasadnienie=e.uzasadnienie,
            ))

        else:
            # Brak decyzji — żaden checkbox niezaznaczony
            results.append(FinalEntry(
                filename=e.filename,
                perspektywa=e.perspektywa,
                tryb=e.tryb,
                prawo=e.prawo,
                triada=e.triada,
                confidence=e.confidence,
                signal=e.signal,
                source="UNRESOLVED",
                status="PENDING_DECISION",
                uzasadnienie=e.uzasadnienie,
            ))

    return results


# ---------------------------------------------------------------------------
# Output builder
# ---------------------------------------------------------------------------

def build_final_markdown(entries: list[FinalEntry]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final = [e for e in entries if e.status == "FINAL"]
    pending = [e for e in entries if e.status != "FINAL"]

    triada_count: dict[str, int] = {}
    for e in final:
        triada_count[e.triada] = triada_count.get(e.triada, 0) + 1

    source_count: dict[str, int] = {}
    for e in entries:
        source_count[e.source] = source_count.get(e.source, 0) + 1

    lines: list[str] = [
        "# JEDNOSC 162D FINAL",
        "",
        f"Data generacji: {now}",
        "Wersja: merge v1 (AUTO-APPROVED + REVIEW decisions)",
        f"Pozycji FINAL: {len(final)} / {len(entries)}",
        f"Pozycji PENDING: {len(pending)}",
        "",
        "## Statystyki",
        "",
        "### Zrodla klasyfikacji",
        "",
        "| Zrodlo | Liczba |",
        "|---|---:|",
    ]
    for src, cnt in sorted(source_count.items()):
        lines.append(f"| {src} | {cnt} |")

    lines += [
        "",
        "### Rozklad triad (FINAL)",
        "",
        "| Triada | Liczba |",
        "|---|---:|",
    ]
    for t in ("Unity", "Truth", "Goodness"):
        cnt = triada_count.get(t, 0)
        lines.append(f"| {t} | {cnt} |")

    lines += [
        "",
        "## Finalna mapa produkcyjna",
        "",
        "| # | Dokument | Perspektywa | Tryb | Prawo | Triada | Confidence | Signal | Zrodlo |",
        "|---:|---|---|---|---|---|---:|---:|---|",
    ]
    for i, e in enumerate(final, 1):
        lines.append(
            f"| {i} | {e.filename} | {e.perspektywa} | {e.tryb} | {e.prawo} | {e.triada}"
            f" | {e.confidence:.2f} | {e.signal:.2f} | {e.source} |"
        )

    if pending:
        lines += [
            "",
            "## Pozycje PENDING",
            "",
            "> Poniższe pozycje wymagają uzupełnienia decyzji eksperta.",
            "> Po wypełnieniu `docs/JEDNOSC_162D_REVIEW_CHECKLIST.md` uruchom ponownie ten skrypt.",
            "",
            "| # | Dokument | Prawo | Triada | Confidence | Signal | Status | Powod |",
            "|---:|---|---|---|---:|---:|---|---|",
        ]
        for i, e in enumerate(pending, 1):
            if e.status == "PENDING_TARGET":
                reason = "CHANGE bez prawa docelowego — uzupelnij 'Prawo docelowe' w checkliście"
            else:
                reason = "Brak zaznaczonego KEEP ani CHANGE w checkliście"
            lines.append(
                f"| {i} | {e.filename} | {e.prawo} | {e.triada}"
                f" | {e.confidence:.2f} | {e.signal:.2f} | {e.status} | {reason} |"
            )
    else:
        lines += [
            "",
            "> **STATUS PRODUKCYJNY:** Wszystkie 17 pozycji zaklasyfikowane ostatecznie.",
            "> Mapa gotowa do linkowania z dokumentacją i testami.",
        ]

    lines += [
        "",
        "## Legenda",
        "",
        "| Zrodlo | Opis |",
        "|---|---|",
        "| AUTO-APPROVED | Confidence >= 0.76 lub signal >= 11.0 (OK w MAP v2) |",
        "| PRE-APPROVED  | REVIEW: KEEP + confidence >= 0.74 + signal >= 11.0 |",
        "| MODEL-SUGGESTED | REVIEW: decyzja/przypisanie uzupelnione automatycznie z checklisty |",
        "| KEEP          | REVIEW: ręczna decyzja eksperta — KEEP |",
        "| CHANGE        | REVIEW: ręczna decyzja eksperta — CHANGE (nowe prawo) |",
        "| UNRESOLVED    | REVIEW: brak decyzji w checkliście |",
        "| MISSING       | REVIEW: pozycja bez wpisu w checkliście (błąd synchronizacji) |",
    ]

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Merge JEDNOSC 162D MAP + REVIEW CHECKLIST → FINAL production map."
    )
    ap.add_argument("--map", default=DEFAULT_MAP, help="Ścieżka do MAP.md")
    ap.add_argument("--checklist", default=DEFAULT_CHECKLIST, help="Ścieżka do CHECKLIST.md")
    ap.add_argument("--output", default=DEFAULT_OUTPUT, help="Ścieżka wyjściowa FINAL.md")
    args = ap.parse_args()

    map_path = Path(args.map)
    checklist_path = Path(args.checklist)
    output_path = Path(args.output)

    print(f"[MERGE] Parsing MAP: {map_path}")
    map_entries = parse_map(map_path)
    print(f"  Entries: {len(map_entries)}")

    print(f"[MERGE] Parsing CHECKLIST: {checklist_path}")
    decisions = parse_checklist(checklist_path)
    print(f"  Decisions: {len(decisions)}")

    print("[MERGE] Merging...")
    final_entries = merge(map_entries, decisions)
    final_count = sum(1 for e in final_entries if e.status == "FINAL")
    pending_count = sum(1 for e in final_entries if e.status != "FINAL")
    print(f"  FINAL: {final_count}  PENDING: {pending_count}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_final_markdown(final_entries), encoding="utf-8")
    print(f"[MERGE] Final map written: {output_path}")


if __name__ == "__main__":
    main()
