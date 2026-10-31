@echo off
start "MontenAI API" cmd /k "cd /d "%~dp0backend" && run_api.bat"
start "MontenAI Frontend" cmd /k "cd /d "%~dp0frontend" && run_frontend.bat"
