@echo off
title Culto App - Iniciando...
echo.
echo  ============================================
echo    🙏  CULTO APP - Sistema de Gestao de Culto
echo  ============================================
echo.

echo [1/3] Subindo os containers (Evolution API + App)...
docker compose up -d --build
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Erro ao subir os containers. Verifique se o Docker esta rodando.
    pause
    exit /b 1
)

echo.
echo [2/3] Aguardando os servicos iniciarem...
timeout /t 8 /nobreak >nul

echo.
echo [3/3] Abrindo o painel admin no navegador...
start http://localhost:5000/admin

echo.
echo  ============================================
echo    ✅  Tudo rodando!
echo  ============================================
echo.
echo    Painel Admin:    http://localhost:5000/admin
echo    Formulario:      http://localhost:5000
echo    Evolution API:   http://localhost:8080/manager
echo.
echo    Para parar: docker compose down
echo.
pause
