param(
    [Parameter(Mandatory = $true)]
    [string]$RootPath,

    [Parameter(Mandatory = $true)]
    [string]$MarkdownOutputPath,

    [Parameter(Mandatory = $true)]
    [string]$CsvOutputPath
)

$ErrorActionPreference = 'Stop'

function Convert-ToAsciiKey {
    param(
        [string]$Value
    )

    $asciiReady = $Value.Replace([string][char]322, 'l').Replace([string][char]321, 'L').Replace([string][char]273, 'd').Replace([string][char]272, 'D')
    $normalized = $asciiReady.Normalize([Text.NormalizationForm]::FormD)
    $builder = New-Object System.Text.StringBuilder
    foreach ($char in $normalized.ToCharArray()) {
        $category = [Globalization.CharUnicodeInfo]::GetUnicodeCategory($char)
        if ($category -ne [Globalization.UnicodeCategory]::NonSpacingMark) {
            [void]$builder.Append($char)
        }
    }

    return $builder.ToString().Normalize([Text.NormalizationForm]::FormC).ToLowerInvariant()
}

function Get-PlanForFolder {
    param(
        [string]$Name
    )

    switch (Convert-ToAsciiKey -Value $Name) {
        'awatary i zdjecia' { return @{ Category = '02_DO_SORTOWANIA_I_DEDUPLIKACJI'; Target = 'Awatary i Zdjecia'; Action = 'move'; Reason = 'Folder mieszany, wymaga dalszego rozkladu na kategorie docelowe.' } }
        'dcim' { return @{ Category = '01_IMPORTY_ZRODLOWE'; Target = 'DCIM'; Action = 'keep'; Reason = 'Kanon dla wspolczesnych importow z telefonu.' } }
        'drive-download-20260401t061135z-3-001' { return @{ Category = '01_IMPORTY_ZRODLOWE'; Target = 'Drive_Download_20260401T061135Z_3_001'; Action = 'move'; Reason = 'Techniczny zrzut importu, powinien pozostac w strefie zrodlowej.' } }
        'kuzynka kuzynka' { return @{ Category = '04_OSOBY_I_RELACJE'; Target = 'Kuzynka Kuzynka'; Action = 'move'; Reason = 'Folder osobowy.' } }
        'love u babe' { return @{ Category = '04_OSOBY_I_RELACJE'; Target = 'Love U Babe'; Action = 'move'; Reason = 'Folder relacyjny.' } }
        'marta i adi' { return @{ Category = '04_OSOBY_I_RELACJE'; Target = 'Marta i Adi'; Action = 'move'; Reason = 'Folder relacyjny.' } }
        'mix' { return @{ Category = '02_DO_SORTOWANIA_I_DEDUPLIKACJI'; Target = 'MIX'; Action = 'review'; Reason = 'Glowna strefa duplikatow z DCIM i samojebki.' } }
        'mix zdjec i awatarow' { return @{ Category = '02_DO_SORTOWANIA_I_DEDUPLIKACJI'; Target = 'Mix_Zdjec_I_Awatarow'; Action = 'merge'; Reason = 'Nalezy scalic ze strefa miksow i awatarow.' } }
        'naprawde stare zdjecia' {
            if ($Name -cmatch 'Stare') {
                return @{ Category = '05_ARCHIWUM_HISTORYCZNE'; Target = 'Naprawde_Stare_Zdjecia\Czesc_2'; Action = 'merge'; Reason = 'Jeden z trzech wariantow archiwum historycznego.' }
            }
            return @{ Category = '05_ARCHIWUM_HISTORYCZNE'; Target = 'Naprawde_Stare_Zdjecia\Czesc_1'; Action = 'merge'; Reason = 'Jeden z trzech wariantow archiwum historycznego.' }
        }
        'naprawde stare zdjecia cz 2' { return @{ Category = '05_ARCHIWUM_HISTORYCZNE'; Target = 'Naprawde_Stare_Zdjecia\Czesc_3'; Action = 'merge'; Reason = 'Domkniecie wspolnego archiwum historycznego.' } }
        'od belgii po przez afryke az do miedzynarodowki' { return @{ Category = '06_PODROZE'; Target = 'Od_Belgii_Po_Przez_Afryke_Az_Do_Miedzynarodowki'; Action = 'move'; Reason = 'Spojny folder podrozniczy z lokalnymi duplikatami do redukcji.' } }
        'pozostale' { return @{ Category = '02_DO_SORTOWANIA_I_DEDUPLIKACJI'; Target = 'Pozostale'; Action = 'review'; Reason = 'Folder przejsciowy do rozdzielenia.' } }
        'samojebki' { return @{ Category = '02_DO_SORTOWANIA_I_DEDUPLIKACJI'; Target = 'samojebki'; Action = 'review'; Reason = 'Wysokie nakladanie z DCIM i MIX, wymaga decyzji po deduplikacji.' } }
        'screenshot' { return @{ Category = '01_IMPORTY_ZRODLOWE'; Target = 'ScreenShot'; Action = 'move'; Reason = 'Techniczny import zrzutow ekranu.' } }
        'studniowka adriana 9.02.2006' { return @{ Category = '03_WYDARZENIA'; Target = 'Studniowka_Adriana_09-02-2006'; Action = 'move'; Reason = 'Folder wydarzeniowy, nazwa do standaryzacji.' } }
        'studniowka marty' { return @{ Category = '03_WYDARZENIA'; Target = 'Studniowka_Marty_06-01-2007'; Action = 'merge'; Reason = 'Nalezy scalic z wariantem datowanym.' } }
        'studniowka marty 6.01.2007' { return @{ Category = '03_WYDARZENIA'; Target = 'Studniowka_Marty_06-01-2007'; Action = 'merge'; Reason = 'Folder kanoniczny po scaleniu dwoch wariantow.' } }
        'sylwester 2006-2007' { return @{ Category = '03_WYDARZENIA'; Target = 'Sylwester_2006-2007'; Action = 'move'; Reason = 'Folder wydarzeniowy z lokalnymi duplikatami do oczyszczenia.' } }
        'tajne od marty' { return @{ Category = '04_OSOBY_I_RELACJE'; Target = 'Tajne_Od_Marty'; Action = 'move'; Reason = 'Folder relacyjny.' } }
        'u bebe w domu' { return @{ Category = '03_WYDARZENIA'; Target = 'U_Bebe_W_Domu'; Action = 'move'; Reason = 'Folder wydarzeniowy lub rodzinny, zachowany jako osobna jednostka.' } }
        'zapasowe rar' { return @{ Category = '01_IMPORTY_ZRODLOWE'; Target = 'Zapasowe_RAR'; Action = 'move'; Reason = 'Pliki archiwalne, nie powinny mieszac sie z galeria.' } }
        'lysa gora' { return @{ Category = '03_WYDARZENIA'; Target = 'Lysa_Gora'; Action = 'move'; Reason = 'Folder wydarzeniowy lub lokalizacyjny.' } }
        default { return @{ Category = '02_DO_SORTOWANIA_I_DEDUPLIKACJI'; Target = $Name; Action = 'review'; Reason = 'Nieznany folder, wymagany przeglad reczny.' } }
    }
}

$topDirs = Get-ChildItem -LiteralPath $RootPath -Directory -Force | Sort-Object Name
$rows = New-Object System.Collections.Generic.List[object]

foreach ($dir in $topDirs) {
    $plan = Get-PlanForFolder -Name $dir.Name
    $files = (Get-ChildItem -LiteralPath $dir.FullName -File -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object).Count
    $subdirs = (Get-ChildItem -LiteralPath $dir.FullName -Directory -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object).Count
    $rows.Add([PSCustomObject]@{
        SourceName = $dir.Name
        SourcePath = $dir.FullName
        FileCount = $files
        SubdirCount = $subdirs
        ProposedCategory = $plan.Category
        ProposedTargetName = $plan.Target
        ProposedTargetPath = (Join-Path (Join-Path $RootPath $plan.Category) $plan.Target)
        Action = $plan.Action
        Reason = $plan.Reason
    })
}

$csvLines = New-Object System.Collections.Generic.List[string]
$csvLines.Add('SourceName;FileCount;SubdirCount;Action;ProposedCategory;ProposedTargetName;ProposedTargetPath;Reason')
foreach ($row in $rows) {
    $csvLines.Add(($row.SourceName, $row.FileCount, $row.SubdirCount, $row.Action, $row.ProposedCategory, $row.ProposedTargetName, $row.ProposedTargetPath, $row.Reason) -join ';')
}
[System.IO.File]::WriteAllLines($CsvOutputPath, $csvLines, [System.Text.UTF8Encoding]::new($false))

$grouped = $rows | Group-Object ProposedCategory
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('# Dry Run Reorganizacji Pictures')
$lines.Add('')
$lines.Add('Root: ' + $RootPath)
$lines.Add('Tryb: dry-run, bez wykonywania przenosin')
$lines.Add('')
$lines.Add('## Zasady')
$lines.Add('')
$lines.Add('1. DCIM pozostaje folderem kanonicznym dla wspolczesnych importow z telefonu.')
$lines.Add('2. MIX i samojebki pozostaja w strefie review do deduplikacji 1:1 przed ewentualnym scaleniem.')
$lines.Add('3. Foldery Studniowka Marty sa planowane do scalenia pod jedna nazwa kanoniczna.')
$lines.Add('4. Trzy warianty Naprawde stare zdjecia sa planowane do wspolnego archiwum historycznego.')
$lines.Add('5. Raport opisuje wylacznie docelowe rozmieszczenie, bez zmian na danych.')
$lines.Add('')
$lines.Add('## Mapa Folderow')
$lines.Add('')
foreach ($group in ($grouped | Sort-Object Name)) {
    $lines.Add('### ' + $group.Name)
    $lines.Add('')
    foreach ($row in ($group.Group | Sort-Object SourceName)) {
        $lines.Add('- ' + $row.SourceName + ' -> ' + $row.ProposedTargetPath + ' | action=' + $row.Action + ' | files=' + $row.FileCount + ' | reason=' + $row.Reason)
    }
    $lines.Add('')
}
$lines.Add('## Priorytet Wdrozenia')
$lines.Add('')
$lines.Add('1. Uporzadkowac strefe 01_IMPORTY_ZRODLOWE bez modyfikacji zawartosci plikow.')
$lines.Add('2. Oznaczyc MIX, samojebki, Pozostale i Awatary i Zdjecia jako obszary review do deduplikacji.')
$lines.Add('3. Scalac nazewnictwo wydarzen i archiwow historycznych dopiero po zatwierdzeniu nazw kanonicznych.')
$lines.Add('4. W drugim kroku wykonac deduplikacje potwierdzonych plikow 1:1.')
$lines.Add('')
$lines.Add('## Plik CSV')
$lines.Add('')
$lines.Add($CsvOutputPath)

[System.IO.File]::WriteAllLines($MarkdownOutputPath, $lines, [System.Text.UTF8Encoding]::new($false))
$lines
