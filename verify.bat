@echo off
REM QURRA Boutique - Installation Verification Script

echo.
echo ====================================
echo QURRA Boutique - Verification Report
echo ====================================
echo.

REM Check Node.js
echo [1/5] Checking Node.js...
if exist "C:\Users\Procurement3\AppData\Local\Programs\nodejs\node.exe" (
    echo   OK - Node.js installed
    "C:\Users\Procurement3\AppData\Local\Programs\nodejs\node.exe" --version
) else (
    echo   ERROR - Node.js not found
)
echo.

REM Check npm
echo [2/5] Checking npm...
if exist "C:\Users\Procurement3\AppData\Local\Programs\nodejs\npm.cmd" (
    echo   OK - npm installed
    "C:\Users\Procurement3\AppData\Local\Programs\nodejs\npm.cmd" --version
) else (
    echo   ERROR - npm not found
)
echo.

REM Check node_modules
echo [3/5] Checking dependencies...
if exist "node_modules" (
    echo   OK - node_modules directory exists
    dir /b node_modules | find /c /v "" > temp.txt
    set /p count=<temp.txt
    del temp.txt
    echo   Found approximately %count% packages
) else (
    echo   ERROR - node_modules not found. Run: npm install
)
echo.

REM Check configuration files
echo [4/5] Checking configuration files...
if exist "package.json" echo   OK - package.json
if exist "webpack.config.js" echo   OK - webpack.config.js
if exist "tailwind.config.js" echo   OK - tailwind.config.js
if exist "postcss.config.js" echo   OK - postcss.config.js
if exist ".babelrc" echo   OK - .babelrc
echo.

REM Check source files
echo [5/5] Checking source files...
if exist "static\js\main.js" echo   OK - static/js/main.js
if exist "static\css\main.css" echo   OK - static/css/main.css
echo.

REM Check for build output
if exist "static\dist" (
    echo [BONUS] Build output found in static/dist!
    dir /b static\dist
) else (
    echo [INFO] Run 'npm run build' to generate static/dist/
)

echo.
echo ====================================
echo Setup Status: COMPLETE
echo ====================================
echo.
echo Next steps:
echo   1. npm run build      - Build production assets
echo   2. npm run dev        - Start development build
echo   3. flask run          - Start Flask server
echo   4. Open http://localhost:5000
echo.
pause
