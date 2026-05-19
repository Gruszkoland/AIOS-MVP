# UI-UX dla Systemu ADRION 369

## Mapa Nawigacji (od fundamentu do kodu)

```
WARSTWA 1: FILOZOFIA
  └─ Manifest Projektowy Systemu Vortex-Phi.txt
  └─ TEORIA-FUNDAMENTALNA_Vortex-369-Phi.txt  ← SCALONE (Enneagram+Fibonacci+Gurdżijew+Raport)
  └─ Bioarchitektura Złota Proporcja.txt

WARSTWA 2: HEURYSTYKI UX
  └─ Spirala Fibonacciego i Punkty 3-6-9 w UX.txt
  └─ UI_UX z Fibonaccim i 3-6-9.txt

WARSTWA 3: DESIGN SYSTEM (tokeny → kod)
  └─ System Design Tokens_ Vortex-Phi.txt      ← specyfikacja źródłowa
  └─ System Kolorów Vortex-Phi.txt              ← teoria kolorów + psychologia
  ├─ vortex-phi.css                             ← WYGENEROWANY — CSS Custom Properties + WCAG
  └─ tailwind.config.js                         ← WYGENEROWANY — konfiguracja Tailwind

WARSTWA 4: STYL & ESTETYKA
  └─ Design Stron dla agentów AI i Robotów.txt  ← styl HUD/FUI, inspiracje
  └─ Projekt _Agentic OS__ Layout i Grafika.txt ← layout Command Center + prompty AI
  └─ Przeanalizuj wszystkie podane strony...txt ← audit 5 benchmarków

WARSTWA 5: IMPLEMENTACJA
  └─ UI AI Daszbord... .txt                     ← iteracje v1→v11 (HTML/CSS/JS)
  └─ adrion-dashboard.html                      ← WYGENEROWANY — zunifikowany dashboard
```

## Jak zacząć

1. **Teoria** → Przeczytaj `Manifest Projektowy` i `TEORIA-FUNDAMENTALNA`
2. **Zasady UX** → Przejrzyj `Spirala Fibonacciego` i `UI_UX z Fibonaccim`
3. **Tokeny** → Zaimportuj `vortex-phi.css` lub skonfiguruj `tailwind.config.js`
4. **Wdróż** → Otwórz `adrion-dashboard.html` jako punkt startowy

## Pliki Usunięte (scalenie)

| Plik (usunięty) | Włączony do |
|---|---|
| Styl graficzny dla stron AI_Robotyka.txt | Identyczny z Design Stron — usunięty |
| Enneagram, Rodin i 3-6-9.txt | TEORIA-FUNDAMENTALNA (Część I) |
| Fibonacciego, 3-6-9 i Złota Proporcja.txt | TEORIA-FUNDAMENTALNA (Część II) |
| Prawo Siedmiu i Prawo Trzech (Gurdżijew).txt | TEORIA-FUNDAMENTALNA (Część III) |
| Raport Systemowy: Paradygmat 3-6-9.txt | TEORIA-FUNDAMENTALNA (Część IV) |

## WCAG Compliance

Wszystkie pary kolorów w `vortex-phi.css` mają udokumentowane contrast ratios:
- Tekst główny na tle: **14.7:1** (AAA ✅)
- Tekst pomocniczy: **7.2:1** (AAA ✅)
- Akcenty (cyan/amber): **10.4–12.8:1** (AAA ✅)
- Statusy (error/success): **5.0–6.3:1** (AA ✅)

## Matematyka Systemu

| Parametr | Wartość | Redukcja 3-6-9 |
|---|---|---|
| V-Unit (spacing) | 9px | 9 |
| Font base | 15px | 6 |
| Font H1 | 63px | 9 |
| Motion fast | 174ms | 3 |
| Motion standard | 396ms | 9 |
| Motion emphasis | 528ms | 6 |
| Grid major | 61.8% | φ |
| Grid minor | 38.2% | 1-φ |
