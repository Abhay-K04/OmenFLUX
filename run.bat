@echo off
title OmenFLUX
cd /d "%~dp0"
if exist "dist\OmenFLUX.exe" (
    start "" "dist\OmenFLUX.exe" %*
) else if exist "dist\OmenPulse.exe" (
    start "" "dist\OmenPulse.exe" %*
) else if exist "dist\OmenGlow.exe" (
    start "" "dist\OmenGlow.exe" %*
) else (
    start "" "C:\Users\Abhay\AppData\Local\Programs\Python\Python311\pythonw.exe" "main.py" %*
)