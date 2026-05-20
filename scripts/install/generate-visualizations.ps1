# ============================================================================
# GENERATE-VISUALIZATIONS.PS1 - Create Mermaid diagrams and visual maps
# Purpose: Generate architecture diagrams, project relationships, file distribution charts
# Output: Generates VISUALIZATIONS.md with embedded Mermaid diagrams
# ============================================================================

param(
    [string]$VaultRoot = "C:\Users\adiha\Desktop\Dokumentacja\Obsydian-synchronizacja dokumentów\_PROJEKTY_SCALONE",
    [string]$OutputFile = "VISUALIZATIONS.md"
)

# Color configuration
$colors = @{
    Info = 'Cyan'
    Success = 'Green'
    Warning = 'Yellow'
    Error = 'Red'
}

function Write-Log {
    param([string]$Message, [string]$Type = 'Info')
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = $colors[$Type]
    Write-Host "[$timestamp] " -NoNewline -ForegroundColor DarkGray
    Write-Host $Message -ForegroundColor $color
}

try {
    Write-Log "Starting visualization generation..." Info
    Write-Log "Vault root: $VaultRoot" Info
    
    if (-not (Test-Path $VaultRoot)) {
        Write-Log "ERROR: Vault root not found at $VaultRoot" Error
        exit 1
    }

    # Collect project information
    Write-Log "Analyzing projects..." Info
    $projects = @()
    $projectDirs = Get-ChildItem -Path $VaultRoot -Directory | Where-Object { $_.Name -notmatch '^_' }
    
    foreach ($dir in $projectDirs) {
        $files = Get-ChildItem -Path $dir.FullName -File -Recurse
        $mdFiles = $files | Where-Object { $_.Extension -eq '.md' }
        
        $projects += @{
            Name = $dir.Name
            TotalFiles = $files.Count
            MarkdownFiles = $mdFiles.Count
            TotalSize = ($files | Measure-Object -Sum Length).Sum
            Path = $dir.FullName
        }
    }
    
    $projects = $projects | Sort-Object -Property TotalFiles -Descending
    
    Write-Log "Found $($projects.Count) projects" Info
    
    # Generate markdown with visualizations
    $markdown = @()
    $markdown += "# 📊 Wizualizacje Knowledge Bank"
    $markdown += ""
    $markdown += "> **Wykresy i Diagramy** — Wizualne reprezentacje struktury, rozmiarów i relacji"
    $markdown += ""
    $markdown += "---"
    $markdown += ""
    
    # 1. PROJECT DISTRIBUTION - Pie chart
    $markdown += "## 📈 Dystrybucja Projektów"
    $markdown += ""
    $markdown += "### Liczba Plików na Projekt"
    $markdown += ""
    
    $markdown += "``````mermaid"
    $markdown += "pie title Dystrybucja Plików Wg Projektów"
    
    foreach ($project in $projects | Select-Object -First 10) {
        $projectLabel = if ($project.Name.Length -gt 20) {
            $project.Name.Substring(0, 17) + "..."
        } else {
            $project.Name
        }
        $markdown += "`"$projectLabel`" : $($project.TotalFiles)"
    }
    
    $othersCount = ($projects | Select-Object -Skip 10 | Measure-Object -Sum TotalFiles).Sum
    if ($othersCount -gt 0) {
        $markdown += "`"Pozostałe`" : $othersCount"
    }
    
    $markdown += "``````"
    $markdown += ""
    
    # 2. FILE SIZE DISTRIBUTION - Bar chart
    $markdown += "### Rozmiar Projektów (MB)"
    $markdown += ""
    
    $markdown += "``````mermaid"
    $markdown += "bar"
    $markdown += "  title Rozmiar Projektów"
    $markdown += "  x-axis ["
    
    $xLabels = $projects | Select-Object -First 8 | ForEach-Object {
        $name = if ($_.Name.Length -gt 15) { $_.Name.Substring(0, 12) + "..." } else { $_.Name }
        "`"$name`""
    }
    $markdown += "    $($xLabels -join ', ')"
    $markdown += "  ]"
    $markdown += "  y-axis `"Rozmiar (MB)`" 0 --> $([math]::Ceiling(($projects[0].TotalSize / 1MB) * 1.2))"
    $markdown += "  line ["
    
    $sizes = $projects | Select-Object -First 8 | ForEach-Object {
        [math]::Round($_.TotalSize / 1MB, 1)
    }
    $markdown += "    $($sizes -join ', ')"
    $markdown += "  ]"
    $markdown += "``````"
    $markdown += ""
    
    # 3. MARKDOWN FILE DISTRIBUTION
    $markdown += "### Rozmieszczenie Plików Markdown"
    $markdown += ""
    
    $markdown += "``````mermaid"
    $markdown += "pie title Pliki Markdown wg Projektów"
    
    foreach ($project in $projects | Select-Object -First 10) {
        if ($project.MarkdownFiles -gt 0) {
            $projectLabel = if ($project.Name.Length -gt 20) {
                $project.Name.Substring(0, 17) + "..."
            } else {
                $project.Name
            }
            $markdown += "`"$projectLabel`" : $($project.MarkdownFiles)"
        }
    }
    
    $markdown += "``````"
    $markdown += ""
    $markdown += "[⬆ Wróć do góry](#-wizualizacje-knowledge-bank)"
    $markdown += ""
    
    # 4. PROJECT STRUCTURE - Flowchart
    $markdown += "---"
    $markdown += ""
    $markdown += "## 🗂️ Struktura Hierarchii Projektów"
    $markdown += ""
    
    $markdown += "``````mermaid"
    $markdown += "graph TD"
    $markdown += "  KB[Knowledge Bank<br/>8,325 Plików]"
    
    $counter = 0
    foreach ($project in $projects | Select-Object -First 12) {
        $counter++
        $safeId = "P$counter"
        $projectLabel = if ($project.Name.Length -gt 20) {
            $project.Name.Substring(0, 20) + "..."
        } else {
            $project.Name
        }
        $markdown += "  $safeId[$projectLabel<br/>$($project.TotalFiles) files]"
        $markdown += "  KB --> $safeId"
    }
    
    $markdown += "``````"
    $markdown += ""
    $markdown += "[⬆ Wróć do góry](#-wizualizacje-knowledge-bank)"
    $markdown += ""
    
    # 5. FILE TYPE DISTRIBUTION - Across entire KB
    $markdown += "---"
    $markdown += ""
    $markdown += "## 📁 Typy Plików w Knowledge Bank"
    $markdown += ""
    
    Write-Log "Analyzing file types..." Info
    $allFiles = Get-ChildItem -Path $VaultRoot -File -Recurse
    $fileTypes = @{}
    
    foreach ($file in $allFiles) {
        $ext = if ($file.Extension) { $file.Extension.ToLower() } else { "(brak)" }
        $fileTypes[$ext] = ($fileTypes[$ext] -as [int]) + 1
    }
    
    $sortedTypes = $fileTypes.GetEnumerator() | Sort-Object -Property Value -Descending | Select-Object -First 12
    
    $markdown += "``````mermaid"
    $markdown += "pie title Typy Plików w KB"
    
    foreach ($type in $sortedTypes) {
        $typeName = if ($type.Key -eq "(brak)") { "Bez rozszerzenia" } else { $type.Key.TrimStart('.') }
        $markdown += "`"$typeName`" : $($type.Value)"
    }
    
    $markdown += "``````"
    $markdown += ""
    $markdown += "[⬆ Wróć do góry](#-wizualizacje-knowledge-bank)"
    $markdown += ""
    
    # 6. DETAILED PROJECT STATS TABLE
    $markdown += "---"
    $markdown += ""
    $markdown += "## 📋 Szczegółowa Tabela Projektów"
    $markdown += ""
    
    $markdown += "| Projekt | Pliki | MD | Rozmiar | Średni |"
    $markdown += "|---------|-------|----|---------| -------|"
    
    foreach ($project in $projects) {
        $sizeMB = [math]::Round($project.TotalSize / 1MB, 2)
        $avgSize = [math]::Round($project.TotalSize / $project.TotalFiles / 1KB, 1)
        $projectLink = "[$($project.Name)](_MAPY/$($project.Name) - MAPA.md)"
        $markdown += "| $projectLink | $($project.TotalFiles) | $($project.MarkdownFiles) | $sizeMB MB | $avgSize KB |"
    }
    
    $markdown += ""
    $markdown += "[⬆ Wróć do góry](#-wizualizacje-knowledge-bank)"
    $markdown += ""
    
    # 7. STATISTICS SUMMARY
    $markdown += "---"
    $markdown += ""
    $markdown += "## 📊 Statystyki Podsumowania"
    $markdown += ""
    
    $totalFiles = ($projects | Measure-Object -Sum TotalFiles).Sum
    $totalMD = ($projects | Measure-Object -Sum MarkdownFiles).Sum
    $totalSize = ($projects | Measure-Object -Sum TotalSize).Sum
    $avgFileSize = $totalSize / $totalFiles
    
    $markdown += "| Metryka | Wartość |"
    $markdown += "|---------|---------|"
    $markdown += "| **Całkowita Liczba Plików** | $totalFiles |"
    $markdown += "| **Pliki Markdown** | $totalMD |"
    $markdown += "| **Całkowity Rozmiar** | $([math]::Round($totalSize / 1GB, 2)) GB |"
    $markdown += "| **Średni Rozmiar Pliku** | $([math]::Round($avgFileSize / 1KB, 1)) KB |"
    $markdown += "| **Liczba Projektów** | $($projects.Count) |"
    $markdown += "| **Największy Projekt** | $($projects[0].Name) ($($projects[0].TotalFiles) files) |"
    $markdown += ""
    
    # Write output
    $outputPath = Join-Path $VaultRoot $OutputFile
    $markdown | Set-Content -Path $outputPath -Encoding UTF8 -NoNewline
    
    Write-Log "✓ Visualizations written to: $outputPath" Success
    
    Write-Host ""
    Write-Host "📊 VISUALIZATION SUMMARY:" -ForegroundColor Cyan
    Write-Host "  • Pie charts: 2 (file distribution, markdown distribution)" -ForegroundColor Green
    Write-Host "  • Bar chart: 1 (project sizes)" -ForegroundColor Green
    Write-Host "  • Flowchart: 1 (project hierarchy)" -ForegroundColor Green
    Write-Host "  • Statistics table: 2 (projects table + summary stats)" -ForegroundColor Green
    Write-Host ""
    Write-Host "📈 KEY METRICS:" -ForegroundColor Yellow
    Write-Host "  • Total files: $totalFiles" -ForegroundColor Cyan
    Write-Host "  • Markdown files: $totalMD" -ForegroundColor Cyan
    Write-Host "  • Total size: $([math]::Round($totalSize / 1GB, 2)) GB" -ForegroundColor Cyan
    Write-Host "  • Projects: $($projects.Count)" -ForegroundColor Cyan
    
}
catch {
    Write-Log "ERROR: $_" Error
    Write-Log $_.Exception.StackTrace Error
    exit 1
}
