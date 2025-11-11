# PowerShell script to run the game
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1
Write-Host "Running game..." -ForegroundColor Green
python main.py
Read-Host "Press Enter to exit"

