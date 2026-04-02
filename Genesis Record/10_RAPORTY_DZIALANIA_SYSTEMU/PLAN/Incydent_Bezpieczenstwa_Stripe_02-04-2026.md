# PLAN: Incydent Bezpieczeństwa Stripe — 02-04-2026

## CEL SESJI

Natychmiastowa reakcja na krytyczne naruszenie bezpieczeństwa — obecność live secrets Stripe w pliku `.env.local`.

---

## OCENA RYZYKA

| Zasób                     | Status                                  | Ryzyko                                   |
| ------------------------- | --------------------------------------- | ---------------------------------------- |
| `STRIPE_SECRET_KEY_REDACTED` | **AKTYWNY** w chwili wykrycia        | KRYTYCZNE — pełny dostęp do konta Stripe |
| `STRIPE_LOGIN_PASSWORD`   | Plain text w pliku                      | WYSOKIE                                  |
| `STRIPE_BACKUP_CODE`      | 2FA backup code                         | WYSOKIE                                  |
| Historia git `.env.local` | **NIE znaleziono** w historii           | NISKIE                                   |
| `.gitignore` coverage     | `.env.local` jest wykluczony (linia 16) | BEZPIECZNE                               |

---

## KROKI PLANU

### Krok 1: Weryfikacja ekspozycji w git

- **Cel:** Czy plik był kiedykolwiek scommitowany?
- **Kryterium ukończenia:** `git log -- .env.local` zwraca brak commitów
- **Zależności:** brak
- **Priorytet:** KRYTYCZNY
- **Status:** `done` ✅

### Krok 2: Redakcja secrets w pliku .env.local

- **Cel:** Usunięcie aktywnych credentials z pliku — zastąpienie placeholderami
- **Kryterium ukończenia:** Plik nie zawiera żadnych prawdziwych wartości kluczy
- **Zależności:** Krok 1
- **Priorytet:** KRYTYCZNY
- **Status:** `done` ✅

### Krok 3: Weryfikacja .gitignore

- **Cel:** Potwierdzenie że `.env.local` jest i wszędzie chroniony
- **Kryterium ukończenia:** Linia `.env.local` obecna w `.gitignore`
- **Zależności:** brak
- **Priorytet:** WYSOKI
- **Status:** `done` ✅

### Krok 4: Manualne działania użytkownika (WYMAGANE)

- **Cel:** Unieważnienie skompromitowanych credentials na platformach zewnętrznych
- **Kryterium ukończenia:** Użytkownik potwierdza unieważnienie klucza i zmianę hasła
- **Zależności:** Kroki 1-3
- **Priorytet:** KRYTYCZNY
- **Status:** `in-progress` ⚠️

#### 4.1 Unieważnij klucz Stripe `STRIPE_SECRET_KEY_REDACTED`

→ https://dashboard.stripe.com/apikeys > znajdź klucz > "Roll key" lub "Delete"

#### 4.2 Zmień hasło konta Stripe

→ https://dashboard.stripe.com/settings/user > Change password

#### 4.3 Wygeneruj nowe kody zapasowe 2FA

→ https://dashboard.stripe.com/settings/user > Two-factor authentication > Regenerate backup codes

#### 4.4 Wygeneruj nowy `STRIPE_SECRET_KEY`

→ https://dashboard.stripe.com/apikeys > "Create restricted key" lub "Reveal live key"

### Krok 5: Raport końcowy

- **Cel:** Dokumentacja incydentu i potwierdzenie zamknięcia
- **Kryterium ukończenia:** Plik REPORTS utworzony z pełną dokumentacją
- **Zależności:** Kroki 1-4
- **Priorytet:** STANDARDOWY
- **Status:** `planned`
