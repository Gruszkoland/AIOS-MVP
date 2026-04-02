#!/usr/bin/env python3
"""
autofill_jednosc_pending.py

ADRION 369 — automatyczne wypełnienie 4 pozycji PENDING w checkliście na podstawie
sugerowanych praw i rekomendacji modelu.

Logika:
  PENDING_TARGET (CHANGE bez prawa docelowego):
    → wpisz sugerowane prawo docelowe + triadę
  
  PENDING_DECISION (brak zaznaczonego KEEP/CHANGE):
    → zaznacz [x] KEEP jeśli rec_decision=KEEP

Możliwe statusy wejściowe:
  - [ ] APPROVED (żadna decyzja)
  - [x] APPROVED-WSTEPNIE (już zatwierdzony)

Wszyscy auto-filled otrzymają status: [ ] APPROVED-MODEL-SUGGESTED

Użycie:
  python scripts/reporting/autofill_jednosc_pending.py
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_CHECKLIST = "docs/JEDNOSC_162D_REVIEW_CHECKLIST.md"

# ---------------------------------------------------------------------------
# Parsery sekcji
# ---------------------------------------------------------------------------

def _section_lines(section_text: str) -> list[str]:
    """Rozbija tekstsekcji na linie."""
    return section_text.strip().split('\n')


def _extract_field(section_lines: list[str], key: str) -> str:
    """Wyciąga wartość pola '- {key}: {wartość}' z linii sekcji."""
    prefix = f"- {key}:"
    for line in section_lines:
        if line.strip().startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def _find_line_index(section_lines: list[str], key: str) -> int:
    """Zwraca indeks linii z danym kluczem lub -1."""
    prefix = f"- {key}:"
    for i, line in enumerate(section_lines):
        if line.strip().startswith(prefix):
            return i
    return -1


def _is_pending_target(section_lines: list[str]) -> bool:
    """Pozycja PENDING_TARGET: [x] CHANGE i pustego 'Prawo docelowe'."""
    decision = _extract_field(section_lines, "Decyzja eksperta")
    prawo_docelowe = _extract_field(section_lines, "Prawo docelowe (jesli CHANGE)")
    has_change = "[x] CHANGE" in decision
    has_no_target = not prawo_docelowe.strip()
    return has_change and has_no_target


def _is_pending_decision(section_lines: list[str]) -> bool:
    """Pozycja PENDING_DECISION: brak zaznaczonego KEEP ani CHANGE."""
    decision = _extract_field(section_lines, "Decyzja eksperta")
    has_keep = "[x] KEEP" in decision
    has_change = "[x] CHANGE" in decision
    return not (has_keep or has_change)


def _autofill_section(section_lines: list[str]) -> list[str]:
    """Wypełnia sekcję jeśli PENDING. Zwraca zaktualizowaną listę linii."""
    if _is_pending_target(section_lines):
        # PENDING_TARGET: wpisz sugerowane prawo i triadę
        suggested_prawo = _extract_field(section_lines, "Sugerowane prawo docelowe")
        suggested_triada = _extract_field(section_lines, "Sugerowana triada docelowa")
        
        if suggested_prawo and suggested_triada:
            # Znaj indeksy pół
            prawo_idx = _find_line_index(section_lines, "Prawo docelowe (jesli CHANGE)")
            triada_idx = _find_line_index(section_lines, "Triada docelowa (jesli CHANGE)")
            uzas_idx = _find_line_index(section_lines, "Uzasadnienie decyzji")
            status_idx = _find_line_index(section_lines, "Status")
            
            # Modyfikuj in-place
            if prawo_idx >= 0:
                section_lines[prawo_idx] = f"- Prawo docelowe (jesli CHANGE): {suggested_prawo}"
            if triada_idx >= 0:
                section_lines[triada_idx] = f"- Triada docelowa (jesli CHANGE): {suggested_triada}"
            if uzas_idx >= 0:
                section_lines[uzas_idx] = f"- Uzasadnienie decyzji: AUTO-FILL: {suggested_prawo}/{suggested_triada}"
            if status_idx >= 0:
                section_lines[status_idx] = "- Status: [ ] APPROVED-MODEL-SUGGESTED"
    
    elif _is_pending_decision(section_lines):
        # PENDING_DECISION: zaznacz KEEP jeśli rekomendacja modelu
        rec_decision = _extract_field(section_lines, "Rekomendacja automatyczna")
        
        if rec_decision.strip() == "KEEP":
            # Znaj indeksy pół
            decyzja_idx = _find_line_index(section_lines, "Decyzja eksperta")
            uzas_idx = _find_line_index(section_lines, "Uzasadnienie decyzji")
            status_idx = _find_line_index(section_lines, "Status")
            
            # Modyfikuj in-place
            if decyzja_idx >= 0:
                section_lines[decyzja_idx] = "- Decyzja eksperta: [x] KEEP  [ ] CHANGE"
            if uzas_idx >= 0:
                section_lines[uzas_idx] = "- Uzasadnienie decyzji: AUTO-FILL: KEEP (model recommendation)"
            if status_idx >= 0:
                section_lines[status_idx] = "- Status: [ ] APPROVED-MODEL-SUGGESTED"
    
    return section_lines


def autofill_checklist(path: Path) -> None:
    """Czyta checklist, wypełnia PENDING pozycje, wpisuje z powrotem."""
    with open(path, encoding="utf-8") as f:
        all_lines = f.readlines()
    
    output_lines: list[str] = []
    i = 0
    position = 0
    
    while i < len(all_lines):
        line = all_lines[i]
        
        # Szukaj nagłówka sekcji ### N.
        if line.lstrip().startswith("###"):
            position += 1
            # Zbierz linie sekcji aż do następnego nagłówka lub end
            section_lines_raw = [line.rstrip('\n\r')]
            i += 1
            
            while i < len(all_lines) and not all_lines[i].lstrip().startswith("###"):
                section_lines_raw.append(all_lines[i].rstrip('\n\r'))
                i += 1
            
            # Autofill sekcji
            is_target = _is_pending_target(section_lines_raw)
            is_decision = _is_pending_decision(section_lines_raw)
            
            print(f"[DEBUG] Pos {position}: target={is_target}, decision={is_decision}")
            
            if is_target or is_decision:
                print(f"[AUTO-FILL] Pozycja {position}: {'TARGET' if is_target else 'DECISION'}")
            
            section_lines = _autofill_section(section_lines_raw)
            
            # Dodaj sekcję do output
            for sl in section_lines:
                output_lines.append(sl + "\n")
        else:
            output_lines.append(line)
            i += 1
    
    with open(path, 'w', encoding="utf-8") as f:
        f.writelines(output_lines)
    
    print(f"[AUTO-FILL] Checklist zaktualizowany: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Autofill pending decisions in JEDNOSC_162D_REVIEW_CHECKLIST.md"
    )
    parser.add_argument(
        "--checklist",
        default=DEFAULT_CHECKLIST,
        help="Path to review checklist markdown",
    )
    args = parser.parse_args()
    autofill_checklist(Path(args.checklist))


if __name__ == "__main__":
    main()
