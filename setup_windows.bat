@echo off
setlocal
cd /d "%~dp0"
echo =============================================
echo Instagram Reel Factory - Windows Setup
echo =============================================
where py >nul 2>nul
if %errorlevel%==0 (
  py -3.12 -m venv .venv 2>nul
  if not exist .venv\Scripts\python.exe py -3 -m venv .venv
) else (
  python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env
cd my-video
call npm install
if %errorlevel% neq 0 (
  echo npm install failed. Check Node.js/npm installation and try again.
  exit /b 1
)
cd ..
echo.
echo Setup complete.
echo 1. Edit .env and add your LLM key.
echo 2. Run run_reel.bat
pause
