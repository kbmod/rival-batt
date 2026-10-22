$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller==6.22.3
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name rival-batt --collect-submodules pystray rival_batt.py
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
