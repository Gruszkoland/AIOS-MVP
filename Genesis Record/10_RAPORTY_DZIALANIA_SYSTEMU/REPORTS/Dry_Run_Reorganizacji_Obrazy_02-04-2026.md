# Dry Run Reorganizacji Pictures

Root: C:\Users\adiha\Pictures
Tryb: dry-run, bez wykonywania przenosin

## Zasady

1. DCIM pozostaje folderem kanonicznym dla wspolczesnych importow z telefonu.
2. MIX i samojebki pozostaja w strefie review do deduplikacji 1:1 przed ewentualnym scaleniem.
3. Foldery Studniowka Marty sa planowane do scalenia pod jedna nazwa kanoniczna.
4. Trzy warianty Naprawde stare zdjecia sa planowane do wspolnego archiwum historycznego.
5. Raport opisuje wylacznie docelowe rozmieszczenie, bez zmian na danych.

## Mapa Folderow

### 01_IMPORTY_ZRODLOWE

- DCIM -> C:\Users\adiha\Pictures\01_IMPORTY_ZRODLOWE\DCIM | action=keep | files=338 | reason=Kanon dla wspolczesnych importow z telefonu.
- drive-download-20260401T061135Z-3-001 -> C:\Users\adiha\Pictures\01_IMPORTY_ZRODLOWE\Drive_Download_20260401T061135Z_3_001 | action=move | files=199 | reason=Techniczny zrzut importu, powinien pozostac w strefie zrodlowej.
- ScreenShot -> C:\Users\adiha\Pictures\01_IMPORTY_ZRODLOWE\ScreenShot | action=move | files=6 | reason=Techniczny import zrzutow ekranu.
- Zapasowe RAR -> C:\Users\adiha\Pictures\01_IMPORTY_ZRODLOWE\Zapasowe_RAR | action=move | files=16 | reason=Pliki archiwalne, nie powinny mieszac sie z galeria.

### 02_DO_SORTOWANIA_I_DEDUPLIKACJI

- Awatary i zdjęcia -> C:\Users\adiha\Pictures\02_DO_SORTOWANIA_I_DEDUPLIKACJI\Awatary i Zdjecia | action=move | files=46 | reason=Folder mieszany, wymaga dalszego rozkladu na kategorie docelowe.
- MIX -> C:\Users\adiha\Pictures\02_DO_SORTOWANIA_I_DEDUPLIKACJI\MIX | action=review | files=302 | reason=Glowna strefa duplikatow z DCIM i samojebki.
- Mix zdjec i awatarow -> C:\Users\adiha\Pictures\02_DO_SORTOWANIA_I_DEDUPLIKACJI\Mix_Zdjec_I_Awatarow | action=merge | files=1 | reason=Nalezy scalic ze strefa miksow i awatarow.
- Pozostałe -> C:\Users\adiha\Pictures\02_DO_SORTOWANIA_I_DEDUPLIKACJI\Pozostale | action=review | files=18 | reason=Folder przejsciowy do rozdzielenia.
- samojebki -> C:\Users\adiha\Pictures\02_DO_SORTOWANIA_I_DEDUPLIKACJI\samojebki | action=review | files=9 | reason=Wysokie nakladanie z DCIM i MIX, wymaga decyzji po deduplikacji.

### 03_WYDARZENIA

- Łysa Góra -> C:\Users\adiha\Pictures\03_WYDARZENIA\Lysa_Gora | action=move | files=58 | reason=Folder wydarzeniowy lub lokalizacyjny.
- Studniówka Adriana 9.02.2006 -> C:\Users\adiha\Pictures\03_WYDARZENIA\Studniowka_Adriana_09-02-2006 | action=move | files=139 | reason=Folder wydarzeniowy, nazwa do standaryzacji.
- Studniówka Marty -> C:\Users\adiha\Pictures\03_WYDARZENIA\Studniowka_Marty_06-01-2007 | action=merge | files=144 | reason=Nalezy scalic z wariantem datowanym.
- Studniówka Marty 6.01.2007 -> C:\Users\adiha\Pictures\03_WYDARZENIA\Studniowka_Marty_06-01-2007 | action=merge | files=4 | reason=Folder kanoniczny po scaleniu dwoch wariantow.
- Sylwester 2006-2007 -> C:\Users\adiha\Pictures\03_WYDARZENIA\Sylwester_2006-2007 | action=move | files=432 | reason=Folder wydarzeniowy z lokalnymi duplikatami do oczyszczenia.
- U Bebe w Domu -> C:\Users\adiha\Pictures\03_WYDARZENIA\U_Bebe_W_Domu | action=move | files=14 | reason=Folder wydarzeniowy lub rodzinny, zachowany jako osobna jednostka.

### 04_OSOBY_I_RELACJE

- Kuzynka Kuzynka -> C:\Users\adiha\Pictures\04_OSOBY_I_RELACJE\Kuzynka Kuzynka | action=move | files=20 | reason=Folder osobowy.
- Love U Babe -> C:\Users\adiha\Pictures\04_OSOBY_I_RELACJE\Love U Babe | action=move | files=24 | reason=Folder relacyjny.
- Marta i Adi -> C:\Users\adiha\Pictures\04_OSOBY_I_RELACJE\Marta i Adi | action=move | files=14 | reason=Folder relacyjny.
- Tajne od Marty -> C:\Users\adiha\Pictures\04_OSOBY_I_RELACJE\Tajne_Od_Marty | action=move | files=14 | reason=Folder relacyjny.

### 05_ARCHIWUM_HISTORYCZNE

- Naprawde stare zdjecia -> C:\Users\adiha\Pictures\05_ARCHIWUM_HISTORYCZNE\Naprawde_Stare_Zdjecia\Czesc_1 | action=merge | files=1 | reason=Jeden z trzech wariantow archiwum historycznego.
- Naprawde Stare zdjęcia -> C:\Users\adiha\Pictures\05_ARCHIWUM_HISTORYCZNE\Naprawde_Stare_Zdjecia\Czesc_2 | action=merge | files=100 | reason=Jeden z trzech wariantow archiwum historycznego.
- Naprawde stare zdjęcia cz 2 -> C:\Users\adiha\Pictures\05_ARCHIWUM_HISTORYCZNE\Naprawde_Stare_Zdjecia\Czesc_3 | action=merge | files=8 | reason=Domkniecie wspolnego archiwum historycznego.

### 06_PODROZE

- Od Belgii Po przez Afryke az do Miedzynarodowki -> C:\Users\adiha\Pictures\06_PODROZE\Od_Belgii_Po_Przez_Afryke_Az_Do_Miedzynarodowki | action=move | files=238 | reason=Spojny folder podrozniczy z lokalnymi duplikatami do redukcji.

## Priorytet Wdrozenia

1. Uporzadkowac strefe 01_IMPORTY_ZRODLOWE bez modyfikacji zawartosci plikow.
2. Oznaczyc MIX, samojebki, Pozostale i Awatary i Zdjecia jako obszary review do deduplikacji.
3. Scalac nazewnictwo wydarzen i archiwow historycznych dopiero po zatwierdzeniu nazw kanonicznych.
4. W drugim kroku wykonac deduplikacje potwierdzonych plikow 1:1.

## Plik CSV

C:\Users\adiha\162 demencje w schemacie 369\Genesis Record\10_RAPORTY_DZIALANIA_SYSTEMU\REPORTS\Dry_Run_Reorganizacji_Obrazy_02-04-2026.csv
