# OAuth 2.0 w ADRION 369 - FAQ (Frequently Asked Questions)

---

## 🔐 Pytanie 1: Dlaczego ADRION 369 używa OAuth zamiast haseł?

**Odpowiedź:**

OAuth 2.0 rozwiązuje trzy kluczowe problemy bezpieczeństwa:

1. **Hasła nie muszą być udostępniane aplikacjom**
   - Google: Nieznany login/hasło = brak ryzyka wycieku w aplikacji
   - ADRION 369: MCP servers nie znają uprawnień użytkownika, tylko token czasowy

2. **Ograniczone uprawnienia (Scopes)**
   - Google: Aplikacja może czytać tylko Drive, nie pocztę
   - ADRION 369: Genesis server może czytać logi, nie modyfikować konfiguracji

3. **Łatwa rewokacja**
   - Google: Odwołujesz dostęp w ustawieniach, aplikacja utraci token
   - ADRION 369: `roo revoke-token genesis` = natychmiast brak dostępu

**Mapowanie do Guardian Laws**:
- ✅ **G7 (Privacy)**: Minimalne dane udostępniane aplikacjom
- ✅ **G8 (Nonmaleficence)**: Ograniczone uprawnienia = mniejsza szkoda jeśli token wycieknie

---

## 🔐 Pytanie 2: Co to są "Scopes"?

**Odpowiedź:**

Scope to **etykieta dostępu** - dokładnie definiuje co aplikacja może robić.

**Analogia Google**:
```
Scope: https://www.googleapis.com/auth/drive.readonly
Znaczenie: "Mogę czytać pliki na Drive, ale nie edytować"
```

**ADRION 369 Scopes**:
```
Scope: mcp://genesis.adrion/read.record
Znaczenie: "Mogę czytać rekordy z Genesis Record, ale nie pisać"

Scope: mcp://healer.adrion/health.check
Znaczenie: "Mogę sprawdzać kondycję systemu Healer"
```

**Dlaczego granularnie?** (Least Privilege)
- ❌ ZAŻYCZENIE: `mcp://genesis.adrion/*` (dostęp do wszystkiego)
- ✅ POPRAWNE: `mcp://genesis.adrion/read.record` (tylko czytanie rekordów)

**Weryfikacja**: Roo Code sprawdza SEC-008 podczas analizy kodu:
```bash
roo analyze --profile security-audit
# SEC-008 sprawdzi czy wszystkie scopes są granularne
```

---

## 🔐 Pytanie 3: Gdzie są przechowywane tokeny OAuth w ADRION 369?

**Odpowiedź:**

**❌ NIGDY nie w pliku tekstowym** (Roo Code SEC-010: Unencrypted Token Storage)

**✅ Bezpieczna Storage**:

### Opcja 1: Encrypted Environment (Rekomendowana)
```python
# Token szyfrowany AES-256-GCM
ENCRYPTED_TOKEN = "gAAAAABl4x9c..."  # Zaszyfrowany
CIPHER_KEY = "<pobrane z system-keyring>"

# Deszyfrowanie przy użyciu
from cryptography.fernet import Fernet
cipher = Fernet(CIPHER_KEY)
token = cipher.decrypt(ENCRYPTED_TOKEN.encode())
```

**Lokalizacja**: `.env.template` (zmienne szyfrowane)
**Konfiguracja**: `oauth_config.ini`:
```ini
[servers.genesis]
storage_backend = "encrypted-env"
```

### Opcja 2: System Keyring (macOS/Windows/Linux)
```python
import keyring
token = keyring.get_password("ADRION-Genesis", "oauth_token")
```

**Zaleta**: OS-level encryption, bezpieczny dla produkcji
**Konfiguracja**:
```ini
storage_backend = "system-keyring"
```

### Opcja 3: Cloud Vault (AWS/Azure)
```ini
storage_backend = "aws-secretsmanager"
# lub
storage_backend = "azure-keyvault"
```

**Weryfikacja SEC-010**:
```
roo analyze --profile security-audit
# Sprawdzi czy tokeny są szyfrowane
```

---

## 🔐 Pytanie 4: Co się dzieje kiedy token wygasa?

**Odpowiedź:**

ADRION 369 implementuje **token rotation** (SEC-009):

### Timeline:
```
T=0h    : Token wydany (Access Token)
T=23h   : Roo Code SEC-009 detektuje wygaśnięcie za 1h
T=23h:01 : Aplikacja automatycznie odświeża token (Refresh Token)
T=24h   : Stary token wygasa (ale już jest nowy)
```

### Kod (automatyczny):
```python
async def token_rotation_loop(server_name: str):
    """SEC-009 implementation"""
    while True:
        token = get_current_token(server_name)
        expires_at = datetime.fromisoformat(token['exp'])
        rotation_time = expires_at - timedelta(hours=1)

        if datetime.utcnow() >= rotation_time:
            new_token = refresh_token(server_name)  # Otrzymaj nowy token
            store_encrypted(server_name, new_token)  # Zaszyfruj i zapisz
            log_audit(f"Token rotated: {server_name}")  # Loguj (SEC-011)

        await asyncio.sleep(3600)  # Sprawdzaj co godzinę
```

### Konfiguracja `.roo/oauth_config.ini`:
```ini
[servers.genesis]
token_expiration_hours = 24
requires_rotation = true

[global_settings]
rotation_margin_hours = 1  # Odśwież 1h przed wygaśnięciem
```

**Mapowanie do Guardian Laws**:
- ✅ **G3 (Rhythm)**: Cykliczne odświeżenie tokenów
- ✅ **G9 (Sustainability)**: Token rotation zapobiega długotrwałym kompromitacjom

---

## 🔐 Pytanie 5: Gdzie logują się wszystkie operacje OAuth?

**Odpowiedź:**

Wszystkie OAuth operacje są logowane w **audit trail** (Roo Code SEC-011: Mandatory Scope Audit Logging):

### Lokalizacja:
```
Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/oauth_audit.jsonl
```

### Format JSONL (JSON Lines):
```json
{"timestamp":"2026-04-08T14:30:00.000Z","event_type":"token_request","server":"genesis","scope":"read.record","user_id":"adrion-master","result":"success"}
{"timestamp":"2026-04-08T14:30:05.123Z","event_type":"token_rotated","server":"genesis","scope":"read.record","user_id":"system","result":"success"}
{"timestamp":"2026-04-08T23:59:59.999Z","event_type":"scope_denied","server":"vortex","scope":"write.dangerous-data","user_id":"client-a","result":"denied"}
```

### Co jest logowane?
- ✅ Kiedy token jest wydawany
- ✅ Który server go zażądał
- ✅ Jaki scope był żądany
- ✅ Czy żądanie zostało zaakceptowane czy odrzucone
- ✅ Kiedy token został obrócony

### Przegląd logów:
```bash
# Wszystkie operacje
cat "Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/oauth_audit.jsonl" | jq .

# Tylko odmowy dostępu
cat "..." | jq 'select(.result == "denied")'

# Tylko operacje określonego servera
cat "..." | jq 'select(.server == "genesis")'
```

**Mapowanie do Guardian Laws**:
- ✅ **G4 (Causality)**: Każda operacja ma przyczynę i efekt (zalogowane)
- ✅ **G5 (Transparency)**: Wszystko jest widoczne w audit trail

---

## 🔐 Pytanie 6: Co to są "ukryte dane aplikacji" (App Data Folders)?

**Odpowiedź:**

**Analogia Google**:
- Google Drive ma folder `.hidden` gdzie aplikacje mogą magazynować dane
- Użytkownik nie widzi go w normalnym widoku
- Ale Google go udokumentuje i pozwala użytkownikowi go usunąć

**ADRION 369 Ukryte Foldery**:

| Folder | Cel | Dokumentacja | Usunięcie |
|--------|-----|--------------|-----------|
| `.roo_cache/` | Temp cache analizy kodu | ✅ W `oauth_config.ini` | `rm -rf .roo_cache/` |
| `.aider/` | Historia konwersacji Aider | ✅ W `oauth_config.ini` | `rm -rf .aider/` |
| `Genesis Record/10_RAPORTY/.../` | Logi audytu OAuth | ✅ W `oauth_config.ini` | `rm -rf Genesis\ Record/...` |

### Roo Code SEC-012: Application Data Folder Leakage
```
Rko Code szuka ukrytych folderów - jeśli nie są udokumentowane, zgłasza błąd.
```

**Kontrola użytkownika** (G7-Privacy):
```bash
# Użytkownik może sprawdzić co jest przechowywane
ls -la .roo_cache/
ls -la .aider/
du -sh "Genesis Record/"

# Użytkownik może usunąć
rm -rf .roo_cache/
rm -rf .aider/
```

---

## 🔐 Pytanie 7: Co się stanie jeśli token ucieka?

**Odpowiedź:**

**Ze względu na OAuth 2.0 design, ryzyko jest ograniczone:**

### Scenariusz: Wyciekł token Genesis `read.record`

#### Ograniczenia naturalnie:
1. ✅ Token ma **24-godzinny TTL** - sam się deaktywuje
2. ✅ Token ograniczony do **samego `read.record`** - nie może pisać
3. ✅ Token dla **Genesis** - nie można użyć dla Guardian/Healer
4. ✅ Wszystkie operacje **logowane** - łatwo detectować abuse

#### Szybka reaktywacja:
```bash
# Administrator: Natychmiast odwołaj token
roo revoke-token genesis

# Wystawimy nowy token
roo refresh-token genesis --force
```

**Porównanie**:
- ❌ **Jeśli by hasło**: Attakant ma dostęp na zawsze
- ✅ **Z OAuth**: Attakant ma dostęp do `read.record` przez max 24h

**Mapowanie do Guardian Laws**:
- ✅ **G8 (Nonmaleficence)**: Ograniczone uprawnienia = ograniczona szkoda
- ✅ **G3 (Rhythm)**: Automatyczne rotacje zmniejszają okno ataku

---

## 🔐 Pytanie 8: Jak weryfikować, czy OAuth jest poprawnie skonfigurowany?

**Odpowiedź:**

**Roo Code Security Profile:**
```bash
# Pełna analiza OAuth
roo analyze --profile security-audit
```

**Checklist po wdrożeniu:**
```ini
[compliance_checklist]
all_mcp_servers_oauth_configured = true  # ✅ Wszystkie 6 serwerów
scopes_documented = true                  # ✅ W oauth_config.ini
token_expiration_configured = true        # ✅ 24h/12h ustawione
token_rotation_implemented = true         # ✅ SEC-009 aktywny
tokens_encrypted_at_rest = true          # ✅ AES-256-GCM
audit_logging_active = true              # ✅ oauth_audit.jsonl zapisuje
hidden_folders_documented = true         # ✅ SEC-012 przeszedł
roo_code_security_passes = true          # ✅ SEC-008-012 no issues
security_profile_analysis_passes = true  # ✅ Brak ostrzeżeń
oauth_consent_screen_reviewed = true     # ✅ Przejrzano
quarterly_audit_scheduled = true         # ✅ W kalendarzu
```

**Ręczna weryfikacja:**
```bash
# 1. Sprawdź konfigurację
cat .roo/oauth_config.ini | grep "\[servers\."

# 2. Sprawdź reguły Roo Code
cat roo.rules.json | grep "SEC-00[89]"

# 3. Sprawdź logi OAuth
tail "Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/oauth_audit.jsonl"

# 4. Sprawdź VS Code settings
cat .vscode/settings.json | grep "roo.security"
```

---

## 🔐 Pytanie 9: Czy mogę użyć API Google/OpenRouter z ADRION 369?

**Odpowiedź:**

**TAK!** Google OAuth + OpenRouter API mogą być zintegrowane:

### Google Integration:
```ini
[servers.google-connector]
name = "Google Data Connector"
scopes = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/sheets.readonly"
]
token_expiration_hours = 24
requires_rotation = true
storage_backend = "encrypted-env"
```

### OpenRouter Integration:
```ini
[servers.openrouter-llm]
name = "OpenRouter LLM Server"
scopes = [
    "openrouter://api.query"
]
token_expiration_hours = 24
requires_rotation = true
storage_backend = "encrypted-env"
```

### Wdrażanie:
1. Dodaj do `oauth_config.ini`
2. Uruchom `roo analyze --profile security-audit` (weryfikacja SEC-008)
3. Szyfruj API keys w `.env.template` (SEC-010)
4. Testy: `roo test-oauth <server-name>`

---

## 🔐 Pytanie 10: Gdzie znaleźć więcej informacji o implementacji?

**Odpowiedź:**

| Dokument | Zawartość | Lokalizacja |
|----------|-----------|------------|
| **mcp-security.md** | Pełny poradnik wdrażania OAuth | `.roo/mcp-security.md` |
| **oauth_config.ini** | Konfiguracja serwerów & tokenów | `.roo/oauth_config.ini` |
| **google-oauth-mapping.md** | Mapowanie Google OAuth → ADRION | `.roo/google-oauth-mapping.md` |
| **roo.rules.json** | Reguły SEC-008-012 | `roo.rules.json` |
| **mcp.json** | Konfiguracja MCP servers | `.roo/mcp.json` |
| **README.md** | Przegląd Roo Code | `.roo/README.md` |

**Szybkie linki**:
- 🔐 Bezpieczeństwo: [mcp-security.md](.roo/mcp-security.md)
- 📋 Konfiguracja: [oauth_config.ini](.roo/oauth_config.ini)
- 🗺️ Mapowanie: [google-oauth-mapping.md](.roo/google-oauth-mapping.md)
- ✅ Reguły: `roo.rules.json` (SEC-008 through SEC-012)

---

## 📞 Problemy & Rozwiązania

### Problem: "SEC-008 Scope validation failed"
**Rozwiązanie:**
1. Sprawdź scope w kodzie
2. Porównaj z `oauth_config.ini [servers.XX]`
3. Dodaj scope jeśli jest potrzebny
4. Re-run: `roo analyze --profile security-audit`

### Problem: "Token storage must be encrypted"
**Rozwiązanie:**
1. Upewnij się że masz `CIPHER_KEY` w system-keyring
2. Zaktualizuj `oauth_config.ini`:
   ```ini
   storage_backend = "encrypted-env"
   ```
3. Pobierz nowy token: `roo refresh-token <server> --force`

### Problem: "Audit logging not active"
**Rozwiązanie:**
```bash
mkdir -p "Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU"
chmod 755 "Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU"
```

---

**Prepared**: 2026-04-08
**Status**: ✅ Complete & Compliant with 9 Guardian Laws
**Questions?**: See [mcp-security.md](.roo/mcp-security.md) or contact ADRION Master Orchestrator
