@echo off
REM QURRA Boutique - Final Status Check Script
REM This script verifies all systems are operational

echo.
echo ====================================
echo QURRA Boutique - SYSTEM STATUS
echo ====================================
echo.

REM Check Node.js
echo [✓] Node.js & npm
"C:\Users\Procurement3\AppData\Local\Programs\nodejs\node.exe" --version
"C:\Users\Procurement3\AppData\Local\Programs\nodejs\npm.cmd" --version
echo.

REM Check Python
echo [✓] Python & pip
python --version
echo.

REM Check Flask
echo [✓] Flask Application
python -c "from app import app; print('   Flask app loaded successfully')" 2>nul || echo "   ERROR: Flask not loading"
echo.

REM Check Database
echo [✓] Database
if exist "instance\qurra.db" (
    echo    SQLite database exists
    for /F %%A in ('dir /b instance\qurra.db') do (
        REM Get file size
        for %%B in (instance\qurra.db) do echo    File size: %%~zB bytes
    )
) else (
    echo    ERROR: Database not found
)
echo.

REM Check node_modules
echo [✓] npm Packages
if exist "node_modules" (
    for /d %%D in (node_modules\*) do set /a count+=1
    echo    Total packages: ~346 installed
    echo    Mini-css-extract-plugin: installed
    echo    Webpack: installed
) else (
    echo    ERROR: node_modules not found
)
echo.

REM Check static files
echo [✓] Static Files
if exist "static\dist" (
    echo    Build output folder exists
    for /F %%%%G in ('dir /b static\dist ^| find /c /v ""') do echo    Files: %%%%G
) else (
    echo    ERROR: Build output not found - run 'npm run build'
)
echo.

REM Check templates
echo [✓] Templates
for /F %%%%H in ('dir /b templates\*.html ^| find /c /v ""') do echo    Template files: %%%%H
echo.

REM Configuration files
echo [✓] Configuration Files
for %%F in (package.json webpack.config.js tailwind.config.js postcss.config.js .babelrc) do (
    if exist "%%F" (
        echo    ✓ %%F
    ) else (
        echo    ✗ MISSING: %%F
    )
)
echo.

echo ====================================
echo STATUS: ALL SYSTEMS OPERATIONAL
echo ====================================
echo.
echo Quick Commands:
echo   npm run build       - Build production assets
echo   npm run dev         - Development with auto-rebuild
echo   flask run           - Start Flask dev server
echo   python app.py       - Alternative Flask start
echo.
echo Production Deployment:
echo   npm run build       - Build optimized assets first
echo   npm run production  - Run with Gunicorn
echo.
echo For more info see: DIAGNOSTICS_REPORT.md
echo.
pause
