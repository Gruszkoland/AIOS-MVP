from __future__ import annotations

import argparse
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


ALLOWED_SUFFIXES = {
    ".md",
    ".mdx",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".csv",
}

EXCLUDED_NAMES = {
    "KNOWLEDGE_HUB.md",
    "KNOWLEDGE_VISUALS.md",
    "THEMATIC_INDEX.md",
    "IMPORTANCE_INDEX.md",
}

THEMES: Dict[str, Tuple[str, Tuple[str, ...]]] = {
    "Architektura i infrastruktura": (
        "Platform, runtime, deployment, orchestration and system design.",
        (
            "architecture",
            "architektura",
            "infrastructure",
            "infrastrukt",
            "docker",
            "kubernetes",
            "deployment",
            "wdrozen",
            "orchestration",
            "workflow",
            "platform",
        ),
    ),
    "Bezpieczeństwo i zgodność": (
        "Security, threat modeling, auth, privacy and compliance artifacts.",
        (
            "security",
            "threat",
            "privacy",
            "oauth",
            "ssl",
            "rbac",
            "guardian",
            "secur",
            "auth",
            "cipher",
            "zabezpiec",
        ),
    ),
    "Monitorowanie i obserwowalność": (
        "Dashboards, metrics, logs, alerts and runtime health.",
        (
            "monitor",
            "observability",
            "dashboard",
            "metrics",
            "prometheus",
            "grafana",
            "loki",
            "alert",
            "health",
            "telemetry",
        ),
    ),
    "Wdrożenia i operacje": (
        "Runbooks, quick starts, production procedures and maintenance guides.",
        (
            "deploy",
            "deployment",
            "production",
            "runbook",
            "quickstart",
            "install",
            "setup",
            "maintenance",
            "operat",
            "start",
            "production",
        ),
    ),
    "AI i orkiestracja agentów": (
        "Agent frameworks, MCP, orchestration, reasoning and LLM tooling.",
        (
            "agent",
            "mcp",
            "foundry",
            "llm",
            "dspy",
            "trinity",
            "oracle",
            "swarm",
            "persona",
            "arbitrage",
            "orchestrator",
        ),
    ),
    "Wiedza i nawigacja": (
        "Indexes, maps, tables of contents and knowledge base entry points.",
        (
            "index",
            "map",
            "toc",
            "table of contents",
            "knowledge",
            "hub",
            "navigation",
            "readme",
            "starting here",
            "guide",
        ),
    ),
    "Jedność i 162D": (
        "The Jednosc source set, 162D decision space and guardian-law mapping.",
        (
            "jednosc",
            "162d",
            "guardian",
            "decision space",
            "laws",
            "triad",
            "truth",
            "goodness",
            "unity",
            "praw",
        ),
    ),
    "Testy i walidacja": (
        "Tests, regression checks, quality gates and verification artifacts.",
        (
            "test",
            "spec",
            "validation",
            "verify",
            "coverage",
            "lint",
            "qa",
            "quality",
            "auditor",
        ),
    ),
    "Dane, kopie i odtwarzanie": (
        "Databases, backups, restore procedures, archival and recovery.",
        (
            "database",
            "postgres",
            "sqlite",
            "backup",
            "restore",
            "archiv",
            "recovery",
            "dr",
            "data",
            "storage",
        ),
    ),
}

IMPORTANCE_KEYWORDS: Dict[str, float] = {
    "readme": 4.0,
    "index": 4.0,
    "hub": 3.5,
    "dashboard": 3.5,
    "architecture": 3.5,
    "architektura": 3.5,
    "security": 3.5,
    "threat": 3.0,
    "production": 3.0,
    "deploy": 3.0,
    "runbook": 3.0,
    "quickstart": 2.5,
    "workflow": 2.5,
    "guide": 2.5,
    "decision space": 3.5,
    "162d": 4.0,
    "jednosc": 4.0,
    "guardian": 3.0,
    "openapi": 2.5,
    "api schema": 2.5,
    "monitor": 2.5,
    "metrics": 2.5,
    "grafana": 2.5,
    "prometheus": 2.5,
    "backup": 2.5,
    "restore": 2.5,
    "test": 2.0,
    "validation": 2.0,
}


@dataclass(frozen=True)
class DocumentRecord:
    path: Path
    relative_path: Path
    title: str
    theme: str
    theme_score: float
    secondary_themes: Tuple[str, ...]
    importance_score: float
    importance_tier: str
    word_count: int
    link_count: int
    age_days: float
    size_kb: float
    signals: Tuple[str, ...]


def read_preview(path: Path, limit: int = 12000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except Exception:
        return ""


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_\-]{3,}", text.lower())


def normalize_text(path: Path, preview: str) -> str:
    return f"{path.as_posix().lower()}\n{preview.lower()}"


def iter_source_files(docs_root: Path) -> Iterable[Path]:
    for path in sorted(docs_root.rglob("*"), key=lambda item: str(item).lower()):
        if not path.is_file():
            continue
        if path.name in EXCLUDED_NAMES:
            continue
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            continue
        if ".git" in path.parts:
            continue
        yield path


def score_theme(text: str) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    for theme, (_, keywords) in THEMES.items():
        score = 0.0
        for keyword in keywords:
            score += float(text.count(keyword.lower()))
        scores[theme] = score
    return scores


def choose_theme(scores: Dict[str, float]) -> Tuple[str, float, Tuple[str, ...]]:
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0].lower()))
    if not ordered or ordered[0][1] <= 0:
        return "Wiedza i nawigacja", 0.0, tuple()

    top_theme, top_score = ordered[0]
    secondary = tuple(theme for theme, score in ordered[1:4] if score > 0 and score >= top_score * 0.45)
    return top_theme, top_score, secondary


def count_links(preview: str) -> int:
    return len(re.findall(r"\[[^\]]+\]\(([^)]+)\)", preview))


def count_words(preview: str) -> int:
    return len(tokenize(preview))


def classify_importance(path: Path, text: str, word_count: int, link_count: int) -> Tuple[float, str, Tuple[str, ...]]:
    lowered = normalize_text(path, text)
    score = 0.0
    signals: List[str] = []

    for keyword, bonus in IMPORTANCE_KEYWORDS.items():
        hits = lowered.count(keyword)
        if hits:
            contribution = bonus + min(2.0, hits * 0.25)
            score += contribution
            signals.append(f"{keyword}:{hits}")

    if path.name.lower().startswith(("readme", "index", "dashboard", "starting_here", "quickstart")):
        score += 2.5
        signals.append("hub-file")

    try:
        depth = max(0, len(path.relative_to(path.parents[1]).parts))
    except Exception:
        depth = len(path.parts)
    if depth <= 2:
        score += 0.75
        signals.append("shallow-path")

    size_bonus = min(2.5, math.log10(max(10, word_count)) * 0.9)
    link_bonus = min(2.5, link_count * 0.35)
    freshness_days = max(0.0, (datetime.now().timestamp() - path.stat().st_mtime) / 86400.0)
    freshness_bonus = 1.25 if freshness_days <= 14 else 0.75 if freshness_days <= 90 else 0.0

    score += size_bonus + link_bonus + freshness_bonus
    signals.append(f"size:{word_count}")
    signals.append(f"links:{link_count}")
    signals.append(f"fresh:{int(freshness_days)}d")

    if score >= 10.0:
        tier = "Critical"
    elif score >= 7.0:
        tier = "High"
    elif score >= 4.5:
        tier = "Medium"
    else:
        tier = "Low"

    return round(score, 2), tier, tuple(signals[:8])


def relative_link(docs_root: Path, path: Path) -> str:
    rel = path.relative_to(docs_root).as_posix().replace(" ", "%20")
    title = path.name.replace(".md", "")
    return f"[{title}]({rel})"


def rank_documents(docs_root: Path) -> List[DocumentRecord]:
    records: List[DocumentRecord] = []

    for path in iter_source_files(docs_root):
        preview = read_preview(path)
        normalized = normalize_text(path, preview)
        theme_scores = score_theme(normalized)
        theme, theme_score, secondary = choose_theme(theme_scores)
        word_count = count_words(preview)
        link_count = count_links(preview)
        importance_score, importance_tier, signals = classify_importance(path, preview, word_count, link_count)
        try:
            stat = path.stat()
            age_days = max(0.0, (datetime.now().timestamp() - stat.st_mtime) / 86400.0)
            size_kb = round(stat.st_size / 1024.0, 2)
        except Exception:
            age_days = 0.0
            size_kb = 0.0

        records.append(
            DocumentRecord(
                path=path,
                relative_path=path.relative_to(docs_root),
                title=path.stem,
                theme=theme,
                theme_score=theme_score,
                secondary_themes=secondary,
                importance_score=importance_score,
                importance_tier=importance_tier,
                word_count=word_count,
                link_count=link_count,
                age_days=round(age_days, 1),
                size_kb=size_kb,
                signals=signals,
            )
        )

    return records


def sort_key(record: DocumentRecord) -> Tuple[float, float, float, str]:
    return (-record.importance_score, -record.theme_score, -record.word_count, record.relative_path.as_posix().lower())


def select_top(records: Sequence[DocumentRecord], limit: int = 10) -> List[DocumentRecord]:
    return sorted(records, key=sort_key)[:limit]


def render_theme_pie(theme_counts: Counter[str]) -> str:
    top_items = theme_counts.most_common(7)
    other = sum(theme_counts.values()) - sum(count for _, count in top_items)
    lines = ["pie title Top themes by document count"]
    for theme, count in top_items:
        lines.append(f'  "{theme}" : {count}')
    if other > 0:
        lines.append(f'  "Other" : {other}')
    return "\n".join(lines)


def render_importance_pie(tier_counts: Counter[str]) -> str:
    lines = ["pie title Importance tiers"]
    for tier in ("Critical", "High", "Medium", "Low"):
        lines.append(f'  "{tier}" : {tier_counts.get(tier, 0)}')
    return "\n".join(lines)


def build_visuals_md(records: Sequence[DocumentRecord], docs_root: Path) -> str:
    theme_counts = Counter(record.theme for record in records)
    tier_counts = Counter(record.importance_tier for record in records)

    top_themes = theme_counts.most_common(6)
    top_records = select_top(records, limit=8)

    lines: List[str] = []
    lines.append("# Knowledge Visuals")
    lines.append("")
    lines.append(f"Data wygenerowania: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Zakres: {len(records)} dokumentow w `docs/`.")
    lines.append("")
    lines.append("## Read order")
    lines.append("")
    lines.append("1. Otworz Knowledge Hub.")
    lines.append("2. Przejrzyj wykres tematow.")
    lines.append("3. Przejdz do mapy tematycznej lub indeksu ważnosci.")
    lines.append("")
    lines.append("## System map")
    lines.append("")
    lines.append("```mermaid")
    lines.append("flowchart TD")
    lines.append('  A[docs/ Knowledge Base] --> B[KNOWLEDGE_HUB.md]')
    lines.append('  B --> C[THEMATIC_INDEX.md]')
    lines.append('  B --> D[IMPORTANCE_INDEX.md]')
    lines.append('  B --> E[KNOWLEDGE_VISUALS.md]')
    for theme, count in top_themes:
        node = re.sub(r"[^A-Za-z0-9]+", "_", theme)
        lines.append(f'  C --> {node}[{theme} ({count})]')
    lines.append("```")
    lines.append("")
    lines.append("## Theme distribution")
    lines.append("")
    lines.append("```mermaid")
    lines.append(render_theme_pie(theme_counts))
    lines.append("```")
    lines.append("")
    lines.append("## Importance distribution")
    lines.append("")
    lines.append("```mermaid")
    lines.append(render_importance_pie(tier_counts))
    lines.append("```")
    lines.append("")
    lines.append("## Top visual hubs")
    lines.append("")
    lines.append("| Dokument | Temat | Importance | Linki | Słowa |")
    lines.append("|---|---|---:|---:|---:|")
    for record in top_records:
        lines.append(
            f"| {relative_link(docs_root, record.path)} | {record.theme} | {record.importance_tier} ({record.importance_score:.2f}) | {record.link_count} | {record.word_count} |"
        )
    lines.append("")
    lines.append("## Uwaga")
    lines.append("")
    lines.append("- Diagramy są generowane z heurystyk nazw plikow, sciezki i zawartosci tekstowej.")
    lines.append("- Mermaid flowchart jest bezpieczniejszy niz zewnetrzne wykresy i dziala dobrze w Obsidian.")
    return "\n".join(lines)


def build_thematic_index_md(records: Sequence[DocumentRecord], docs_root: Path) -> str:
    grouped: Dict[str, List[DocumentRecord]] = defaultdict(list)
    for record in records:
        grouped[record.theme].append(record)

    theme_counts = Counter(record.theme for record in records)
    lines: List[str] = []
    lines.append("# Thematic Index")
    lines.append("")
    lines.append(f"Data wygenerowania: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("Cel: mapowanie wedlug tematow, nie tylko projektow.")
    lines.append("")
    lines.append("## Theme summary")
    lines.append("")
    lines.append("| Temat | Dokumenty | Opis |")
    lines.append("|---|---:|---|")
    for theme, count in sorted(theme_counts.items(), key=lambda item: (-item[1], item[0].lower())):
        description = THEMES.get(theme, ("", tuple()))[0]
        lines.append(f"| {theme} | {count} | {description} |")

    lines.append("")
    lines.append("## Themes")
    lines.append("")
    for theme, items in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0].lower())):
        description = THEMES.get(theme, ("", tuple()))[0]
        lines.append(f"### {theme} ({len(items)})")
        lines.append("")
        lines.append(description)
        lines.append("")
        lines.append("| Dokument | Importance | Score | Secondary | Słowa | Linki |")
        lines.append("|---|---|---:|---|---:|---:|")
        for record in select_top(items, limit=12):
            secondary = ", ".join(record.secondary_themes) if record.secondary_themes else "-"
            lines.append(
                f"| {relative_link(docs_root, record.path)} | {record.importance_tier} | {record.importance_score:.2f} | {secondary} | {record.word_count} | {record.link_count} |"
            )
        if len(items) > 12:
            lines.append("")
            lines.append(f"- Pokazano 12 z {len(items)} dokumentow; reszta zostaje w rankingu ważnosci.")
        lines.append("")

    return "\n".join(lines)


def build_importance_index_md(records: Sequence[DocumentRecord], docs_root: Path) -> str:
    grouped: Dict[str, List[DocumentRecord]] = defaultdict(list)
    for record in records:
        grouped[record.importance_tier].append(record)

    tier_counts = Counter(record.importance_tier for record in records)
    lines: List[str] = []
    lines.append("# Importance Index")
    lines.append("")
    lines.append(f"Data wygenerowania: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("Cel: oddzielic dokumenty krytyczne od wspierajacych i archiwalnych.")
    lines.append("")
    lines.append("## Scoring model")
    lines.append("")
    lines.append("- Krytycznosc pochodzi z nazw, sciezek, liczby linkow, wielkosci i swiezosci.")
    lines.append("- Huby, indeksy, architecture, security i 162D dostaja najwyzszy priorytet.")
    lines.append("")
    lines.append("## Tier summary")
    lines.append("")
    lines.append("| Tier | Dokumenty |")
    lines.append("|---|---:|")
    for tier in ("Critical", "High", "Medium", "Low"):
        lines.append(f"| {tier} | {tier_counts.get(tier, 0)} |")

    lines.append("")
    lines.append("```mermaid")
    lines.append(render_importance_pie(tier_counts))
    lines.append("```")
    lines.append("")

    for tier in ("Critical", "High", "Medium", "Low"):
        items = grouped.get(tier, [])
        lines.append(f"### {tier} ({len(items)})")
        lines.append("")
        lines.append("| Dokument | Temat | Score | Sygnały |")
        lines.append("|---|---|---:|---|")
        for record in select_top(items, limit=15):
            signal = "; ".join(record.signals)
            lines.append(
                f"| {relative_link(docs_root, record.path)} | {record.theme} | {record.importance_score:.2f} | {signal} |"
            )
        if len(items) > 15:
            lines.append("")
            lines.append(f"- Pokazano 15 z {len(items)} dokumentow; reszta zostaje poza top listą.")
        lines.append("")

    return "\n".join(lines)


def build_hub_md(records: Sequence[DocumentRecord]) -> str:
    theme_counts = Counter(record.theme for record in records)
    tier_counts = Counter(record.importance_tier for record in records)
    top_themes = theme_counts.most_common(6)

    lines: List[str] = []
    lines.append("# Knowledge Hub")
    lines.append("")
    lines.append(f"Data wygenerowania: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("Centralny punkt wejscia do wizualizacji, map tematycznych i rankingu ważnosci.")
    lines.append("")
    lines.append("## Start here")
    lines.append("")
    lines.append("1. [Knowledge Visuals](KNOWLEDGE_VISUALS.md)")
    lines.append("2. [Thematic Index](THEMATIC_INDEX.md)")
    lines.append("3. [Importance Index](IMPORTANCE_INDEX.md)")
    lines.append("")
    lines.append("## Existing hubs")
    lines.append("")
    lines.append("- [JEDNOSC_INDEX.md](JEDNOSC_INDEX.md)")
    lines.append("- [TOOLING-MATRIX-Maps.md](TOOLING-MATRIX-Maps.md)")
    lines.append("- [162D-DECISION-SPACE.md](162D-DECISION-SPACE.md)")
    lines.append("- [WORKFLOW.md](WORKFLOW.md)")
    lines.append("")
    lines.append("## Current distribution")
    lines.append("")
    lines.append("| Theme | Documents |")
    lines.append("|---|---:|")
    for theme, count in top_themes:
        lines.append(f"| {theme} | {count} |")
    lines.append("")
    lines.append("| Tier | Documents |")
    lines.append("|---|---:|")
    for tier in ("Critical", "High", "Medium", "Low"):
        lines.append(f"| {tier} | {tier_counts.get(tier, 0)} |")
    lines.append("")
    lines.append("## What this gives you")
    lines.append("")
    lines.append("- szybki wizualny orientacyjny obraz calego knowledge banku,")
    lines.append("- mapowanie tematyczne zamiast tylko podzialu projektowego,")
    lines.append("- ranking dokumentow, ktore warto otwierac najpierw.")
    return "\n".join(lines)


def write_output(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate knowledge navigation artifacts for docs/")
    parser.add_argument("--docs-root", default=None, help="Docs root directory")
    parser.add_argument("--output-dir", default=None, help="Output directory for generated markdown")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    docs_root = Path(args.docs_root) if args.docs_root else repo_root / "docs"
    output_dir = Path(args.output_dir) if args.output_dir else docs_root

    records = rank_documents(docs_root)

    hub = build_hub_md(records)
    visuals = build_visuals_md(records, docs_root)
    thematic = build_thematic_index_md(records, docs_root)
    importance = build_importance_index_md(records, docs_root)

    write_output(output_dir / "KNOWLEDGE_HUB.md", hub)
    write_output(output_dir / "KNOWLEDGE_VISUALS.md", visuals)
    write_output(output_dir / "THEMATIC_INDEX.md", thematic)
    write_output(output_dir / "IMPORTANCE_INDEX.md", importance)

    print(f"Generated knowledge hub artifacts in {output_dir}")
    print(f"Documents analyzed: {len(records)}")


if __name__ == "__main__":
    main()