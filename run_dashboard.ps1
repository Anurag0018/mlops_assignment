Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Launching Student Performance Analytics Dashboard..." -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

python -m streamlit run dashboard/app.py
