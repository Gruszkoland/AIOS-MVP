---
name: ai-personas
description: >-
  Use when the user invokes ADRION/Gemini numbered personas (01–33), multi-agent
  orchestration, MPG/AWA/supplementary prompts from the Desktop PERSONY folder,
  or asks which specialist persona to apply. Requires @-attaching the specific
  persona .md from that folder for full behavior.
---

# AI Personas (ADRION — rejestr zewnętrzny)

## Źródło prawdy treści

Kanoniczne pełne prompty person leżą poza repo (Pulpit):

`C:\Users\adiha\Desktop\Dokumentacja\03_OSOBOWOSCI_AI\Gemy Gemini\Gotowe i skoczone PERSONY`

- Persony **01–33:** podfolder `33 Persony AI\` (**33** pliki `.md` + `validation_report_v3.md`)
- **Alternatywa wdrożeniowa „02”:** w korzeniu PERSONY plik `# [02-AWA] — Agent Wdrożeniowo-Automatyzujący.md` (osobnie od osoby **02** w `33 Persony AI\`; szczegóły w `.cursor/rules/ai-personas-registry.mdc`).
- **Orkiestracja:** `MASTER ORKIESTRACJA\` — m.in. `ADRION_369_MASTER_PROMPT_v5.0.md`, warianty KIMI / DeepSeek / Gemini / Grok (pełna lista nazw plików w regule `ai-personas-registry.mdc`).
- **Registry / instrukcje pomocnicze:** m.in. `MATRIX_REGISTRY_2.1.md`, `ADRION_369_Instructions_v5_1.md`, `IMPLEMENTER_AI_PROMPT.md`, `Harmonia-Gateway.md` (korzeń folderu PERSONY).

Portable skill (fallback gdy runtime nie widzi `.github/agents`): `.agents/skills/ai-personas/SKILL.md`.

## Protokół pracy

1. Bez załączonego pliku `.md` persony — krótko wskaż użytkownikowi, którą personę wybrać z tabeli w `.cursor/rules/ai-personas-registry.mdc` i poproś o `@` na właściwy plik (`33 Persony AI\` lub AWA / MPG w korzeniu PERSONY). Jeśli `@` nie widzi plików z Pulpitu, dodaj folder PERSONY do workspace.
2. Po załączeniu pliku — **przyjmij pełną tożsamość** według tego dokumentu (REASONING, INVOKE_WHEN, CONSTRAINTS, OUTPUT_FORMAT).
3. Przy pipeline wieloagentowym — najpierw dokument orkiestracji lub `MATRIX_REGISTRY`, potem handoff do person specjalistycznych (**AOR**/**ARB** według załączonych definicji).

## Relacja do innych agentów workspace

Zadania wyłącznie **n8n-as-code** → nadal używaj agenta `n8n-architect`. Persony ADRION są osobną warstwą — łącz je tylko gdy użytkownik tego chce lub załączy odpowiednie pliki.
