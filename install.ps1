# pii-safe-read installer
# Usage (PowerShell):
#   irm https://raw.githubusercontent.com/USERNAME/REPO/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

$Base = "https://raw.githubusercontent.com/USERNAME/REPO/main"
$SkillName = "pii-safe-read"

$id = $env:__CFBundleIdentifier
if ($id -and $id -match "codebuddy") {
    $SkillsDir = Join-Path $HOME ".codebuddy/skills"
} elseif ($env:CODEBUDDY_CONFIG_DIR) {
    $SkillsDir = Join-Path $env:CODEBUDDY_CONFIG_DIR "skills"
} elseif ($env:WORKBUDDY_CONFIG_DIR) {
    $SkillsDir = Join-Path $env:WORKBUDDY_CONFIG_DIR "skills"
} else {
    $SkillsDir = Join-Path $HOME ".workbuddy/skills"
}

$Target = Join-Path $SkillsDir $SkillName
New-Item -ItemType Directory -Force -Path (Join-Path $Target "references") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Target "scripts") | Out-Null

$files = @(
    "SKILL.md",
    "references/pii_rules.json",
    "references/workflow.md",
    "scripts/gen_safe_list.py"
)

foreach ($f in $files) {
    $dest = Join-Path $Target $f
    $url  = "$Base/$f"
    Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
    Write-Host "  ok  $f"
}

Write-Host ""
Write-Host "Installed to: $Target"
Get-ChildItem -Recurse $Target | Select-Object -ExpandProperty FullName
