# Zautomatyzowanego SaaS

## Cel
Zbudowac i uruchomic zautomatyzowany mikro-SaaS do analizy PDF, ktory prowadzi uzytkownika przez pelny przeplyw:
landing -> upload PDF -> analiza -> wynik -> pricing -> checkout.

Docelowo system ma byc gotowy do walidacji pierwszego przychodu oraz dalszej automatyzacji: parser PDF, platnosci, zapis sesji, onboarding i podstawowa analityka.

## Aktualny etap
Etap 5 z 6: Trwale logowanie historii analiz i zdarzen billingowych jest wdrozone lokalnie, ale srodowisko nadal nie pozwala na runtime test, bo brakuje `node` i `npm` w PATH.

Status biezacy:
- `done`: greenfield modul `micro-saas` zostal utworzony
- `done`: landing, upload, result i pricing sa zaimplementowane
- `done`: API analizy PDF istnieje i ma fallback do mock
- `done`: checkout Stripe jest przygotowany na poziomie kodu
- `done`: webhook Stripe i lokalny billing log sa przygotowane na poziomie kodu
- `done`: historia analiz jest zapisywana lokalnie i dostepna przez API oraz widok historii
- `done`: lokalna identyfikacja uzytkownika i plan dostepu Free/Pro/Founding sa wdrozone
- `done`: historia analiz i endpoint `api/analyses` sa ograniczone do biezacego `userId`
- `done`: widok `/account` pokazuje plan, usage i billing events dla biezacego `userId`
- `done`: lokalna analityka lejka zapisuje zdarzenia funnel per `userId` i jest widoczna w `/account`
- `done`: dashboard konta pokazuje KPI lejka (success rate i checkout conversion)
- `done`: dashboard konta pozwala eksportowac raport KPI lejka do JSON i CSV
- `done`: raport dzienny 09:00 jest skonfigurowany do wysylki na `punktodniesienia.adrian@gmail.com`
- `in-progress`: przygotowanie srodowiska do realnego uruchomienia i testu end-to-end
- `planned`: utrwalenie danych, dostepow i automatyzacji po platnosci

## Plan wdrozenia

### Etap 1: Architektura i szkielet MVP
Status: `done`

Kroki:
1. Wydzielic nowy modul `micro-saas`, aby nie mieszac Node.js z istniejacym stackiem Python.
2. Dodac Next.js 15, TypeScript, Tailwind i podstawowa strukture aplikacji.
3. Przygotowac wspolny layout, style globalne i nawigacje.

Kryterium ukonczenia:
- Modul startowy istnieje i ma komplet plikow konfiguracyjnych.

### Etap 2: Przeplyw produktu i backend MVP
Status: `done`

Kroki:
1. Dodac landing page z jasna propozycja wartosci.
2. Dodac widok uploadu PDF.
3. Dodac wynik analizy z sekcja premium unlock.
4. Dodac pricing page jako pomost do monetyzacji.
5. Dodac route `api/analyze` z walidacja pliku i fallbackiem.

Kryterium ukonczenia:
- Uzytkownik moze przejsc przez caly przeplyw MVP bez integracji z zewnetrznymi systemami.

### Etap 3: Uruchomienie lokalne i walidacja runtime
Status: `in-progress`

Kroki:
1. Zainstalowac Node.js LTS i npm w systemie.
2. Uruchomic `npm install` w `micro-saas`.
3. Uruchomic `npm run dev` i sprawdzic wszystkie trasy.
4. Zweryfikowac upload PDF i odpowiedz `api/analyze`.
5. Zweryfikowac checkout flow w trybie konfiguracji testowej Stripe.

Kryterium ukonczenia:
- Aplikacja uruchamia sie lokalnie bez bledow i wszystkie glowne trasy sa sprawdzone recznie.

### Etap 4: Monetyzacja i automatyzacja dostepu
Status: `in-progress`

Kroki:
1. Dodac prawidlowe `STRIPE_PRICE_ID_PRO` i `STRIPE_PRICE_ID_FOUNDING`.
2. Dodac webhook Stripe do nadawania dostepu po platnosci.
3. Wprowadzic prosty model dostepu Free/Pro/Founding.
4. Dodac komunikaty sukcesu, anulowania i bledow platnosci.
5. Dodac log lub podglad zdarzen billingowych do testow lokalnych.

Kryterium ukonczenia:
- Platnosc testowa skutkuje nadaniem uprawnien albo zapisem statusu klienta.

### Etap 5: Dane, sesje i wartosc produktu
Status: `in-progress`

Kroki:
1. Dodac zapisywanie historii analiz.
2. Dodac identyfikacje uzytkownika lub proste konto.
3. Dodac trwaly zapis wynikow i podstawowe limity planow.
4. Rozszerzyc parser PDF o lepsza obsluge dokumentow skanowanych.
5. Udostepnic prosty widok historii analiz dla walidacji wartosci.

Kryterium ukonczenia:
- Uzytkownik widzi swoje analizy i status planu po ponownym wejsciu.

### Etap 6: Operacjonalizacja i pierwsza walidacja przychodu
Status: `planned`

Kroki:
1. Dodac podstawowa analityke lejka.
2. Dodac onboarding po platnosci.
3. Przygotowac prosta oferte dla pierwszych klientow.
4. Wykonac test z realnym use case PDF dla jednej niszy.
5. Zmierzyc: wejscia, uploady, checkout start, checkout success.
6. Dodac prosty onboarding po sukcesie platnosci.

Kryterium ukonczenia:
- System jest gotowy do pierwszej walidacji rynkowej i mierzy kluczowe kroki konwersji.

## Najblizsze kroki
1. Zainstalowac Node.js i npm.
2. Uruchomic lokalnie `micro-saas`.
3. Skonfigurowac testowe dane Stripe w `.env.local`.
4. Sprawdzic pelny scenariusz upload -> analiza -> pricing -> checkout.

## Checklista uruchomienia lokalnego po instalacji Node.js

### A. Weryfikacja srodowiska
- [ ] Otworzyc nowy terminal po instalacji Node.js.
- [ ] Sprawdzic `node -v`.
- [ ] Sprawdzic `npm -v`.
- [ ] Wejsc do katalogu `C:\Users\adiha\162 demencje w schemacie 369\micro-saas`.

### B. Instalacja zaleznosci
- [ ] Uruchomic `npm install`.
- [ ] Potwierdzic, ze instalacja konczy sie bez bledow krytycznych.
- [ ] Sprawdzic, czy powstal katalog `node_modules`.

### C. Konfiguracja lokalna
- [ ] Skopiowac `micro-saas/.env.example` do `micro-saas/.env.local`.
- [ ] Ustawic `NEXT_PUBLIC_APP_URL=http://localhost:3000`.
- [ ] Jesli checkout ma byc testowany: ustawic `STRIPE_SECRET_KEY`.
- [ ] Jesli checkout ma byc testowany: ustawic `STRIPE_PRICE_ID_PRO`.
- [ ] Jesli checkout ma byc testowany: ustawic `STRIPE_PRICE_ID_FOUNDING`.

### D. Start aplikacji
- [ ] Uruchomic `npm run dev`.
- [ ] Otworzyc `http://localhost:3000`.
- [ ] Potwierdzic, ze laduje sie landing page bez bledu 500.

### E. Test tras aplikacji
- [ ] Wejsc na `/upload`.
- [ ] Wejsc na `/result` bez payload i potwierdzic stan pusty.
- [ ] Wejsc na `/pricing`.
- [ ] Potwierdzic, ze `/success?plan=pro` otwiera sie poprawnie.

### F. Test analizy PDF
- [ ] Przygotowac testowy plik PDF mniejszy niz 10 MB.
- [ ] Wgrac plik na `/upload`.
- [ ] Potwierdzic przekierowanie na `/result`.
- [ ] Sprawdzic, czy wynik pokazuje `real parser` albo `mock parser`.
- [ ] Sprawdzic, czy widac `summary`, `verdict`, `signals found` i `premium unlock`.

### G. Test checkout
- [ ] Kliknac plan `Pro` na `/pricing`.
- [ ] Potwierdzic, ze bez konfiguracji Stripe pojawia sie kontrolowany blad.
- [ ] Po dodaniu testowych danych Stripe potwierdzic przekierowanie do Stripe Checkout.
- [ ] Po sukcesie potwierdzic przekierowanie na `/success?plan=pro`.

### H. Kontrola koncowa
- [ ] Sprawdzic, czy w konsoli dev servera nie ma runtime errors.
- [ ] Sprawdzic, czy `api/analyze` nie zwraca 400 dla poprawnego PDF.
- [ ] Sprawdzic, czy `api/checkout` zwraca 503 tylko wtedy, gdy Stripe nie jest skonfigurowany.
- [ ] Sprawdzic, czy `api/billing-events` zwraca liste zdarzen lub pusty wynik bez bledu.
- [ ] Sprawdzic, czy `api/analyses` zwraca historie analiz lub pusty wynik bez bledu.
- [ ] Sprawdzic, czy `api/usage` zwraca aktualny plan i limity dla `x-user-id`.
- [ ] Sprawdzic, czy trasa `/history` wyswietla najnowsze wpisy po analizie PDF.
- [ ] Zapisac wynik testu i zaktualizowac aktualny etap w tym pliku.

## Checklista webhook Stripe po uruchomieniu Node.js

### A. Konfiguracja webhooka
- [ ] Ustawic `STRIPE_WEBHOOK_SECRET` w `micro-saas/.env.local`.
- [ ] Uruchomic lokalnie aplikacje `npm run dev`.
- [ ] Uruchomic Stripe CLI: `stripe listen --forward-to localhost:3000/api/webhooks/stripe`.

### B. Test zdarzenia
- [ ] Wyslac testowy event `checkout.session.completed` albo wykonac testowy checkout.
- [ ] Potwierdzic odpowiedz 200 z webhook route.
- [ ] Potwierdzic, ze event zostal zapisany do `.runtime/stripe-events.log`.
- [ ] Otworzyc `GET /api/billing-events?limit=20` i sprawdzic, czy event jest widoczny.

### C. Walidacja zachowania
- [ ] Potwierdzic, ze `checkout.session.completed` daje `accessState=active`.
- [ ] Potwierdzic, ze `invoice.payment_succeeded` daje `accessState=payment_received`.
- [ ] Potwierdzic, ze `customer.subscription.deleted` daje `accessState=canceled`.
- [ ] Potwierdzic, ze brak lub zla sygnatura webhooka zwraca kontrolowany blad 400.

### Polecenia robocze
```powershell
cd "C:\Users\adiha\162 demencje w schemacie 369\micro-saas"
node -v
npm -v
npm install
Copy-Item .env.example .env.local
npm run dev
```

## Dziennik postepu
- 2026-03-30 20:00: Rozpoczeto wdrozenie izolowanego modulu `micro-saas`.
- 2026-03-30 20:06: Dodano szkielet Next.js 15 + TypeScript + Tailwind.
- 2026-03-30 20:08: Zaimplementowano flow `landing -> upload -> result -> pricing`.
- 2026-03-30 20:11: Potwierdzono brak bledow statycznych oraz brak `node` i `npm` w PATH.
- 2026-03-30 20:18: Dodano zaleznosci pod parser PDF i Stripe.
- 2026-03-30 20:22: Dodano parser PDF z fallbackiem oraz checkout Stripe na poziomie kodu.
- 2026-03-30 20:28: Potwierdzono brak bledow statycznych po rozszerzeniu funkcji.
- 2026-03-30 20:35: Sporządzono plan celu i oznaczono aktualny etap jako uruchomienie lokalne i walidacja runtime.
- 2026-03-30 20:41: Dodano szczegolowa checkliste uruchomienia lokalnego po instalacji Node.js.
- 2026-03-30 20:48: Dodano webhook Stripe, lokalny billing log oraz endpoint podgladu zdarzen billingowych.
- 2026-03-30 20:56: Dodano trwaly zapis historii analiz, endpoint `api/analyses` i widok historii `/history`.
- 2026-03-30 20:57: Potwierdzono brak bledow statycznych dla nowych plikow etapu 5.
- 2026-03-30 21:05: Dodano lokalna identyfikacje uzytkownika, endpoint `api/usage` i limity planu Free (1 analiza dziennie).
- 2026-03-30 21:06: Polaczono checkout/webhook z entitlements (`.runtime/entitlements.log`) przez `userId` w metadata Stripe.
- 2026-03-30 21:07: Potwierdzono brak bledow statycznych po wdrozeniu logiki dostepu i limitow.
- 2026-03-30 21:12: Zmieniono widok `/history` oraz `api/analyses` na zakres per `userId`.
- 2026-03-30 21:13: Potwierdzono brak bledow statycznych po wdrozeniu user-scoped historii.
- 2026-03-30 21:20: Ujednolicono bezpieczny standard sekretow w `micro-saas/.env.example` (stale niesekretne + placeholdery sekretow, bez realnych wartosci).
- 2026-03-30 21:21: Dodano `micro-saas/lib/reference-constants.ts` z niesekretnymi stalymi referencyjnymi.
- 2026-03-30 21:22: Dodano `micro-saas/scripts/security/load-secrets.mjs` i skrypt `npm run check:secrets` do walidacji `.env.local` bez wyswietlania sekretow.
- 2026-03-30 21:22: Uzupelniono `micro-saas/README.md` o bezpieczny workflow ladowania sekretow lokalnych.
- 2026-03-30 21:28: Dodano skrypt `micro-saas/scripts/security/check-env-template.mjs` walidujacy bezpieczenstwo `.env.example`.
- 2026-03-30 21:28: Dodano `npm run check:env-template` w `micro-saas/package.json`.
- 2026-03-30 21:29: Dodano workflow CI `.github/workflows/micro-saas-security-check.yml` uruchamiany dla zmian w `micro-saas/**`.
- 2026-03-30 21:29: Zaktualizowano `micro-saas/README.md` o instrukcje lokalnego i CI checku szablonu env.
- 2026-03-30 21:19: Dodano user-scoped endpoint `api/billing-events` i widok `/account` z planem, usage i billing status.
- 2026-03-30 21:20: Potwierdzono brak bledow statycznych po wdrozeniu dashboardu konta.
- 2026-03-30 21:28: Dodano lokalny event log lejka (`api/funnel-events`) i tracking kluczowych zdarzen w MVP.
- 2026-03-30 21:29: Dodano trase `/onboarding` oraz podpiecie z `/success` po platnosci.
- 2026-03-30 21:30: Rozszerzono `/account` o podglad ostatnich zdarzen funnel dla biezacego usera.
- 2026-03-30 21:31: Potwierdzono brak bledow statycznych po wdrozeniu analityki i onboardingu.
- 2026-03-30 21:34: Dodano drugi job CI `secret-hygiene-scan` w `.github/workflows/micro-saas-security-check.yml`.
- 2026-03-30 21:34: CI blokuje commit `*.env.local` i skanuje tracked files pod wzorce Stripe-like secret keys.
- 2026-03-30 21:35: Uzupelniono `micro-saas/README.md` o informacje o CI secret-hygiene scan.
- 2026-03-30 21:38: Dodano `api/funnel-summary` i KPI lejka w `/account` (analysis success rate, checkout conversion rate).
- 2026-03-30 21:39: Podpieto webhook Stripe do eventow `checkout_success` i `subscription_canceled` w lokalnej analityce.
- 2026-03-30 21:40: Potwierdzono brak bledow statycznych po wdrozeniu KPI lejka.
- 2026-03-30 21:46: Dodano endpoint `api/funnel-export` z formatami JSON/CSV i user-scoped danymi raportowymi.
- 2026-03-30 21:47: Dodano przyciski eksportu KPI w `/account` (JSON i CSV).
- 2026-03-30 21:48: Potwierdzono brak bledow statycznych po wdrozeniu eksportu raportow.
- 2026-03-30 21:56: Dodano endpoint `api/cron/daily-report` z wysylka e-mail przez Resend.
- 2026-03-30 21:57: Dodano harmonogram 09:00 (`micro-saas/vercel.json`) i skrypt Windows Task Scheduler.
- 2026-03-30 21:58: Ustawiono domyslny odbiorca raportu: `punktodniesienia.adrian@gmail.com` w `.env.example`.
- 2026-03-30 21:59: Potwierdzono brak bledow statycznych po wdrozeniu dziennego raportu.

## Podsumowanie sesji
- Wykonane: Istnieje fundament produktu, parser fallback, checkout route, webhook Stripe, lokalny billing log, historia analiz z API/widokiem, lokalna logika planow i limitow, dashboard konta per user oraz analityka lejka z onboardingiem.
- Pozostalo: Uruchomienie runtime, test end-to-end, oraz docelowa synchronizacja dostepu i analityki z baza produkcyjna.
- Blokery: Brak `node` i `npm` w aktualnym srodowisku.

## Mikro-streszczenie
- Ustalono glowny cel
- Rozpisano etapy wdrozenia
- Oznaczono aktualny etap
- Potwierdzono stan MVP
- Zapisano najblizsze kroki
- Dodano dziennik postepu