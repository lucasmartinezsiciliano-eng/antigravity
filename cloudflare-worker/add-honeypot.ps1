$dir = "c:\Users\Pc2025\Desktop\ANTIGRAVITY\broker-web"
$files = Get-ChildItem -Path $dir -Recurse -Filter "*.html" | Where-Object { $_.FullName -notlike "*.claude*" }

$honeypot = '<input type="text" name="q_hp" style="display:none!important;position:absolute;left:-9999px;" tabindex="-1" autocomplete="off" aria-hidden="true" value="" />'

# Pattern: the privacy line that appears right after the email field in every quiz contact step
# Use [System.Text.StringBuilder] to handle the replacement safely
$searchStr = "Tus datos est" + [char]0xE1 + "n protegidos. No compartimos tu informaci" + [char]0xF3 + "n con terceros."

$changed = 0
foreach ($f in $files) {
    $bytes = [System.IO.File]::ReadAllBytes($f.FullName)
    $content = [System.Text.Encoding]::UTF8.GetString($bytes)

    if ($content.Contains($searchStr) -and -not $content.Contains('name="q_hp"')) {
        # Use [string]::Replace which handles multi-char strings correctly
        $replacement = $honeypot + "`n          " + $searchStr
        $content = [string]::Concat(
            $content.Substring(0, $content.IndexOf($searchStr)),
            $replacement,
            $content.Substring($content.IndexOf($searchStr) + $searchStr.Length)
        )
        $outBytes = [System.Text.Encoding]::UTF8.GetBytes($content)
        [System.IO.File]::WriteAllBytes($f.FullName, $outBytes)
        $changed++
        Write-Host "Honeypot added: $($f.Name)"
    }
}
Write-Host "Total: $changed archivos"
