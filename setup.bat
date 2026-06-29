@echo off
REM QURRA Boutique - Setup Script
REM This script sets up the Node.js PATH and runs npm commands

setlocal enabledelayedexpansion

set NODE_HOME=C:\Users\Procurement3\AppData\Local\Programs\nodejs
set "PATH=%NODE_HOME%;%PATH%"

echo.
echo ====================================
echo QURRA Boutique - Project Setup
echo ====================================
echo.

if "%1"=="build" (
    echo Building production assets...
    call npm run build
    echo.
    echo Build complete! Assets are in static/dist/
) else if "%1"=="dev" (
    echo Starting development build with watch...
    call npm run dev
) else if "%1"=="install" (
    echo Installing npm dependencies...
    call npm install
    echo Dependencies installed!
) else if "%1"=="start" (
    echo Starting Flask development server...
    python app.py
) else if "%1"=="production" (
    echo Building for production...
    call npm run build
    echo.
    echo Starting production server with Gunicorn...
    call gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
) else (
    echo Usage: setup.bat [command]
    echo.
    echo Available commands:
    echo   install      - Install npm dependencies
    echo   build        - Build production assets
    echo   dev          - Start development build with file watching
    echo   start        - Start Flask development server
    echo   production   - Build and run production with Gunicorn
    echo.
    echo Examples:
    echo   setup.bat install
    echo   setup.bat build
    echo   setup.bat start
)

endlocal
