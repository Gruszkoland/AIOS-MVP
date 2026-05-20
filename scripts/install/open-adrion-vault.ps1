$vaultPath = "C:\Users\adiha\Desktop\Dokumentacja\ADRION-KNOWLEDGE-BANK"
$encodedPath = [System.Uri]::EscapeDataString($vaultPath)
Start-Process "obsidian://open?path=$encodedPath"
Write-Host "Wyslano polecenie otwarcia vaulta w Obsidian: $vaultPath"
