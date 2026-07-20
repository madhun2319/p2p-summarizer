# ponytail: Resolve script location dynamically instead of hardcoding paths.
$P2P_DIR = $PSScriptRoot
Set-Location $P2P_DIR

Write-Host "🚀 [1/2] Fetching & Triaging last 7 days of PDBs (Llama 3.1 8B)..." -ForegroundColor Cyan
uv run --env-file .env --with openai ingest.py

Write-Host "📰 [2/2] Generating Proteins of the Week Newsletter (Llama 3.1 70B)..." -ForegroundColor Green
uv run --env-file .env --with openai newsletter.py

Write-Host "🎉 Weekly Pipeline Complete!" -ForegroundColor Yellow
