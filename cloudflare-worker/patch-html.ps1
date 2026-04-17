$dir = "c:\Users\Pc2025\Desktop\ANTIGRAVITY\broker-web"
$htmlFiles = Get-ChildItem -Path $dir -Recurse -Filter "*.html" | Where-Object { $_.FullName -notlike "*.claude*" }

$honeypot = '<input type="text" name="q_hp" style="display:none!important;position:absolute;left:-9999px;" tabindex="-1" autocomplete="off" aria-hidden="true" value="" />'
$trigger  = [char]0x1F512 + " Tus datos est" + [char]0x00E1 + "n protegidos"

$changed = 0
foreach ($f in $htmlFiles) {
    $content = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
    $modified = $false

    # 1. Honeypot antes del parrafo de privacidad
    if ($content.Contains("Tus datos est") -and -not $content.Contains('name="q_hp"')) {
        $searchStr = [char]0x1F512 + " Tus datos est" + [char]0x00E1 + "n protegidos. No compartimos tu informaci" + [char]0x00F3 + "n con terceros."
        if ($content.Contains($searchStr)) {
            $replace = $honeypot + "`n          " + $searchStr
            $content = $content.Replace($searchStr, $replace)
            $modified = $true
        }
    }

    # 2. Meta referrer si no existe
    if (-not $content.Contains('name="referrer"')) {
        $charsetTag = '<meta charset="UTF-8" />'
        if ($content.Contains($charsetTag)) {
            $newTag = $charsetTag + "`n  " + '<meta name="referrer" content="strict-origin-when-cross-origin" />'
            $content = $content.Replace($charsetTag, $newTag)
            $modified = $true
        }
    }

    if ($modified) {
        [System.IO.File]::WriteAllText($f.FullName, $content, [System.Text.Encoding]::UTF8)
        $changed++
        Write-Host "Updated: $($f.Name)"
    }
}
Write-Host "Total: $changed archivos"
