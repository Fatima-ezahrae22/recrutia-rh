@echo off
title RecrutIA - Lancement Serveur et Lien Public
chcp 65001 > nul
cls
echo =====================================================================
echo           RECRUTIA RH - SERVEUR LOCAL ET TUNNEL PUBLIC
echo =====================================================================
echo.
echo [1/2] Demarrage du serveur FastAPI...
start /b python run_backend.py
timeout /t 3 > nul
echo [OK] Serveur local actif sur : http://127.0.0.1:8000
echo.
echo [2/2] Creation du lien public mondial en HTTPS...
echo =====================================================================
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R 80:127.0.0.1:8000 serveo.net
pause
