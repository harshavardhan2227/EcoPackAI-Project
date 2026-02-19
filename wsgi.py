"""
EcoPackAI – WSGI entry point for production servers (Gunicorn, uWSGI).

Usage:
    gunicorn wsgi:app
    gunicorn --chdir app app:app   ← preferred (keeps paths clean)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import app

if __name__ == "__main__":
    app.run()
