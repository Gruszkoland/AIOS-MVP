from __future__ import annotations

import argparse
import html
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from zipfile import ZipFile
import xml.etree.ElementTree as ET


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

PERSPECTIVE_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "Material": (
        "zasob", "zasobow", "region", "gmina", "siec", "architektura", "obrona",
        "infrastr", "fizycz", "operac", "wdrozen", "wezel",
    ),
    "Intellectual": (
        "raport", "analiza", "symulacja", "test", "model", "mapowan", "logika",
        "protokol", "strategie", "wektor", "decyzj", "causality", "metryk",
    ),
    "Essential": (
        "jednosc", "amnestia", "przebaczenia", "swiadom", "negentrop", "koherenc",
        "harmon", "moral", "etyk", "misj", "praw", "transcend",
    ),
}

MODE_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "Inventory": ("inwentaryz", "stan", "diagno", "zasob", "raport", "metryk"),
    "Empathy": ("przebaczenia", "empati", "wspol", "spolecz", "amnestia", "uzdrow"),
    "Process": ("protokol", "proces", "wdrozen", "operac", "architektura", "workflow"),
    "Debate": ("debat", "argument", "weryfik", "test", "analiza", "porownan"),
    "Healing": ("uzdrow", "negentrop", "homeost", "rekultyw", "resilience", "stabiliz"),
    "Action": ("akcj", "dzialan", "obrona", "start", "urucham", "wykonan"),
}

LAW_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "G1": ("jednosc", "wspol", "collective"),
    "G2": ("harmon", "equilibrium", "rownowag"),
    "G3": ("rytm", "cycle", "cykl", "proces"),
    "G4": ("causality", "przyczyn", "uzasad", "logik"),
    "G5": ("transparent", "jasn", "report", "raport"),
    "G6": ("autenty", "zrodl", "weryfik", "karta", "praw"),
    "G7": ("privacy", "prywat", "sekret", "dane"),
    "G8": ("nonmalef", "bezpiec", "obrona", "ochron", "atak"),
    "G9": ("sustain", "trwal", "zrownowaz", "negentrop", "stabil"),
}

TRIAD_WEIGHTS: Dict[str, float] = {
    "Unity": 1.00,
    "Truth": 1.20,
    "Goodness": 1.30,
}

FILENAME_LAW_BONUS: Dict[str, Tuple[str, Tuple[str, ...], float]] = {
    "raport": ("G5", ("raport", "report"), 2.0),
    "protokol": ("G6", ("protokol", "weryfik", "auth"), 1.2),
    "zabezpieczenie": ("G8", ("zabezpieczenie", "obrona", "ochrona"), 2.0),
    "obrony": ("G8", ("obrona", "obrony", "ochron"), 1.5),
    "negentrop": ("G9", ("negentrop", "stabil", "sustain"), 1.5),
    "karta praw": ("G6", ("karta", "praw", "source"), 1.2),
}

TRIAD_FOR_LAW = {
    "G1": "Unity", "G2": "Unity", "G3": "Unity",
    "G4": "Truth", "G5": "Truth", "G6": "Truth",
    "G7": "Goodness", "G8": "Goodness", "G9": "Goodness",
}

REVIEW_CONFIDENCE_THRESHOLD = 0.76
REVIEW_SIGNAL_THRESHOLD = 11.0
AUTO_APPROVE_KEEP_CONFIDENCE = 0.74
AUTO_APPROVE_KEEP_SIGNAL = 11.0


@dataclass
class MappingResult:
    file_path: Path
    perspective: str
    mode: str
    law: str
    triad: str
    confidence: float
    signal: float
    rationale: str
    review_tag: str


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


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_\-]{3,}", text.lower())


def score_by_keywords(tokens: List[str], keyword_map: Dict[str, Tuple[str, ...]]) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    for key, kws in keyword_map.items():
        score = 0.0
        for kw in kws:
            score += float(sum(1 for tok in tokens if kw in tok))
        scores[key] = score
    return scores


def pick_top(scores: Dict[str, float], default_key: str) -> Tuple[str, float]:
    best_key = default_key
    best_val = -1.0
    for key, value in scores.items():
        if value > best_val:
            best_key = key
            best_val = value
    if best_val < 0:
        return default_key, 0.0
    return best_key, best_val


def apply_law_calibration(law_scores: Dict[str, float], file_name: str, tokens: List[str]) -> Dict[str, float]:
    calibrated = dict(law_scores)

    for law, score in law_scores.items():
        triad = TRIAD_FOR_LAW[law]
        calibrated[law] = score * TRIAD_WEIGHTS[triad]

    lowered_name = file_name.lower()
    token_blob = " ".join(tokens)
    for key, (target_law, kws, bonus) in FILENAME_LAW_BONUS.items():
        if key in lowered_name:
            calibrated[target_law] += bonus
            for kw in kws:
                if kw in token_blob:
                    calibrated[target_law] += 0.5

    return calibrated


def compute_mapping(file_path: Path, paragraphs: List[str]) -> MappingResult:
    sample_text = " ".join(paragraphs[:12])
    tokens = tokenize(sample_text + " " + file_path.name)

    perspective_scores = score_by_keywords(tokens, PERSPECTIVE_KEYWORDS)
    mode_scores = score_by_keywords(tokens, MODE_KEYWORDS)
    law_scores_raw = score_by_keywords(tokens, LAW_KEYWORDS)
    law_scores = apply_law_calibration(law_scores_raw, file_path.name, tokens)

    perspective, p_score = pick_top(perspective_scores, "Intellectual")
    mode, m_score = pick_top(mode_scores, "Process")
    law, l_score = pick_top(law_scores, "G5")
    triad = TRIAD_FOR_LAW[law]

    sorted_law_scores = sorted(law_scores.values(), reverse=True)
    law_margin = 0.0
    if len(sorted_law_scores) >= 2:
        law_margin = sorted_law_scores[0] - sorted_law_scores[1]

    total_signal = p_score + m_score + l_score
    confidence = 0.40
    if total_signal > 0:
        confidence = min(0.97, 0.42 + (total_signal / 42.0) + min(0.15, law_margin / 10.0))

    top_words = [w for w, _ in Counter(tokens).most_common(6)]
    rationale = ", ".join(top_words)

    needs_review = confidence < REVIEW_CONFIDENCE_THRESHOLD or total_signal < REVIEW_SIGNAL_THRESHOLD
    review_tag = "REVIEW" if needs_review else "OK"

    return MappingResult(
        file_path=file_path,
        perspective=perspective,
        mode=mode,
        law=law,
        triad=triad,
        confidence=round(confidence, 2),
        signal=round(total_signal, 2),
        rationale=rationale,
        review_tag=review_tag,
    )


def rel_link(root: Path, file_path: Path) -> str:
    rel = file_path.relative_to(root)
    target = str(rel).replace("\\", "/")
    return f"[{file_path.name}]({target.replace(' ', '%20')})"


def build_markdown(results: List[MappingResult], output_path: Path) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines: List[str] = []
    lines.append("# JEDNOSC 162D MAP")
    lines.append("")
    lines.append(f"Data generacji: {now}")
    lines.append("Wersja klasyfikatora: v2 (triad weighting + filename bonus)")
    lines.append("Zakres: mapowanie dokumentow Jednosc_Source do perspektyw, trybow i praw Guardian.")
    lines.append("")
    lines.append("## Tabela mapowania")
    lines.append("")
    lines.append("| # | Dokument | Perspektywa | Tryb | Prawo | Triada | Confidence | Signal | Review | Uzasadnienie (tokeny) |")
    lines.append("|---:|---|---|---|---|---|---:|---:|---|---|")

    for index, result in enumerate(results, start=1):
        link = rel_link(output_path.parent, result.file_path)
        lines.append(
            f"| {index} | {link} | {result.perspective} | {result.mode} | {result.law} | {result.triad} | {result.confidence:.2f} | {result.signal:.2f} | {result.review_tag} | {result.rationale} |"
        )

    triad_counts = Counter(result.triad for result in results)
    lines.append("")
    lines.append("## Rozklad triad")
    lines.append("")
    for triad in ("Unity", "Truth", "Goodness"):
        lines.append(f"- {triad}: {triad_counts.get(triad, 0)}")

    review_count = sum(1 for result in results if result.review_tag == "REVIEW")
    lines.append(f"- REVIEW flagged: {review_count}")

    lines.append("")
    lines.append("## Pozycje do recznej walidacji")
    lines.append("")
    review_results = [result for result in results if result.review_tag == "REVIEW"]
    if not review_results:
        lines.append("- Brak pozycji REVIEW.")
    else:
        for result in review_results:
            lines.append(
                f"- {result.file_path.name}: confidence={result.confidence:.2f}, signal={result.signal:.2f}, triada={result.triad}"
            )

    lines.append("")
    lines.append("## Notatka")
    lines.append("")
    lines.append("- Klasyfikacja jest heurystyczna i oparta o slowa kluczowe, nazwe pliku i wazenie triad.")
    lines.append(
        f"- Etykieta REVIEW gdy confidence < {REVIEW_CONFIDENCE_THRESHOLD:.2f} lub signal < {REVIEW_SIGNAL_THRESHOLD:.1f}."
    )

    return "\n".join(lines)


def build_approved_markdown(results: List[MappingResult], output_path: Path) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    approved = [result for result in results if result.review_tag == "OK"]

    lines: List[str] = []
    lines.append("# JEDNOSC 162D APPROVED")
    lines.append("")
    lines.append(f"Data generacji: {now}")
    lines.append(f"Liczba pozycji OK: {len(approved)}")
    lines.append("")
    lines.append("## Lista zatwierdzona")
    lines.append("")
    lines.append("| # | Dokument | Perspektywa | Tryb | Prawo | Triada | Confidence | Signal |")
    lines.append("|---:|---|---|---|---|---|---:|---:|")

    for index, result in enumerate(approved, start=1):
        link = rel_link(output_path.parent, result.file_path)
        lines.append(
            f"| {index} | {link} | {result.perspective} | {result.mode} | {result.law} | {result.triad} | {result.confidence:.2f} | {result.signal:.2f} |"
        )

    return "\n".join(lines)


def build_review_backlog_markdown(results: List[MappingResult], output_path: Path) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    review = [result for result in results if result.review_tag == "REVIEW"]

    lines: List[str] = []
    lines.append("# JEDNOSC 162D REVIEW BACKLOG")
    lines.append("")
    lines.append(f"Data generacji: {now}")
    lines.append(f"Liczba pozycji REVIEW: {len(review)}")
    lines.append("")
    lines.append("## Kolejka walidacji")
    lines.append("")
    lines.append("| # | Dokument | Obecna triada | Confidence | Signal | Priorytet | Zalecane dzialanie |")
    lines.append("|---:|---|---|---:|---:|---|---|")

    def priority_for(result: MappingResult) -> str:
        if result.confidence < 0.70 or result.signal < 9.0:
            return "HIGH"
        if result.confidence < 0.76 or result.signal < 11.0:
            return "MED"
        return "LOW"

    for index, result in enumerate(review, start=1):
        link = rel_link(output_path.parent, result.file_path)
        priority = priority_for(result)
        lines.append(
            f"| {index} | {link} | {result.triad} | {result.confidence:.2f} | {result.signal:.2f} | {priority} | Ręczna weryfikacja prawa i triady |"
        )

    lines.append("")
    lines.append("## Kryteria")
    lines.append("")
    lines.append(
        f"- REVIEW gdy confidence < {REVIEW_CONFIDENCE_THRESHOLD:.2f} lub signal < {REVIEW_SIGNAL_THRESHOLD:.1f}."
    )

    return "\n".join(lines)


def build_review_checklist_markdown(results: List[MappingResult]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    review = [result for result in results if result.review_tag == "REVIEW"]

    lines: List[str] = []
    lines.append("# JEDNOSC 162D REVIEW CHECKLIST")
    lines.append("")
    lines.append(f"Data generacji: {now}")
    lines.append(f"Liczba pozycji REVIEW: {len(review)}")
    lines.append("")
    lines.append("## Instrukcja")
    lines.append("")
    lines.append("- Uzupełnij decyzję dla każdej pozycji: KEEP lub CHANGE.")
    lines.append("- Jeśli CHANGE: wpisz docelowe prawo i triadę.")
    lines.append("- Uzupełnij uzasadnienie i ustaw status na APPROVED po zatwierdzeniu.")
    lines.append("")
    lines.append("## Decyzje eksperckie")
    lines.append("")

    def recommendation_for(result: MappingResult) -> Tuple[str, str, str, str]:
        name = result.file_path.name.lower()

        # Default recommendation based on model confidence/signal.
        if result.confidence < 0.70 or result.signal < 9.0:
            decision = "CHANGE"
        else:
            decision = "KEEP"

        suggested_law = result.law
        suggested_triad = result.triad

        # File-name heuristics for stronger directional hints.
        if "raport" in name:
            suggested_law, suggested_triad = "G5", "Truth"
        elif "zabezpieczenie" in name or "obron" in name:
            suggested_law, suggested_triad = "G8", "Goodness"
        elif "negentrop" in name:
            suggested_law, suggested_triad = "G9", "Goodness"
        elif "protok" in name:
            suggested_law, suggested_triad = "G6", "Truth"

        confidence_note = (
            f"confidence={result.confidence:.2f}, signal={result.signal:.2f}, "
            f"obecnie={result.law}/{result.triad}"
        )
        return decision, suggested_law, suggested_triad, confidence_note

    if not review:
        lines.append("- Brak pozycji REVIEW do decyzji.")
        return "\n".join(lines)

    for index, result in enumerate(review, start=1):
        rec_decision, rec_law, rec_triad, rec_note = recommendation_for(result)
        pre_approved = (
            rec_decision == "KEEP"
            and result.confidence >= AUTO_APPROVE_KEEP_CONFIDENCE
            and result.signal >= AUTO_APPROVE_KEEP_SIGNAL
        )

        if pre_approved:
            decision_line = "- Decyzja eksperta: [x] KEEP  [ ] CHANGE"
            status_line = "- Status: [x] APPROVED-WSTEPNIE"
        elif rec_decision == "CHANGE":
            decision_line = "- Decyzja eksperta: [ ] KEEP  [x] CHANGE"
            status_line = "- Status: [ ] APPROVED"
        else:
            decision_line = "- Decyzja eksperta: [ ] KEEP  [ ] CHANGE"
            status_line = "- Status: [ ] APPROVED"

        lines.append(f"### {index}. {result.file_path.name}")
        lines.append("")
        lines.append(f"- Obecna klasyfikacja: {result.law} / {result.triad}")
        lines.append(f"- Confidence: {result.confidence:.2f}")
        lines.append(f"- Signal: {result.signal:.2f}")
        lines.append(f"- Uzasadnienie modelu: {result.rationale}")
        lines.append(f"- Rekomendacja automatyczna: {rec_decision}")
        lines.append(f"- Sugerowane prawo docelowe: {rec_law}")
        lines.append(f"- Sugerowana triada docelowa: {rec_triad}")
        lines.append(f"- Notatka rekomendacji: {rec_note}")
        lines.append(decision_line)
        lines.append("- Prawo docelowe (jesli CHANGE):")
        lines.append("- Triada docelowa (jesli CHANGE):")
        lines.append("- Uzasadnienie decyzji:")
        lines.append(status_line)
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Map Jednosc DOCX documents to 162D dimensions")
    parser.add_argument("--source-dir", default="docs/Jednosc_Source", help="Directory with source docs")
    parser.add_argument("--output", default="docs/JEDNOSC_162D_MAP.md", help="Output markdown path")
    parser.add_argument(
        "--approved-output",
        default="docs/JEDNOSC_162D_APPROVED.md",
        help="Output markdown path for approved (OK) items",
    )
    parser.add_argument(
        "--review-output",
        default="docs/JEDNOSC_162D_REVIEW_BACKLOG.md",
        help="Output markdown path for review backlog items",
    )
    parser.add_argument(
        "--checklist-output",
        default="docs/JEDNOSC_162D_REVIEW_CHECKLIST.md",
        help="Output markdown path for review decision checklist",
    )
    parser.add_argument(
        "--pending-output",
        default="docs/JEDNOSC_162D_REVIEW_PENDING.md",
        help="Output markdown path for still-pending manual decisions",
    )
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    output = Path(args.output)
    approved_output = Path(args.approved_output)
    review_output = Path(args.review_output)
    checklist_output = Path(args.checklist_output)
    pending_output = Path(args.pending_output)

    files = sorted(source_dir.rglob("*.docx"), key=lambda path: str(path).lower())
    results: List[MappingResult] = []
    for file_path in files:
        paragraphs = extract_paragraphs(file_path)
        results.append(compute_mapping(file_path, paragraphs))

    markdown = build_markdown(results, output)
    approved_markdown = build_approved_markdown(results, approved_output)
    review_markdown = build_review_backlog_markdown(results, review_output)
    checklist_markdown = build_review_checklist_markdown(results)

    pending_lines: List[str] = []
    pending_lines.append("# JEDNOSC 162D REVIEW PENDING")
    pending_lines.append("")
    pending_lines.append(f"Data generacji: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    pending_lines.append("")
    pending_lines.append("## Pozycje wymagajace decyzji recznej")
    pending_lines.append("")
    pending_lines.append("| # | Dokument | Rekomendacja | Confidence | Signal |")
    pending_lines.append("|---:|---|---|---:|---:|")

    pending = []
    for result in results:
        if result.review_tag != "REVIEW":
            continue
        rec_decision = "CHANGE" if (result.confidence < 0.70 or result.signal < 9.0) else "KEEP"
        pre_approved = (
            rec_decision == "KEEP"
            and result.confidence >= AUTO_APPROVE_KEEP_CONFIDENCE
            and result.signal >= AUTO_APPROVE_KEEP_SIGNAL
        )
        if pre_approved:
            continue
        pending.append((result, rec_decision))

    for index, (result, rec_decision) in enumerate(pending, start=1):
        link = rel_link(pending_output.parent, result.file_path)
        pending_lines.append(
            f"| {index} | {link} | {rec_decision} | {result.confidence:.2f} | {result.signal:.2f} |"
        )

    if not pending:
        pending_lines.append("| 1 | Brak | - | - | - |")

    pending_markdown = "\n".join(pending_lines)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    approved_output.parent.mkdir(parents=True, exist_ok=True)
    approved_output.write_text(approved_markdown, encoding="utf-8")
    review_output.parent.mkdir(parents=True, exist_ok=True)
    review_output.write_text(review_markdown, encoding="utf-8")
    checklist_output.parent.mkdir(parents=True, exist_ok=True)
    checklist_output.write_text(checklist_markdown, encoding="utf-8")
    pending_output.parent.mkdir(parents=True, exist_ok=True)
    pending_output.write_text(pending_markdown, encoding="utf-8")

    print(f"Map written: {output}")
    print(f"Approved written: {approved_output}")
    print(f"Review backlog written: {review_output}")
    print(f"Review checklist written: {checklist_output}")
    print(f"Review pending written: {pending_output}")
    print(f"Documents mapped: {len(results)}")


if __name__ == "__main__":
    main()
