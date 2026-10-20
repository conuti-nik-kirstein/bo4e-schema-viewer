@echo off
rem BO4E-Schema-Viewer neu erzeugen (aktueller Stand von GitHub) und im Browser oeffnen.
rem Parameter werden durchgereicht, z. B.:  aktualisieren.bat --quelle lokal
setlocal
cd /d "%~dp0"
set "PY=python"
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
%PY% build_viewer.py %*
if errorlevel 1 (
  echo.
  echo Fehler beim Erzeugen - siehe Meldungen oben.
  pause
  exit /b 1
)
start "" "%~dp0output\BO4E-Schema-Viewer.html"
