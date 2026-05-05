# Micro SaaS PDF Analyzer MVP

This folder contains a greenfield Next.js MVP for the PDF analysis flow that was planned as a separate module inside the existing ADRION workspace.

## Scope of this implementation

- landing page
- upload flow with PDF file input
- server-side analysis route with real parser attempt + mock fallback
- local analysis history persistence and history view
- result page with premium upsell
- pricing connected to Stripe checkout route
- local entitlements and Free/Pro/Founding usage logic

## Why it is isolated

The root repository is a Python-first workspace. This module stays separate so Node dependencies, build scripts, and future billing integrations do not interfere with the current Flask and Waitress deployment files.

## Run locally

```bash
cd micro-saas
npm install
npm run dev
```

Then open:

- http://localhost:3000

## Environment setup

Create a local env file before testing checkout:

1. copy `.env.example` to `.env.local`
2. fill Stripe variables

Required for checkout:

- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ID_PRO`
- `STRIPE_PRICE_ID_FOUNDING`
- `NEXT_PUBLIC_APP_URL`

Required for daily report e-mail (09:00):

- `RESEND_API_KEY`
- `DAILY_REPORT_TO` (default: `punktodniesienia.adrian@gmail.com`)
- `DAILY_REPORT_FROM`
- `DAILY_REPORT_TOKEN` (optional but recommended)

Safe local secret handling:

- Keep real secret values only in `.env.local` (never in git).
- Non-secret references are stored in `lib/reference-constants.ts`.
- Validate required secret placeholders without printing values:

```bash
npm run check:secrets
```

- Validate `.env.example` template safety (used in CI):

- Validate `.env.example` template safety (used in CI):

```bash
npm run check:env-template
```

CI also blocks committed `.env.local` files and scans tracked files for Stripe-like secret patterns.

Optional but recommended for webhook testing:

- Stripe CLI with `stripe listen --forward-to localhost:3000/api/webhooks/stripe`
- Inspect local billing events with `GET /api/billing-events?limit=20`

## Current limitations

- parser can still fallback to mock mode for scan-heavy or encrypted PDFs
- there is no authentication, billing, or persistence yet
- webhook currently logs billing events locally to `.runtime/stripe-events.log` instead of syncing to a user database

Current local persistence:

- analyses: `.runtime/analysis-history.log`
- billing events: `.runtime/stripe-events.log`
- entitlements: `.runtime/entitlements.log`

History scope:

- `/history` and `GET /api/analyses` are scoped to the current local `userId`.
- `userId` is stored in browser localStorage (`pdf-saas-user-id`).

## Usage and plan behavior

- default plan is `free`
- free plan limit is 1 analysis per day per local user id
- checkout attaches local `userId` metadata to Stripe sessions
- webhook events update local entitlements, which then affect usage limits

Useful local endpoints:

- `GET /api/usage` with header `x-user-id`
- `GET /api/analyses?limit=20`
- `GET /api/billing-events?limit=20`
- `GET /api/funnel-events?limit=50`
- `GET /api/funnel-summary`
- `GET /api/funnel-export?format=json|csv`
- `POST /api/funnel-events`
- `POST /api/cron/daily-report`

Account surfaces:

- `/account` - per-user plan, usage, and billing overview
- `/history` - per-user analysis history
- `/onboarding` - first-week activation checklist

Funnel events captured in MVP:

- page views: home, upload, pricing, success
- analysis submit, success, and error
- checkout start and checkout error
- checkout success (from Stripe webhook)

Funnel KPI summary available in `/account`:

- analysis success rate
- checkout conversion rate
- checkout starts vs checkout successes

Export:

- `/account` includes buttons to export user-scoped KPI reports as JSON or CSV.

Daily report automation:

- `micro-saas/vercel.json` schedules `0 9 * * *` for `/api/cron/daily-report`.
- For local Windows scheduling, use:

```powershell
cd "micro-saas"
.\scripts\report\register-daily-report-task.ps1 -Endpoint "http://127.0.0.1:3000/api/cron/daily-report" -Token "YOUR_DAILY_REPORT_TOKEN"
```

Manual test trigger:

```powershell
Invoke-WebRequest -UseBasicParsing -Method POST -Uri "http://127.0.0.1:3000/api/cron/daily-report?token=YOUR_DAILY_REPORT_TOKEN"
```

Auth diagnostic (401/200 check):

```powershell
cd "micro-saas"
.\scripts\report\test-daily-report-auth.ps1
```

Optional explicit token:

```powershell
.\scripts\report\test-daily-report-auth.ps1 -Token "YOUR_DAILY_REPORT_TOKEN"
```

## Webhook test flow

1. start the app locally
2. run Stripe CLI forwarding to `/api/webhooks/stripe`
3. trigger a checkout or test event from Stripe
4. inspect `GET /api/billing-events?limit=20`
5. confirm local event log was appended in `.runtime/stripe-events.log`

## Suggested next step

1. Connect real extraction for PDF text.
2. Persist analysis sessions.
3. Add Stripe Checkout for the Pro plan.