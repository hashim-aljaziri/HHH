# Build Assets Automatically
# Run this to create dist folder before first deployment

echo "Building QURRA Boutique assets..."
$npmPath = "C:\Users\Procurement3\AppData\Local\Programs\nodejs\npm.cmd"
$nodePath = "C:\Users\Procurement3\AppData\Local\Programs\nodejs\node.exe"

# Set environment variables for this session
$env:NODE_ENV = "production"
$env:Path = "C:\Users\Procurement3\AppData\Local\Programs\nodejs;$env:Path"

# Install if needed
if (-not (Test-Path "node_modules")) {
    Write-Output "Installing npm dependencies..."
    & $npmPath install
}

# Build production assets
Write-Output "Running production build..."
& $npmPath "run" "build:prod"

if (Test-Path "static/dist") {
    Write-Output "[OK] Build successful! Assets created in static/dist/"
    Get-ChildItem "static/dist" | Format-Table Name, Length
} else {
    Write-Output "[ERROR] Build failed - static/dist not created"
    exit 1
}
