# QURRA Boutique - Premium Libyan Abayas

A Flask-based e-commerce boutique for premium Libyan traditional wear with multilingual support (Arabic/English), dynamic theming, and admin controls.

## Features

- **Multilingual Support**: Arabic and English interface
- **Theme Selection**: Light, Dark, Warm, Ocean, Sand, and Forest themes
- **Full Control Panel**: Manage branding, typography, products, and admin users
- **Product Management**: Add products individually or via CSV import
- **Image Upload**: Support for logo, background, and product images
- **Dynamic Content**: Editable homepage text via control panel
- **Admin Permissions**: Owner/Manager/Editor presets + custom per-admin permissions
- **Admin Password Management**: Change own password and reset other admin passwords
- **Responsive Design**: Mobile-friendly interface using Tailwind CSS

## Project Structure

```
├── app.py                 # Flask app, models, and routes
├── requirements.txt       # Python dependencies
├── wsgi.py               # Production WSGI entry point
├── Procfile              # Deployment configuration (Heroku)
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
├── static/
│   ├── style.css         # Theme and styling
│   └── images/           # Logo, background, and product images
├── templates/
│   ├── layout.html       # Main layout with navigation
│   ├── index.html        # Homepage with slider
│   ├── shop.html         # Product listing
│   ├── product_detail.html # Product details page
│   ├── admin.html        # Admin dashboard
│   ├── control_panel.html # Site settings control
│   └── login.html        # Admin login
└── instance/             # Instance-specific files (database)
```

## Local Development

### Prerequisites
- Python 3.8+
- pip or poetry

### Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd QURRA_Boutique
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the development server:
```bash
python app.py
```

The app will be available at `http://127.0.0.1:5000`

### Admin Access

Use any of these credentials to log in at `/login`:
- `admin1` / `QurraAdmin#1`
- `admin2` / `QurraAdmin#2`
- `admin3` / `QurraAdmin#3`

## Production Deployment

### Environment Setup

1. Copy `.env.example` to `.env` and update values:
```bash
cp .env.example .env
```

2. Update environment variables:
```bash
FLASK_DEBUG=False
FLASK_ENV=production
SECRET_KEY=<your-strong-secret-key>
SESSION_COOKIE_SECURE=True
# Optional: external DB (Render/Neon/Supabase/Postgres)
# DATABASE_URL=postgresql://user:password@host:5432/dbname
```

3. Health check endpoint:
- Use `/health` for platform health probes.

### Deploy to Heroku

1. Install Heroku CLI and log in:
```bash
heroku login
```

2. Create a Heroku app:
```bash
heroku create your-app-name
```

3. Set environment variables:
```bash
heroku config:set FLASK_ENV=production SECRET_KEY=<your-secret-key>
```

4. Deploy:
```bash
git push heroku main
```

### Deploy to Render (Recommended)

This repository includes a Render blueprint file at `render.yaml`.

1. Push this code to GitHub.
2. In Render, choose **New +** -> **Blueprint**.
3. Select your repository.
4. Confirm the service settings and create the service.

Render will automatically:
- install Python dependencies
- build frontend assets with npm
- start Gunicorn
- run health checks on `/health`

If you deploy manually (without blueprint), use:

```bash
Build Command: npm ci && npm run build && pip install -r requirements.txt
Start Command: gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 3
```

### Deploy with Gunicorn (Self-hosted)

1. Install Gunicorn (included in requirements.txt):
```bash
pip install -r requirements.txt
```

2. Run with Gunicorn:
```bash
gunicorn wsgi:app --bind 0.0.0.0:5000 --workers 4
```

3. Use a reverse proxy (Nginx) in front for production.

## Publish Checklist

1. Set a strong `SECRET_KEY` in production.
2. Set `SESSION_COOKIE_SECURE=True` when using HTTPS.
3. Configure `DATABASE_URL` for Postgres in production (recommended).
4. Keep `FLASK_DEBUG=False`.
5. Confirm health endpoint: `GET /health` returns 200.
6. Verify login at `/login` and control panel access at `/control`.

## Database

- **Development**: SQLite (`instance/qurra.db`)
- **Production**: PostgreSQL via `DATABASE_URL` environment variable

## API Routes

### Public Routes
- `GET /` - Homepage with featured product slider
- `GET /shop` - All products listing
- `GET /product/<id>` - Product detail page
- `GET /switch_lang` - Toggle language (EN/AR)
- `GET /switch_theme/<theme>` - Change theme
- `GET /login` - Admin login page

### Admin Routes (requires authentication)
- `GET /admin` - Dashboard with product management
- `POST /admin` - Add product or import CSV
- `GET /admin/delete/<id>` - Delete product
- `GET /control` - Site settings control panel
- `POST /control` - Update settings
- `POST /control/admin/password` - Change current admin password
- `POST /control/admins/add` - Add admin user
- `POST /control/admins/update/<id>` - Update admin username/permissions/password
- `POST /control/admins/delete/<id>` - Delete admin user
- `GET /logout` - Logout

### Health Route
- `GET /health` - Deployment health check

## Configuration

### Themes
Located in `static/style.css`:
- `light` - Light theme with teal accents
- `dark` - Dark theme with cyan accents
- `pink` - Warm theme with pink accents

### Settings Editable via Control Panel
- Site logo and background
- Default theme
- Homepage hero text (EN/AR)
- Featured section text (EN/AR)
- Product images

## Support

For issues or questions, contact the admin team.

## License

Private project - QURRA Boutique © 2024
