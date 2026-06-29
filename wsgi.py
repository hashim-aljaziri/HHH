"""
WSGI entry point for production servers (Gunicorn, uWSGI, etc.)
Usage: gunicorn wsgi:app
"""
import os
from app import app

if __name__ == "__main__":
    app.run()
