"""
test_jednosc_162d_final.py

Testy regresji klasyfikacji 162D dla zatwierdzonych pozycji (FINAL).

Cel:
    Każda z 17 pozycji ze statusem FINAL w docs/JEDNOSC_162D_FINAL.md
    posiada zamrożoną asercję: (filename → prawo Guardian + triada).
    Jeśli re-klasyfikator (map_jednosc_to_162d.py) zmieni wynik,
    test wykryje regresję zanim trafi na produkcję.

Uruchomienie:
    pytest tests/test_jednosc_162d_final.py -v
"""

from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Ścieżki
# ---------------------------------------------------------------------------
WORKSPACE = Path(__file__).resolve().parents[1]
MAP_SCRIPT = WORKSPACE / "scripts" / "reporting" / "map_jednosc_to_162d.py"
FINAL_MD = WORKSPACE / "docs" / "JEDNOSC_162D_FINAL.md"
CHECKLIST_MD = WORKSPACE / "docs" / "JEDNOSC_162D_REVIEW_CHECKLIST.md"

sys.path.insert(0, str(MAP_SCRIPT.parent))


# ---------------------------------------------------------------------------
# Frozen FINAL snapshot (17 pozycji zatwierdzone 2026-04-02)
# Format: (filename_fragment, expected_law, expected_triad)
# filename_fragment — unikalny fragment nazwy pliku wystarczający do identyfikacji
# ---------------------------------------------------------------------------
EXPECTED_FINAL: list[tuple[str, str, str]] = [
    # Pozycje PRE-APPROVED
    ("Projekt Gminy Jedno",          "G9", "Goodness"),   # oba warianty — patrz test poniżej
    # Pozycje AUTO-APPROVED
    ("Ewolucja Wewn",                "G3", "Unity"),
    ("Ewolucja Zmys",                "G3", "Unity"),
    ("Fizyka Cud",                   "G3", "Unity"),
    ("Karta Praw",                   "G6", "Truth"),
    ("Nawigacja Wielowymiarow",      "G5", "Truth"),
    ("Operacja _Abundantia",         "G3", "Unity"),
    ("Komunikacja Nielokalna",       "G3", "Unity"),
    ("Przebaczenia",                 "G3", "Unity"),
    ("Przesilenia",                  "G5", "Truth"),
    ("Koherencja i Inkubacja",       "G3", "Unity"),
    ("Symulacja Obrony UC1",         "G8", "Goodness"),
    ("Symulacja Wektorowa",          "G6", "Truth"),
    ("Test Turinga",                 "G6", "Truth"),
    ("Wzmacnianie Gmin",             "G3", "Unity"),
    ("Zabezpieczenie W",             "G8", "Goodness"),
]

# „Projekt Gminy" powtarza się w dwóch plikach (main + archiwalna kopia);
# oba muszą mieć G9/Goodness → obsługiwane przez dedykowany test poniżej.

# ---------------------------------------------------------------------------
# Parser FINAL.md
# ---------------------------------------------------------------------------

@dataclass
class FinalRow:
    filename: str
    perspektywa: str
    tryb: str
    prawo: str
    triada: str
    confidence: float
    signal: float
    source: str


@dataclass
class PendingRow:
    filename: str
    prawo: str
    triada: str
    status: str


_FINAL_ROW_RE = re.compile(
    r"^\|\s*\d+\s*\|"           # #
    r"\s*(.+?)\s*\|"            # Dokument
    r"\s*(\w+)\s*\|"            # Perspektywa
    r"\s*(\w+)\s*\|"            # Tryb
    r"\s*(G\d)\s*\|"            # Prawo
    r"\s*(\w+)\s*\|"            # Triada
    r"\s*([\d.]+)\s*\|"         # Confidence
    r"\s*([\d.]+)\s*\|"         # Signal
    r"\s*([\w\-]+)\s*\|"        # Zrodlo
)

_PENDING_ROW_RE = re.compile(
    r"^\|\s*\d+\s*\|"
    r"\s*(.+?)\s*\|"            # Dokument
    r"\s*(G\d)\s*\|"            # Prawo
    r"\s*(\w+)\s*\|"            # Triada
    r"\s*([\d.]+)\s*\|"         # Confidence
    r"\s*([\d.]+)\s*\|"         # Signal
    r"\s*([\w_]+)\s*\|"         # Status
    r"\s*.+?\s*\|"              # Powod
)


def _parse_final_md(path: Path) -> tuple[list[FinalRow], list[PendingRow]]:
    final_rows: list[FinalRow] = []
    pending_rows: list[PendingRow] = []
    in_final = False
    in_pending = False

    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if "## Finalna mapa produkcyjna" in stripped:
                in_final = True
                in_pending = False
                continue
            if "## Pozycje PENDING" in stripped:
                in_final = False
                in_pending = True
                continue
            if stripped.startswith("## ") and stripped not in (
                "## Finalna mapa produkcyjna", "## Pozycje PENDING"
            ):
                in_final = False
                in_pending = False

            if in_final:
                m = _FINAL_ROW_RE.match(line)
                if m:
                    doc, persp, tryb, prawo, triada, conf_s, sig_s, source = m.groups()
                    final_rows.append(FinalRow(
                        filename=doc.strip(),
                        perspektywa=persp.strip(),
                        tryb=tryb.strip(),
                        prawo=prawo.strip(),
                        triada=triada.strip(),
                        confidence=float(conf_s),
                        signal=float(sig_s),
                        source=source.strip(),
                    ))

            if in_pending:
                m = _PENDING_ROW_RE.match(line)
                if m:
                    doc, prawo, triada, _conf, _sig, status = m.groups()
                    pending_rows.append(PendingRow(
                        filename=doc.strip(),
                        prawo=prawo.strip(),
                        triada=triada.strip(),
                        status=status.strip(),
                    ))

    return final_rows, pending_rows


# Załaduj dane raz na moduł
_FINAL_ROWS, _PENDING_ROWS = _parse_final_md(FINAL_MD)


def _find_row(fragment: str) -> FinalRow | None:
    """Szuka pierwszego FINAL row pasującego do fragmentu nazwy (case-insensitive)."""
    frag_lower = fragment.lower()
    for row in _FINAL_ROWS:
        if frag_lower in row.filename.lower():
            return row
    return None


def _normalize_text(value: str) -> str:
    """Normalizuje tekst do porownan odpornych na diakrytyki i case."""
    decomposed = unicodedata.normalize("NFKD", value)
    no_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return no_marks.casefold().strip()


def _find_row_by_filename(filename: str) -> FinalRow | None:
    """Znajduje FINAL row po nazwie pliku z fallbackiem na porownanie znormalizowane."""
    target = _normalize_text(filename)
    for row in _FINAL_ROWS:
        if _normalize_text(row.filename) == target:
            return row
    for row in _FINAL_ROWS:
        if target in _normalize_text(row.filename) or _normalize_text(row.filename) in target:
            return row
    return None


def _parse_checklist_expected_sources(path: Path) -> dict[str, str]:
    """Zwraca mapowanie {filename: expected_source} dla pozycji REVIEW z checklisty."""
    text = path.read_text(encoding="utf-8")
    result: dict[str, str] = {}
    sections = re.split(r"\n###\s+\d+\.\s+", text)
    for section in sections[1:]:
        lines = [line.strip() for line in section.splitlines() if line.strip()]
        if not lines:
            continue
        filename = lines[0]
        status_line = ""
        for line in lines:
            if line.startswith("- Status:"):
                status_line = line
                break
        if "APPROVED-WSTEPNIE" in status_line:
            result[filename] = "PRE-APPROVED"
        elif "APPROVED-MODEL-SUGGESTED" in status_line:
            result[filename] = "MODEL-SUGGESTED"
    return result


# ---------------------------------------------------------------------------
# Testy FINAL
# ---------------------------------------------------------------------------

class TestFinalCount:
    def test_total_final_entries(self) -> None:
        """Dokładnie 17 pozycji powinno mieć status FINAL."""
        assert len(_FINAL_ROWS) == 17, (
            f"Oczekiwano 17 pozycji FINAL, znaleziono {len(_FINAL_ROWS)}. "
            "Uruchom merge_jednosc_decisions.py po uzupełnieniu checklisty."
        )

    def test_total_pending_entries(self) -> None:
        """Po pełnym merge nie powinno być pozycji PENDING."""
        assert len(_PENDING_ROWS) == 0, (
            f"Oczekiwano 0 pozycji PENDING, znaleziono {len(_PENDING_ROWS)}."
        )


class TestTriadDistribution:
    def test_unity_count(self) -> None:
        unity = sum(1 for r in _FINAL_ROWS if r.triada == "Unity")
        assert unity == 8, f"Oczekiwano 8 pozycji Unity, znaleziono {unity}"

    def test_truth_count(self) -> None:
        truth = sum(1 for r in _FINAL_ROWS if r.triada == "Truth")
        assert truth == 5, f"Oczekiwano 5 pozycji Truth, znaleziono {truth}"

    def test_goodness_count(self) -> None:
        goodness = sum(1 for r in _FINAL_ROWS if r.triada == "Goodness")
        assert goodness == 4, f"Oczekiwano 4 pozycji Goodness, znaleziono {goodness}"

    def test_no_unknown_triads(self) -> None:
        known = {"Unity", "Truth", "Goodness"}
        unknown = {r.triada for r in _FINAL_ROWS} - known
        assert not unknown, f"Nieznane triady w FINAL: {unknown}"


class TestSourceDistribution:
    def test_auto_approved_count(self) -> None:
        n = sum(1 for r in _FINAL_ROWS if r.source == "AUTO-APPROVED")
        assert n == 11, f"Oczekiwano 11 AUTO-APPROVED, znaleziono {n}"

    def test_pre_approved_count(self) -> None:
        n = sum(1 for r in _FINAL_ROWS if r.source == "PRE-APPROVED")
        assert n == 2, f"Oczekiwano 2 PRE-APPROVED, znaleziono {n}"

    def test_model_suggested_count(self) -> None:
        n = sum(1 for r in _FINAL_ROWS if r.source == "MODEL-SUGGESTED")
        assert n == 4, f"Oczekiwano 4 MODEL-SUGGESTED, znaleziono {n}"

    def test_no_unresolved_in_final(self) -> None:
        unresolved = [r for r in _FINAL_ROWS if r.source == "UNRESOLVED"]
        assert not unresolved, (
            f"Pozycje UNRESOLVED nie powinny trafić do tabeli FINAL: "
            f"{[r.filename for r in unresolved]}"
        )


class TestChecklistSourceConsistency:
    def test_checklist_review_entries_mapped(self) -> None:
        expected = _parse_checklist_expected_sources(CHECKLIST_MD)
        assert len(expected) == 6, (
            f"Oczekiwano 6 pozycji REVIEW w checkliscie, znaleziono {len(expected)}"
        )

    def test_review_sources_match_checklist_status(self) -> None:
        expected = _parse_checklist_expected_sources(CHECKLIST_MD)
        mismatches: list[str] = []
        missing: list[str] = []

        for filename, expected_source in expected.items():
            row = _find_row_by_filename(filename)
            if row is None:
                missing.append(filename)
                continue
            if row.source != expected_source:
                mismatches.append(
                    f"{filename}: oczekiwano {expected_source}, znaleziono {row.source}"
                )

        assert not missing, (
            "Brak pozycji z checklisty w FINAL: " + "; ".join(missing)
        )
        assert not mismatches, (
            "Niespojne source FINAL vs checklist: " + "; ".join(mismatches)
        )


class TestConfidenceBounds:
    def test_all_confidence_between_0_and_1(self) -> None:
        for r in _FINAL_ROWS:
            assert 0.0 <= r.confidence <= 1.0, (
                f"{r.filename}: confidence={r.confidence} poza zakresem [0,1]"
            )

    def test_auto_approved_min_confidence(self) -> None:
        """AUTO-APPROVED powinny mieć confidence >= 0.76 lub signal >= 11.0."""
        for r in _FINAL_ROWS:
            if r.source == "AUTO-APPROVED":
                valid = r.confidence >= 0.76 or r.signal >= 11.0
                assert valid, (
                    f"{r.filename}: AUTO-APPROVED ale confidence={r.confidence}, "
                    f"signal={r.signal} — obie wartości poniżej progów."
                )


# ---------------------------------------------------------------------------
# Testy indywidualne — zamrożone asercje (13 pozycji)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fragment,expected_law,expected_triad", [
    e for e in EXPECTED_FINAL if "Projekt Gminy Jedno" not in e[0]
])
def test_final_law_and_triad(fragment: str, expected_law: str, expected_triad: str) -> None:
    """Każda FINAL pozycja musi utrzymać zamrożone prawo i triadę."""
    row = _find_row(fragment)
    assert row is not None, (
        f"Nie znaleziono pozycji pasującej do fragmentu '{fragment}' w FINAL.md. "
        "Sprawdź czy merge_jednosc_decisions.py nie zmienił nazwy pozycji."
    )
    assert row.prawo == expected_law, (
        f"REGRESJA KLASYFIKACJI: '{row.filename}'\n"
        f"  Oczekiwano prawo: {expected_law}\n"
        f"  Znaleziono:       {row.prawo}"
    )
    assert row.triada == expected_triad, (
        f"REGRESJA KLASYFIKACJI: '{row.filename}'\n"
        f"  Oczekiwano triadę: {expected_triad}\n"
        f"  Znaleziono:        {row.triada}"
    )


def test_projekt_gminy_both_variants_g9_goodness() -> None:
    """Oba warianty 'Projekt Gminy Jedności_ Wizja Przyszłości' mają G9/Goodness."""
    matching = [r for r in _FINAL_ROWS if "Wizja Przysz" in r.filename]
    assert len(matching) == 2, (
        f"Oczekiwano 2 wariantów 'Wizja Przyszłości', znaleziono {len(matching)}: "
        f"{[r.filename for r in matching]}"
    )
    for row in matching:
        assert row.prawo == "G9", (
            f"REGRESJA: '{row.filename}' — oczekiwano G9, znaleziono {row.prawo}"
        )
        assert row.triada == "Goodness", (
            f"REGRESJA: '{row.filename}' — oczekiwano Goodness, znaleziono {row.triada}"
        )


class TestProductionState:
    def test_has_production_status_banner(self) -> None:
        content = FINAL_MD.read_text(encoding="utf-8")
        assert "STATUS PRODUKCYJNY" in content, (
            "Brak banneru STATUS PRODUKCYJNY w JEDNOSC_162D_FINAL.md"
        )
