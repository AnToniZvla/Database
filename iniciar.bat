@echo off
title Sistema de Gestión - Papelería
:: Se posiciona en la carpeta actual del proyecto
cd /d %~dp0

echo Iniciando Sistema de Gestión - Papelería...
python menu.py

echo.
echo El programa ha finalizado.
pause