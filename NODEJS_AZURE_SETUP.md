# QURRA Boutique - Node.js & Azure Setup Guide

## 1. Node.js / npm Setup ✓

### Installed Versions
- **Node.js**: v24.18.0
- **npm**: 11.16.0
- **Location**: `C:\Users\Procurement3\AppData\Local\Programs\nodejs`

### Quick Start

#### Option A: Using the setup.bat script (Recommended)
```bash
# Install dependencies
setup.bat install

# Build production assets
setup.bat build

# Development mode (with file watching)
setup.bat dev

# Start Flask development server
setup.bat start

# Build and run production
setup.bat production
```

#### Option B: Manual npm commands
Add Node.js to PATH, then run:
```bash
npm install          # Install dependencies
npm run build        # Production build
npm run dev          # Development with watch
npm run build:dev    # Dev build only
npm run build:prod   # Prod build only
npm run lint:css     # Lint CSS
npm run lint:js      # Lint JavaScript
npm run format       # Format code with Prettier
```

### Project Structure
```
QURRA_Boutique/
├── package.json                 # npm project config
├── webpack.config.js            # Webpack build config
├── tailwind.config.js           # Tailwind CSS config
├── postcss.config.js            # PostCSS config
├── .babelrc                     # Babel transpiler config
├── .npmrc                       # npm config
│
├── static/
│   ├── js/
│   │   └── main.js             # Entry point for JavaScript
│   ├── css/
│   │   └── main.css            # Tailwind CSS entry
│   └── dist/                    # Generated build output
│       ├── main.js
│       ├── main.css
│       └── vendors.js
│
├── node_modules/               # npm dependencies (auto-created)
│
├── templates/
│   ├── control_panel.html
│   ├── product_detail.html
│   └── ...
│
├── app.py                       # Flask application
├── requirements.txt             # Python dependencies
└── wsgi.py                      # WSGI entry point
```

## 2. Build System Overview

### Webpack Build
- **Entry points**: JavaScript and CSS files
- **Output**: Minified and optimized assets in `static/dist/`
- **Dev mode**: Source maps for debugging, file watching enabled
- **Prod mode**: Code splitting, minification, CSS optimization

### Tailwind CSS
- **Config**: `tailwind.config.js`
- **Entry**: `static/css/main.css`
- **Features**: 
  - Dark mode support
  - Arabic font stacks
  - Custom theme colors
  - Typography scaling utilities

### Babel
- **Target**: Modern browsers (ES2020+)
- **Polyfills**: Automatic core-js integration
- **Config**: `.babelrc`

## 3. npm Scripts

```json
{
  "dev": "npm run build:dev -- --watch",           // Dev build with watch
  "build": "npm run build:prod",                   // Production build
  "build:dev": "NODE_ENV=development webpack",    // Dev webpack build
  "build:prod": "NODE_ENV=production webpack",    // Prod webpack build
  "lint:css": "stylelint 'static/css/**/*.css'",  // Lint CSS
  "lint:js": "eslint 'static/js/**/*.js'",        // Lint JavaScript
  "format": "prettier --write 'static/**/*'",     // Format code
  "start": "flask run",                           // Flask dev server
  "production": "gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app"  // Production
}
```

## 4. Installed npm Packages

### Production Dependencies
- **tailwindcss** (3.3.6) - Utility-first CSS framework
- **autoprefixer** (10.4.17) - Vendor prefixes for CSS
- **postcss** (8.4.32) - CSS processor

### Dev Dependencies
- **webpack** (5.89.0) - Module bundler
- **webpack-cli** (5.1.4) - Webpack CLI
- **babel-loader** (9.1.3) - Babel integration for webpack
- **@babel/core** (7.23.6) - JavaScript transpiler
- **@babel/preset-env** (7.23.6) - Modern JS targeting
- **css-loader** (6.8.1) - CSS loading for webpack
- **mini-css-extract-plugin** (2.7.6) - Extract CSS to separate files
- **terser-webpack-plugin** (5.3.9) - JavaScript minification
- **eslint** (8.55.0) - JavaScript linter
- **prettier** (3.1.1) - Code formatter
- **stylelint** (16.3.1) - CSS linter
- **postcss-loader** (7.3.4) - PostCSS for webpack
- **file-loader** (6.2.0) - File handling for webpack

## 5. Azure Migration Setup

### Prerequisites
- PowerShell 5.1+ (already on your system)
- Az.Tools.Migration module **[INSTALLED ✓]** (v11.0.2)
- Azure subscription (if migrating real workloads)

### Installation (Already Complete)
```powershell
Install-Module -Name Az.Tools.Migration -Scope CurrentUser -Repository PSGallery -Force -AllowClobber
```

### Available Migration Tools

Check what's available:
```powershell
Get-Module -ListAvailable Az.Tools.Migration | Select-Object Name,Version
Import-Module Az.Tools.Migration
Get-Command -Module Az.Tools.Migration | Select-Object Name, CommandType
```

### Common Azure Migration Tasks

#### 1. Assess on-premises resources
```powershell
# Use Azure Migrate to assess VMs, databases, web apps
Invoke-AzMigrateAssessment -ResourceGroupName "your-rg" `
  -ProjectName "your-project" `
  -AssessmentName "your-assessment"
```

#### 2. Migrate virtual machines
```powershell
# Start VM replication
Start-AzMigrateServerReplication -InputObject $ReplicationJob
```

#### 3. Plan migration cutover
```powershell
# Test failover before final migration
Test-AzMigrateServerMigration -InputObject $MigrationJob
```

#### 4. Track migration status
```powershell
# Monitor ongoing migrations
Get-AzMigrateEvent -ProjectName "your-project" -ResourceGroupName "your-rg"
```

### Common Migration Scenarios

1. **Lift & Shift VMs to Azure**
   - Use Azure Migrate: Server Migration
   - Replicate on-premises VMs
   - Test and cutover

2. **Migrate Web Apps**
   - Use Azure App Service Migration Assistant
   - Compatible with this Flask app
   - Guides and validates readiness

3. **Database Migration**
   - Azure Database Migration Service (DMS)
   - Minimal downtime migration
   - Schema and data validation

4. **Cost Optimization**
   - Azure Cost Management + Billing
   - Right-size resources
   - Reserved Instances recommendations

## 6. Development Workflow

### Local Development
```bash
# 1. Terminal 1: Start npm dev build
setup.bat dev

# 2. Terminal 2: Start Flask server
setup.bat start

# 3. Visit http://localhost:5000
```

### Production Deployment
```bash
# 1. Build assets
setup.bat build

# 2. Run with Gunicorn
setup.bat production

# 3. Access on port 8000 or configure reverse proxy
```

## 7. Troubleshooting

### npm not recognized
**Solution**: Add Node.js to PATH or use the `setup.bat` script

### Build fails
```bash
npm run build:dev  # Check build errors in detail
```

### Module not found errors
```bash
npm install --legacy-peer-deps  # If peer dependency issues
npm cache clean --force          # Clear cache and retry
```

### Static files not loading
- Ensure `static/dist/` exists after build
- Clear browser cache (Ctrl+Shift+Delete)
- Check Flask static folder configuration

## 8. Next Steps

1. ✓ **Node.js / npm setup complete**
2. ✓ **Dependencies installed**
3. ⏳ **Run first build**: `setup.bat build`
4. ⏳ **Test development mode**: `setup.bat dev`
5. ⏳ **Deploy to Azure** (when ready to migrate)

---

**For Azure migrations**: Contact your Azure administrator or review [Microsoft Azure Migration Documentation](https://learn.microsoft.com/en-us/azure/migrate/).

