"""WSGI entry point for production hosts such as PythonAnywhere."""

import os

if os.environ.get("FLASK_DEBUG") == "1":
    raise RuntimeError("FLASK_DEBUG must not be enabled in the production WSGI process.")
if not os.environ.get("SECRET_KEY"):
    raise RuntimeError("Set SECRET_KEY in the hosting platform's WSGI configuration.")
if not os.environ.get("INITIAL_ADMIN_PASSWORD") and os.environ.get("SEED_DEMO_DATA") != "1":
    raise RuntimeError(
        "Set INITIAL_ADMIN_PASSWORD for the first deployment, or configure an existing admin account."
    )
if os.environ.get("SEED_DEMO_DATA") == "1":
    raise RuntimeError("Do not enable demo accounts or sample records in production.")

os.environ.setdefault("COOKIE_SECURE", "1")

from app import app as application
