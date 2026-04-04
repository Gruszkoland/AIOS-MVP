# Plan: Finalna Odblokada Webhook Secret - Pełna Ścieżka (2)

**Data Planu:** 04-02-2026  
**Status:** IN PROGRESS  
**Priorytet:** CRITICAL (blocks production readiness)

---

## 📋 Cel Sesji

Uzyskać `STRIPE_WEBHOOK_SECRET` i uzupełnić pozostałe 3 placeholder values w `micro-saas/.env.local`, aby osiągnąć 100% green validation pipeline.

**Kryteria ukonczenia:**

- ✓ STRIPE*WEBHOOK_SECRET: `whsec*...` (real value, not placeholder)
- ✓ STRIPE_PRICE_ID_PRO: valid product price ID
- ✓ STRIPE_PRICE_ID_FOUNDING: valid product price ID
- ✓ npm run check:secrets: PASS
- ✓ pytest -q: 157/157 PASS
- ✓ npm run build: SUCCESS

---

## 🎯 Kroki Egzekucji

| Krok | Cel                       | Kryteria Ukończenia                        | Zależności              | Priorytet     | Status      |
| ---- | ------------------------- | ------------------------------------------ | ----------------------- | ------------- | ----------- |
| 1    | Verify webhook status     | Check .env.local files for current state   | None                    | P0 (CRITICAL) | DONE        |
| 2    | Guide Stripe CLI workflow | User completes device auth flow locally    | User action required    | P0 (CRITICAL) | IN PROGRESS |
| 3    | Capture webhook secret    | Paste `whsec_...` into both .env locations | Step 2 completion       | P0 (CRITICAL) | BLOCKED     |
| 4    | Fill price IDs            | User provides or agent fetches from Stripe | Step 3 completion       | P1 (HIGH)     | BLOCKED     |
| 5    | Run validation            | npm run check:secrets → PASS               | Step 3 + 4              | P0 (CRITICAL) | BLOCKED     |
| 6    | Final green               | pytest + build verify                      | Step 5 + external tests | P0 (CRITICAL) | BLOCKED     |

---

## 🔐 Current Secret State

**Root `.env.local`:**

- STRIPE_LOGIN_EMAIL: `YOUR_STRIPE_EMAIL_HERE` (placeholder, needs fill)
- STRIPE_SECRET_KEY: `STRIPE_SECRET_KEY_REDACTED` (value redacted)
- STRIPE_WEBHOOK_SECRET: **EMPTY** ← BLOCKER

**micro-saas `/.env.local`:**

- STRIPE_WEBHOOK_SECRET: `STRIPE_WEBHOOK_SECRET_PLACEHOLDER` (placeholder)
- STRIPE_PRICE_ID_PRO: `price_test_pro_PLACEHOLDER` (placeholder)
- STRIPE_PRICE_ID_FOUNDING: `price_test_founding_PLACEHOLDER` (placeholder)

---

## 🚀 Krok 2: Stripe CLI Device Auth Flow

**Context:** Previous attempts failed because:

1. API keys expired/invalid (rotated offline by user)
2. Background terminal cannot complete interactive browser confirmation

**Solution:** User runs fresh Stripe CLI login locally (interactive PowerShell window)

**User Action (LOCAL - nie agent):**

```powershell
# 1. OTWÓRZ NOWE okno PowerShell
# 2. Uruchom:
stripe login

# 3. Zobaczysz pairing code (np. "top-wisely-brainy-snappy")
# 4. Odwiedź URL lub potwierdź w odpowiadającym linku
# 5. Po potwierdzeniu w przeglądarce, uruchom:
stripe listen --forward-to localhost:3000/api/webhooks/stripe --print-secret

# 6. Output: STRIPE_WEBHOOK_SECRET_PLACEHOLDER (KOPIUJ TĘ WARTOŚĆ)
```

---

## ✅ Następny Krok Po Uzyskaniu Webhook Secret

1. Prześlij wartość `whsec_...` do agenta
2. Agent automatycznie:
   - Wstawi do `micro-saas/.env.local`
   - Wstawi do root `/.env.local`
   - Uruchomi `npm run check:secrets`
   - Uruchomi final pytest + build
   - Utworzy koncowy REPORT

---

## 🛡️ Guardian Laws Compliance

- **G1 (Unity):** Single unified secret across .env files → harmonized
- **G5 (Transparency):** All steps documented, source clear → compliant
- **G6 (Authenticity):** Only real Stripe values, no fakes → enforced by hardened validation
- **G7 (Privacy):** Secrets never logged publicly, local-only → enforced (.gitignore active)
- **G8 (Nonmaleficence):** Placeholder detection prevents accidental deployments → active

---

## 📊 Resources

- Stripe CLI Path: `C:\Users\adiha\AppData\Local\Microsoft\WinGet\Packages\Stripe.StripeCli_Microsoft.Winget.Source_8wekyb3d8bbwe\stripe.exe`
- Webhook Endpoint: `http://localhost:3000/api/webhooks/stripe`
- Validation Script: `micro-saas/scripts/security/load-secrets.mjs` (rejects placeholders)
- Previous Session: session/ruff-secrets-runtime-completion-04-02.md
