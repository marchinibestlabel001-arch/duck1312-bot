# Duck1312 Bot - PowerShell pokretanje skripte
# ================================================

Write-Host "🦆 Duck1312 Bot - Postavljanje i pokretanje" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Postavi API tokene - ZAMIJENI s pravim tokenima!
$env:TELEGRAM_BOT_TOKEN = "TVOJ_TELEGRAM_BOT_TOKEN_OVDJE"
$env:ANTHROPIC_API_KEY  = "TVOJ_ANTHROPIC_API_KLJUC_OVDJE"

# Provjeri postoji li Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python nije pronađen! Instaliraj Python s https://python.org" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python pronađen: $(python --version)" -ForegroundColor Green

# Instaliraj dependencies
Write-Host "`n📦 Instaliranje paketa..." -ForegroundColor Yellow
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Greška pri instalaciji paketa!" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Paketi instalirani!" -ForegroundColor Green
Write-Host "`n🚀 Pokrećem bota..." -ForegroundColor Cyan
Write-Host "Pritisni Ctrl+C za zaustavljanje bota" -ForegroundColor Gray
Write-Host ""

# Pokretanje bota
python bot.py
