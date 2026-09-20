# Build CYRIL on Windows from the repository root. No secrets are bundled.
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path ($PSScriptRoot))
$root = (Get-Location).Path
$entry = Join-Path $root 'scripts\ui\pywebview\app.py'
$icon = Join-Path $root 'scripts\ui\pywebview\CYRIL.ico'
$html = Join-Path $root 'scripts\ui\pywebview\index.html'
$config = Join-Path $root 'config\.env'
foreach ($file in @($entry, $icon, $html, $config)) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Required file missing: $file" }
}
python -m PyInstaller --noconfirm --clean --onedir --windowed --name CYRIL `
    --icon "$icon" `
    --paths "$root" `
    --add-data "${html};scripts/ui/pywebview" `
    --add-data "${icon};scripts/ui/pywebview" `
    --collect-all keyring `
    --collect-submodules scripts `
    --collect-submodules common `
    "$entry"
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }
$dist = Join-Path $root 'dist\CYRIL'
New-Item -ItemType Directory -Force -Path (Join-Path $dist 'config') | Out-Null
Copy-Item -LiteralPath $config -Destination (Join-Path $dist 'config\.env') -Force
Write-Host "Build ready: $dist\CYRIL.exe"
Write-Host 'Configuration is external in dist\CYRIL\config\.env. Do not publish that folder or commit the file.'

# SIG # Begin signature block
# MIIFvwYJKoZIhvcNAQcCoIIFsDCCBawCAQExDzANBglghkgBZQMEAgEFADB5Bgor
# BgEEAYI3AgEEoGswaTA0BgorBgEEAYI3AgEeMCYCAwEAAAQQH8w7YFlLCE63JNLG
# KX7zUQIBAAIBAAIBAAIBAAIBADAxMA0GCWCGSAFlAwQCAQUABCA82vRim4nhybOZ
# gTvW56BDmCyYQDl9gPbjpT+GftkyiaCCAyYwggMiMIICCqADAgECAhBXlahiISyq
# nESWzWsvb8ewMA0GCSqGSIb3DQEBCwUAMCkxJzAlBgNVBAMMHkNZUklMIERldmVs
# b3BtZW50IENvZGUgU2lnbmluZzAeFw0yNjA5MTkxMzA0NDhaFw0yNzA5MTkxMzI0
# NDhaMCkxJzAlBgNVBAMMHkNZUklMIERldmVsb3BtZW50IENvZGUgU2lnbmluZzCC
# ASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALq6ZkrQxUu11q1/C/Jho3dq
# F7U8uLatIrN5Gn98mK34j4p0rpiZ9lmMeJ4Lu0NZj8mpBCRJBWg01eSLZxEiRt0M
# 5+CGk2w7TLiTFn0SXt5w+iZpSVQgyn//beD4yqYJeSYZ+nXbQIJuSXpNBmPRjuWv
# AVDmYgU3x+M2U3MWvw4f6BouaDH1sKwnFaV4fXbNeZlGPPPWG2itur0VpDLebCvl
# A6JcCrRZiPYpqvUeJ/+mPisvK0dOU9yPA8TAOSBLNyxwZjRL0aemccf6oRMzyiTs
# 9HC2sLKdNx6x3fwT/oOxT+YHbtogFryX+lt0a1Zgd3L/LLqlcmsN7mUXEiMeV/UC
# AwEAAaNGMEQwDgYDVR0PAQH/BAQDAgeAMBMGA1UdJQQMMAoGCCsGAQUFBwMDMB0G
# A1UdDgQWBBRkYIxTtwSXGgriTq6+PZBx61JvozANBgkqhkiG9w0BAQsFAAOCAQEA
# s/OqcxAvNoXj18GlV/0Pcgagyze7pUJBIaRneGnINVros6/7ex3PqLSoxum0ZwhU
# FjjSh57gytiYNa6PtDzwpGYzKjfIL32Iv/lNzitLO2fdwaLqThcN0S7vIe1aRFjD
# 90IpUOVV7hZ8w7xzpgJ1My7yszGF4wli2/Su6YpGGUcgQOlho7O9kaB+YH4ECRbU
# W/yvtrxXTfeSl5zJrs67G3aTVHGKMJHMp9SyOu9SJnrcyVOXOlrDJ12TE//fOVwt
# 40e7/XmiLNTNVhO4Yvma+/GRqGxj5moKkN+XeeN8Gb7DGJG7ATBCe1JGTPgXwKaP
# 5jWTxSVBnOoG6icdKEXcjDGCAe8wggHrAgEBMD0wKTEnMCUGA1UEAwweQ1lSSUwg
# RGV2ZWxvcG1lbnQgQ29kZSBTaWduaW5nAhBXlahiISyqnESWzWsvb8ewMA0GCWCG
# SAFlAwQCAQUAoIGEMBgGCisGAQQBgjcCAQwxCjAIoAKAAKECgAAwGQYJKoZIhvcN
# AQkDMQwGCisGAQQBgjcCAQQwHAYKKwYBBAGCNwIBCzEOMAwGCisGAQQBgjcCARUw
# LwYJKoZIhvcNAQkEMSIEIBZi2cd99mQtOnCrKf2FmMpAJV/xI3AL5/dn1Ek9Nu4p
# MA0GCSqGSIb3DQEBAQUABIIBAGAlz72BVuxpLLdcEg9Ma90+I2LLasCnG5Aem1aV
# H+Z50qy6XsfEXMX5CMocTZ12S40Bl1SkAJRjT2Ne7joEGiVTVGUWrKOwFouhyGg+
# EYw4YAsfjtQHJQU0SyruKUP1GxzyWDui2QiNKZfh0DAYwK1I/EHUXMPJwK2CvPW8
# F2XJUOl+CJ7NVMZZyiRNEWjd2+pjzZaArb4oPYdACHn5Nt99slhIBlKhQGwXKMMS
# 41iaSJj9R41eKKyzrFmk5sx2KHcy8VBHITUZjLoM5iduIr3PVecDypgc5Fq4p4ns
# u2Mqrzw3KO1I4umtkAbqEUN00SuNOQQH0aZNSGoGMsYw9fE=
# SIG # End signature block
