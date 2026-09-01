@echo off
title Configurar Ollama para rag-docs
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0configurar-ollama-remoto.ps1"
if errorlevel 1 pause
