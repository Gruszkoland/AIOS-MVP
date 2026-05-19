# Plan Konfiguracji Menu Ustawień Roo Code dla ADRION 369

Ten dokument definiuje optymalne parametry dla wszystkich zakładek ustawień Roo Code, aby zapewnić najwyższą wydajność Roju.

## 1. Zakładka: Provider & Models (API)
*   **Provider:** OpenRouter (rekomendowany dla Claude 3.5 Sonnet) lub Local (Ollama).
*   **Model:** `anthropic/claude-3.5-sonnet` dla Architecta (High Reasoning).
*   **Fallback Model:** `deepseek/deepseek-coder-v2` dla oszczędności/offline.
*   **Context Window:** Ustaw na maksimum (np. 128k+), aby Librarian mógł widzieć całe repozytorium.

## 2. Zakładka: MCP Servers (Ręce Systemu)
Należy podłączyć następujące serwery:
*   **@modelcontextprotocol/server-filesystem:** Podstawa dla SAP do operacji na plikach.
*   **@modelcontextprotocol/server-sequential-thinking:** Klucz do głębokiego rozumowania Arbitra.
*   **brave-search/google-search:** Dla Sentinela do monitorowania trendów i anomalii (Law 4).

## 3. Zakładka: Context Settings (Pamięć)
*   **Ignore Patterns:** Wyklucz duże foldery binarne i `.git`, aby nie zapychać kontekstu.
*   **Include Patterns:** Dodaj `**/*.md`, `**/progress/*`, `**/config/*.yml` – to są źródła prawdy ADRION.

## 4. Zakładka: Privacy & Security (Guardians)
*   **Always Allow Read:** Włącz dla plików tekstowych (przyspiesza pracę Librariana).
*   **Request Permissions for Write/Commands:** OBOWIĄZKOWO włączone (Guardian Law 8 - Compliance).
*   **Data Training:** Wyłącz (Guardian Law 7 - Privacy).

## 5. Zakładka: Notification & Sounds
*   **Enable Sound on Completion:** Włącz (Rhythm - G3), aby wiedzieć, kiedy cykl pracy się zakończył.

---
*Wygenerowano przez: ADRION SAP Agent*
