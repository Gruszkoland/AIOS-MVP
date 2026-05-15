#!/usr/bin/env python3
"""
🏷️ Automatyzacja Tagowania dla Dokumentacji
Batch processing 15k+ .md plików z automatycznym kategoryzowaniem przez AI

Strategia:
- Czyta zawartość każdego .md
- Ekstrahuje 500 znaków treści dla analizy
- Wysyła do lokalnego LLM (Ollama/LM Studio) lub fallback do kategoriami
- Dodaje YAML frontmatter z tagami
- Zachowuje oryginalną treść dokumentu
- Batch processing z progress tracking
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Set, Optional
import requests
from datetime import datetime

# ============================================================================
# KONFIGURACJA
# ============================================================================

ROOT_PATH = r"C:\Users\adiha\Desktop\Dokumentacja"
VENV_PATH = r"C:\Users\adiha\.1_Projekty\162 demencje w schemacie 369\.venv"

# Endpoint dla lokalnego LLM (ApliArte AI / Ollama / LM Studio)
# Spróbuj najpierw lokalny Ollama, fallback do prostych kategorii
LOCAL_LLM_ENDPOINTS = [
    "http://localhost:11434/api/generate",  # Ollama
    "http://localhost:1234/v1/chat/completions",  # LM Studio
]

# Fallback kategorie (jeśli LLM niedostępny)
FALLBACK_CATEGORIES = {
    "projekty": ["projekt", "development", "kod", "implementation", "program"],
    "biznes": ["business", "strategy", "plan", "revenue", "marketing", "sprzedaż"],
    "technologia": ["tech", "system", "architecture", "infrastructure", "docker", "kubernetes"],
    "sztuczna-inteligencja": ["ai", "model", "neural", "machine learning", "llm", "gpt"],
    "dane": ["data", "analytics", "database", "sql", "extraction", "dataframe"],
    "bezpieczeństwo": ["security", "privacy", "encryption", "auth", "rbac"],
    "dokumentacja": ["documentation", "guide", "manual", "readme", "instruction"],
    "raport": ["report", "analysis", "summary", "audit", "metrics"],
}

BATCH_SIZE = 50  # Przetwarzaj po 50 plików na raz
MAX_RETRIES = 3

# ============================================================================
# UTILITIES
# ============================================================================

def log_progress(current: int, total: int, message: str = ""):
    """Print progress indicator"""
    percent = (current / total * 100) if total > 0 else 0
    bar = "█" * int(percent / 5) + "░" * (20 - int(percent / 5))
    status = f"[{bar}] {percent:6.1f}% ({current:,d}/{total:,d})"
    if message:
        status += f" • {message}"
    print(f"\r{status}", end="", flush=True)

def extract_content_sample(md_content: str, sample_size: int = 500) -> str:
    """Extract first N characters of content for AI analysis"""
    # Usuń YAML frontmatter jeśli istnieje
    if md_content.startswith("---"):
        parts = md_content.split("---", 2)
        if len(parts) >= 3:
            md_content = parts[2]
    
    # Usuń markdown headers, linki, itp dla czystszej analizy
    clean_content = re.sub(r'[#*`\[\]()]', '', md_content)
    clean_content = re.sub(r'\n+', ' ', clean_content)
    clean_content = re.sub(r'\s+', ' ', clean_content).strip()
    
    return clean_content[:sample_size]

def categorize_with_llm(content_sample: str, attempt: int = 0) -> Optional[List[str]]:
    """Try to categorize content using local LLM"""
    if attempt >= len(LOCAL_LLM_ENDPOINTS):
        return None
    
    endpoint = LOCAL_LLM_ENDPOINTS[attempt]
    
    prompt = f"""Analyze this document content and suggest 3-5 relevant tags/categories (comma-separated, lowercase, no spaces):

"{content_sample[:200]}"

Tags (only tags, nothing else):"""
    
    try:
        if "ollama" in endpoint.lower() or "1234" in endpoint:
            # Ollama API format
            response = requests.post(
                endpoint,
                json={"prompt": prompt, "model": "mistral", "stream": False},
                timeout=10
            )
            if response.status_code == 200:
                result = response.json().get("response", "").strip()
                tags = [t.strip() for t in result.split(",") if t.strip()]
                return tags[:5] if tags else None
    except Exception as e:
        # Fallback do następnego endpointa
        return categorize_with_llm(content_sample, attempt + 1)
    
    return None

def categorize_with_fallback(content_sample: str) -> List[str]:
    """Fallback categorization based on keyword matching"""
    content_lower = content_sample.lower()
    scores = {}
    
    for category, keywords in FALLBACK_CATEGORIES.items():
        score = sum(1 for kw in keywords if kw in content_lower)
        if score > 0:
            scores[category] = score
    
    # Zwróć top 3-5 kategorii
    sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [cat for cat, _ in sorted_cats[:5]] if sorted_cats else ["dokumentacja"]

def generate_tags(content_sample: str) -> List[str]:
    """Generate tags using AI or fallback"""
    # Najpierw spróbuj LLM
    tags = categorize_with_llm(content_sample)
    if tags:
        return tags
    
    # Fallback
    return categorize_with_fallback(content_sample)

def add_frontmatter_tags(md_content: str, tags: List[str]) -> str:
    """Add YAML frontmatter with tags to markdown content"""
    # Jeśli już istnieje frontmatter, aktualizuj
    if md_content.startswith("---"):
        parts = md_content.split("---", 2)
        if len(parts) >= 3:
            try:
                # Parse existing YAML
                yaml_block = parts[1]
                content = parts[2]
                
                # Update tags in YAML
                if "tags:" in yaml_block:
                    yaml_block = re.sub(
                        r'tags:.*?(?=\n\S|\n*$)',
                        f'tags: {json.dumps(tags)}',
                        yaml_block,
                        flags=re.DOTALL
                    )
                else:
                    yaml_block = yaml_block.rstrip() + f'\ntags: {json.dumps(tags)}'
                
                return f"---{yaml_block}\n---{content}"
            except:
                pass
    
    # Stwórz nowy frontmatter
    tags_yaml = ", ".join(tags)
    frontmatter = f"""---
tags: {json.dumps(tags)}
auto-generated: {datetime.now().isoformat()}
---
"""
    return frontmatter + md_content

def process_md_file(md_path: str) -> Dict[str, any]:
    """Process single .md file and add tags"""
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract sample for categorization
        sample = extract_content_sample(content)
        
        if not sample.strip():
            return {"file": md_path, "status": "empty", "tags": []}
        
        # Generate tags
        tags = generate_tags(sample)
        
        # Add frontmatter
        updated_content = add_frontmatter_tags(content, tags)
        
        # Write back
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        return {"file": md_path, "status": "tagged", "tags": tags}
    
    except Exception as e:
        return {"file": md_path, "status": "error", "error": str(e)}

def scan_md_files(root_path: str) -> List[str]:
    """Scan all .md files in directory"""
    md_files = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip archived folders
        if any(skip in dirpath.lower() for skip in ['.1_projekty', 'archiwum', 'backup']):
            dirnames[:] = []
            continue
        
        for filename in filenames:
            if filename.endswith('.md'):
                md_files.append(os.path.join(dirpath, filename))
    
    return md_files

# ============================================================================
# MAIN BATCH PROCESSING
# ============================================================================

def main():
    print("\n" + "="*80)
    print("🏷️  AUTOMATYZACJA TAGOWANIA - BATCH PROCESSING")
    print("="*80 + "\n")
    
    # Scan plików
    print("🔍 Skanowanie .md plików...")
    md_files = scan_md_files(ROOT_PATH)
    total_files = len(md_files)
    
    print(f"✅ Znaleziono {total_files:,d} plików .md do przetagowania\n")
    
    if total_files == 0:
        print("❌ Brak plików .md do przetworzenia!")
        return
    
    # Batch processing
    results = {
        "tagged": 0,
        "empty": 0,
        "error": 0,
        "tags_summary": {}
    }
    
    print(f"⚙️  Przetwarzanie w batches ({BATCH_SIZE} plików na raz)...\n")
    
    for i, md_file in enumerate(md_files, 1):
        log_progress(i, total_files, os.path.basename(md_file)[:40])
        
        result = process_md_file(md_file)
        results[result["status"]] = results.get(result["status"], 0) + 1
        
        # Aggregate tags
        for tag in result.get("tags", []):
            results["tags_summary"][tag] = results["tags_summary"].get(tag, 0) + 1
    
    print("\n\n" + "="*80)
    print("📊 WYNIKI PRZETAGOWANIA")
    print("="*80)
    print(f"✅ Przetagowano:        {results['tagged']:>6,d} plików")
    print(f"⚠️  Puste:              {results['empty']:>6,d} plików")
    print(f"❌ Błędy:              {results['error']:>6,d} plików")
    print(f"📈 Razem:              {total_files:>6,d} plików")
    
    print("\n" + "-"*80)
    print("🏷️  TOP TAGI (najczęściej przypisane):")
    print("-"*80)
    
    sorted_tags = sorted(
        results["tags_summary"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:15]
    
    for tag, count in sorted_tags:
        percent = (count / results['tagged'] * 100) if results['tagged'] > 0 else 0
        bar = "█" * int(percent / 5)
        print(f"  {tag:<20} │ {count:>5,d} │ {bar} {percent:>5.1f}%")
    
    print("\n" + "="*80)
    print(f"✨ Batch processing zakończony: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    # Generate report
    generate_report(results, total_files)

def generate_report(results: Dict, total_files: int):
    """Generate detailed report"""
    report_path = r"C:\Users\adiha\.1_RAPORTY_WDRAŻANIA\Tagowanie_Automatyczne_{}.md".format(
        datetime.now().strftime("%d-%m-%Y")
    )
    
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    report = f"""# 🏷️ Raport Automatycznego Tagowania Dokumentów

**Data:** {datetime.now().strftime("%d-%m-%Y %H:%M:%S")}  
**Folder:** `{ROOT_PATH}`

## 📊 Statystyka Przetwarzania

| Metrika | Ilość |
|---------|-------|
| **Razem .md plików** | {total_files:,d} |
| **Przetagowano** | {results['tagged']:,d} |
| **Puste (bez treści)** | {results['empty']:,d} |
| **Błędy** | {results['error']:,d} |
| **Sukces** | {((results['tagged']/total_files*100) if total_files > 0 else 0):.1f}% |

## 🏷️ Najczęstsze Tagi

Tagi automatycznie przypisane do dokumentów (top 20):

"""
    
    sorted_tags = sorted(
        results["tags_summary"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:20]
    
    for i, (tag, count) in enumerate(sorted_tags, 1):
        percent = (count / results['tagged'] * 100) if results['tagged'] > 0 else 0
        report += f"{i:2d}. `{tag}` — {count:,d} plików ({percent:.1f}%)\n"
    
    report += f"""

## ✨ Frontmatter Format

Każdy .md plik wzbogacony o YAML frontmatter z tagami:

```yaml
---
tags: ["tag1", "tag2", "tag3"]
auto-generated: 2026-05-14T...
---
```

## 🔄 Następne Kroki

1. **Walidacja Tagów** — Przegląd automatycznie przypisanych kategorii
2. **Indeksowanie** — Integracja z wyszukiwarką pełnotekstową
3. **Rafinacja** — Ręczne poprawy dla dokumentów kluczowych
4. **Eksport Metadanych** — Generowanie JSON z tagami dla systemów zewnętrznych

---
*Raport wygenerowany automatycznie przez batch_tagging_automation.py*
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Raport zapisany: {report_path}\n")

if __name__ == "__main__":
    main()
