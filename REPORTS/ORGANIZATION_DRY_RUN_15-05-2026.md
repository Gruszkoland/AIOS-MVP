# Raport Dry-Run: Organizacja `C:\Users\adiha\.1_Projekty`

Data: 2026-05-15 10:48:57 +02:00
Status: `dry-run`

## Konkluzja

Najbezpieczniejszy pierwszy ruch to organizacja 56 luźnych plików katalogu głównego. Aktywne katalogi projektowe i konfiguracje narzędziowe zostają na miejscu do osobnej decyzji.

## Zakres

| Kategoria | Liczba | Rozmiar |
|---|---:|---:|
| `00_DOKUMENTACJA/operacyjna` | 6 | 42013 B |
| `00_DOKUMENTACJA/referencje` | 16 | 148006 B |
| `20_NARZEDZIA` | 19 | 93047 B |
| `30_WIZUALIZACJE` | 2 | 42349 B |
| `40_RAPORTY` | 10 | 127461 B |
| `90_ARCHIWUM/paczki` | 3 | 85661 B |

## Zostają W Root

| Plik/Katalog | Powód |
|---|---|
| `.git` | Metadane repozytorium |
| `.agents` | Instrukcje agentów |
| `.github` | Integracje GitHub |
| `.n8nac` | Stan n8n-as-code |
| `.vscode` | Ustawienia workspace |
| `AGENTS.md` | Instrukcje runtime |
| `README.md` | Wejście do workspace |
| `.gitattributes` | Konfiguracja Git |
| `desktop.ini` | Plik systemowy Windows |

## Nieprzenoszone Bez Osobnej Akceptacji

| Katalog | Powód |
|---|---|
| `162 demencje w schemacie 369` | Aktywna platforma, 78763 pliki |
| `Consultacja-Wielomodelowa-AI` | Aktywny projekt API |
| `n8n-produkcja` | Produkcyjne workflow n8n |
| `adrion-369-architecture` | Dokumentacja i źródła architektury |
| `adrion-deploy` | Infrastruktura wdrożeniowa |
| `leadgen-comet-pipeline` | Pipeline modułowy |
| `embedding-ab-test-framework` | Framework testowy |
| `kyc-provider-integration-guide` | Integracja KYC |
| `Punkt odniesienia` | Baza referencyjna, 5426 plików |

## Manifest Przenosin Etapu 1

| Źródło | Cel |
|---|---|
| `adrion-369-DEPLOYMENT-GUIDE.md` | `00_DOKUMENTACJA/operacyjna/adrion-369-DEPLOYMENT-GUIDE.md` |
| `instalacja_gpt4all.md` | `00_DOKUMENTACJA/operacyjna/instalacja_gpt4all.md` |
| `Kontynuuj.txt` | `00_DOKUMENTACJA/operacyjna/Kontynuuj.txt` |
| `modele_offline.md` | `00_DOKUMENTACJA/operacyjna/modele_offline.md` |
| `rozwoj.md` | `00_DOKUMENTACJA/operacyjna/rozwoj.md` |
| `SECURITY-HARDENING-IMPLEMENTATION.md` | `00_DOKUMENTACJA/operacyjna/SECURITY-HARDENING-IMPLEMENTATION.md` |
| `1_DANE_DO_WDROZENIA.md` | `00_DOKUMENTACJA/referencje/1_DANE_DO_WDROZENIA.md` |
| `3D-VISUALIZATION-INDEX.md` | `00_DOKUMENTACJA/referencje/3D-VISUALIZATION-INDEX.md` |
| `ADRION369_Autonomous_Agent_Prompt.docx` | `00_DOKUMENTACJA/referencje/ADRION369_Autonomous_Agent_Prompt.docx` |
| `adrion-369-DOCUMENTATION-INDEX.md` | `00_DOKUMENTACJA/referencje/adrion-369-DOCUMENTATION-INDEX.md` |
| `adrion-369-MCP-DEPENDENCIES.md` | `00_DOKUMENTACJA/referencje/adrion-369-MCP-DEPENDENCIES.md` |
| `adrion-369-STRUKTURA.md` | `00_DOKUMENTACJA/referencje/adrion-369-STRUKTURA.md` |
| `adrion-369-VISUALIZATIONS.md` | `00_DOKUMENTACJA/referencje/adrion-369-VISUALIZATIONS.md` |
| `EXPORT_STRATEGY.md` | `00_DOKUMENTACJA/referencje/EXPORT_STRATEGY.md` |
| `KNOWLEDGE BANK.md` | `00_DOKUMENTACJA/referencje/KNOWLEDGE BANK.md` |
| `konfiguracja_api_modeli.md` | `00_DOKUMENTACJA/referencje/konfiguracja_api_modeli.md` |
| `Konfiguracja_ApliArte_AI.md` | `00_DOKUMENTACJA/referencje/Konfiguracja_ApliArte_AI.md` |
| `konfiguracja_gemini_api.md` | `00_DOKUMENTACJA/referencje/konfiguracja_gemini_api.md` |
| `Naprawa - 33 person.txt` | `00_DOKUMENTACJA/referencje/Naprawa - 33 person.txt` |
| `ORGANIZATION_README.md` | `00_DOKUMENTACJA/referencje/ORGANIZATION_README.md` |
| `PLUGINS_README.md` | `00_DOKUMENTACJA/referencje/PLUGINS_README.md` |
| `PROJECT_INDEX.md` | `00_DOKUMENTACJA/referencje/PROJECT_INDEX.md` |
| `batch_tagging_automation.py` | `20_NARZEDZIA/batch_tagging_automation.py` |
| `convert_all_global_recursive.py` | `20_NARZEDZIA/convert_all_global_recursive.py` |
| `convert_files_to_md.py` | `20_NARZEDZIA/convert_files_to_md.py` |
| `convert_filosofia_recursive.py` | `20_NARZEDZIA/convert_filosofia_recursive.py` |
| `convert_pdf_to_md.py` | `20_NARZEDZIA/convert_pdf_to_md.py` |
| `delete_all_global_duplicates.py` | `20_NARZEDZIA/delete_all_global_duplicates.py` |
| `delete_duplicates.py` | `20_NARZEDZIA/delete_duplicates.py` |
| `delete_filosofia_recursive.py` | `20_NARZEDZIA/delete_filosofia_recursive.py` |
| `generate_grafana_dashboard.py` | `20_NARZEDZIA/generate_grafana_dashboard.py` |
| `generate_readmes.py` | `20_NARZEDZIA/generate_readmes.py` |
| `install-copilot-plugins.bat` | `20_NARZEDZIA/install-copilot-plugins.bat` |
| `install-copilot-plugins.ps1` | `20_NARZEDZIA/install-copilot-plugins.ps1` |
| `install-copilot-plugins.sh` | `20_NARZEDZIA/install-copilot-plugins.sh` |
| `scan_all_dokumentacja.py` | `20_NARZEDZIA/scan_all_dokumentacja.py` |
| `scan_pdf_dokumentacja.py` | `20_NARZEDZIA/scan_pdf_dokumentacja.py` |
| `test_dependabot.py` | `20_NARZEDZIA/test_dependabot.py` |
| `verify_all_global_conversion.py` | `20_NARZEDZIA/verify_all_global_conversion.py` |
| `verify_conversion.py` | `20_NARZEDZIA/verify_conversion.py` |
| `verify_filosofia_recursive.py` | `20_NARZEDZIA/verify_filosofia_recursive.py` |
| `ADRION-369-3D-Ecosystem.html` | `30_WIZUALIZACJE/ADRION-369-3D-Ecosystem.html` |
| `ADRION-369-Architecture-Diagram.html` | `30_WIZUALIZACJE/ADRION-369-Architecture-Diagram.html` |
| `adrion-369-CODE-QUALITY-REPORT.md` | `40_RAPORTY/adrion-369-CODE-QUALITY-REPORT.md` |
| `adrion-369-COMPLETE-PACKAGE.md` | `40_RAPORTY/adrion-369-COMPLETE-PACKAGE.md` |
| `AUDIT_REPORT_v1.md` | `40_RAPORTY/AUDIT_REPORT_v1.md` |
| `DEPENDABOT_CODESPACES_PLAN.md` | `40_RAPORTY/DEPENDABOT_CODESPACES_PLAN.md` |
| `Dependabot-Personas-ROPE2-Completion-15-05-2026.md` | `40_RAPORTY/Dependabot-Personas-ROPE2-Completion-15-05-2026.md` |
| `DEPLOYMENT-PIPELINE-SPRINT.md` | `40_RAPORTY/DEPLOYMENT-PIPELINE-SPRINT.md` |
| `EXECUTIVE-SUMMARY-3-SPRINTS.md` | `40_RAPORTY/EXECUTIVE-SUMMARY-3-SPRINTS.md` |
| `GITHUB_EXPORT_COMPLETE_14-05-2026.md` | `40_RAPORTY/GITHUB_EXPORT_COMPLETE_14-05-2026.md` |
| `MASTER-TIMELINE-ALL-SPRINTS.md` | `40_RAPORTY/MASTER-TIMELINE-ALL-SPRINTS.md` |
| `PERFORMANCE-OPTIMIZATION-SPRINT.md` | `40_RAPORTY/PERFORMANCE-OPTIMIZATION-SPRINT.md` |
| `files (1).zip` | `90_ARCHIWUM/paczki/files (1).zip` |
| `files (2).zip` | `90_ARCHIWUM/paczki/files (2).zip` |
| `files.zip` | `90_ARCHIWUM/paczki/files.zip` |

## Następna Decyzja

Rekomendacja: zatwierdzić etap 1 i wykonać tylko przenosiny luźnych plików root. Etap 2, czyli przenoszenie całych katalogów projektów, powinien nastąpić dopiero po aktualizacji indeksów i konfiguracji zależnych.
