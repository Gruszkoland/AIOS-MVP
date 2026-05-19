from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_BASE_DIR = Path(
    r"C:\Users\adiha\162 demencje w schemacie 369\Genesis Record\10_RAPORTY_DZIALANIA_SYSTEMU"
)
LAST_SESSION_FILENAME = ".session_reports_last.txt"


@dataclass(frozen=True)
class SessionNames:
    title: str   # Title_Case_Topic
    date_str: str  # DD-MM-YYYY

    @property
    def filename(self) -> str:
        return f"{self.title}_{self.date_str}.md"


_PL_NORMALIZE: dict[int, str] = str.maketrans(
    "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ",
    "acelnoszzACELNOSZZ",
)


def title_underscore(text: str) -> str:
    """Convert topic text to ASCII Title_Case with underscores.

    Normalizes Polish diacritics before building the name so the
    resulting filename is safe on all OS and filesystems.

    Example: 'Optymalizacja Silnika Arbitrażu'
             -> 'Optymalizacja_Silnika_Arbitrazu'
    """
    value = text.strip().translate(_PL_NORMALIZE)
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    words = [w.capitalize() for w in value.split() if w]
    return "_".join(words) or "Chat_Session"


def build_names(topic: str) -> SessionNames:
    title = title_underscore(topic)
    now = datetime.now()
    date_str = now.strftime("%d-%m-%Y")
    return SessionNames(title=title, date_str=date_str)


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.write_text(content, encoding="utf-8")
    return True


def plan_template(topic: str, names: SessionNames) -> str:
    return f"""# Plan dzialania: {topic}

## Metadane
- data: {datetime.now().isoformat(timespec='seconds')}
- temat: {names.title}
- status-globalny: planned

## Cel glowny
- [Uzupelnij cel glowny]

## Kroki wykonawcze
1. nazwa-kroku: [Uzupelnij]
   cel-kroku: [Uzupelnij]
   kryterium-ukonczenia: [Uzupelnij]
   zaleznosci: [Uzupelnij albo brak]
   priorytet: [high|medium|low]
   status: planned

## Uwagi
- [Uzupelnij]
"""


def progress_template(topic: str, names: SessionNames) -> str:
    return f"""# Dziennik postepu: {topic}

## Metadane
- data-start: {datetime.now().isoformat(timespec='seconds')}
- temat: {names.title}
- status-globalny: in-progress

## Wpisy dzialan (append-only)
- {datetime.now().isoformat(timespec='seconds')} | in-progress | Inicjalizacja dziennika po zaplanowaniu krokow.

## Stan krokow
- [ ] krok-1
- [ ] krok-2
- [ ] krok-3
"""


def report_template(topic: str, names: SessionNames) -> str:
    return f"""# Raport koncowy: {topic}

## Metadane
- data-utworzenia: {datetime.now().isoformat(timespec='seconds')}
- temat: {names.title}
- status-globalny: draft

## Co wykonano
- [Uzupelnij]

## Co pozostalo
- [Uzupelnij]

## Co blokuje
- [Uzupelnij albo brak]

## Uzyskane efekty
- [Uzupelnij]

## Rekomendacje kolejnych krokow
- [Uzupelnij]

## Mikro-streszczenie
- [trzy slowa tutaj]
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Create PLAN/PROGRESS/REPORTS session files.")
    parser.add_argument("--topic", required=True, help="Session topic used for slug generation")
    parser.add_argument(
        "--base-dir",
        default=str(DEFAULT_BASE_DIR),
        help="Base path containing PLAN/PROGRESS/REPORTS directories",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    plan_dir = base_dir / "PLAN"
    progress_dir = base_dir / "PROGRESS"
    reports_dir = base_dir / "REPORTS"

    for folder in (plan_dir, progress_dir, reports_dir):
        folder.mkdir(parents=True, exist_ok=True)

    names = build_names(args.topic)
    filename = names.filename

    created = {
        "PLAN": write_if_missing(plan_dir / filename, plan_template(args.topic, names)),
        "PROGRESS": write_if_missing(progress_dir / filename, progress_template(args.topic, names)),
        "REPORTS": write_if_missing(reports_dir / filename, report_template(args.topic, names)),
    }

    (base_dir / LAST_SESSION_FILENAME).write_text(filename + "\n", encoding="utf-8")

    print(f"filename={filename}")
    for area, state in created.items():
        print(f"{area}: {'CREATED' if state else 'EXISTS'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
