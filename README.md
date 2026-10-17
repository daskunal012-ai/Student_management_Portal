# School Management Portal

A Flask application for student profiles, subjects, examination marks, results, and role-specific dashboards. The project uses SQLite by default and provides separate administrator, teacher, and student access.

This is a learning/demo project, not a production-ready school information system. Use fictional data while testing. Do not publish real student information or deploy the demo accounts to a public website.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/daskunal012-ai/Student_management_Portal)

## What it can do

- Administrator, teacher, and student sign-in with role-protected routes
- Student directory with name/admission-number search and grade filtering
- Student profiles with guardian/contact details and linked student login accounts
- Subject catalogue with unique subject codes and configurable maximum marks
- Examination marks entry and updates by student, subject, exam, and academic year
- Results with totals, percentage, grade, and staff-side filters
- Student dashboard and own-profile/results access restrictions
- Administrator view of user accounts and account activation/deactivation
- CSRF-protected, server-validated Flask-WTF forms
- Responsive server-rendered pages with Jinja, Bootstrap, and custom CSS

## Stack

- Python 3.10+
- Flask and Flask-SQLAlchemy
- SQLite by default; SQLAlchemy database URL can be configured with `DATABASE_URL`
- Flask-Login for session authentication
- Flask-WTF / WTForms for form handling, validation, and CSRF protection
- Werkzeug password hashing
- Jinja templates, Bootstrap 5, Bootstrap Icons, and custom CSS

## Project layout

```text
app.py                      Application, models, forms, routes, and seed logic
wsgi.py                     Production WSGI entry point
requirements.txt            Python dependencies
templates/                  Jinja HTML pages
static/css/style.css        Application styling
.env.example                Local-development environment variable example
.gitignore                  Excludes secrets, databases, and generated files
```

## Deploy from GitHub with a hosted subdomain

The quickest hosted demo is Render, which connects to this GitHub repository, provisions the web app and PostgreSQL database from `render.yaml`, and assigns the service an `onrender.com` subdomain.

1. Click **Deploy to Render** above and sign in to Render using your GitHub account.
2. Authorize Render to read `daskunal012-ai/Student_management_Portal`, then review the Blueprint resources.
3. Select the Free plans if offered. Render will ask you for `INITIAL_ADMIN_PASSWORD`; choose a private password with at least 12 characters. Do not send it in chat, commit it, or reuse a personal password.
4. Confirm deployment. Render builds the app, connects it to PostgreSQL, and assigns the default URL `https://student-management-portal-daskunal012.onrender.com`. If that subdomain is already taken, use the URL Render assigns to the web service.
5. Wait for the deployment health check to pass, then open the service URL and sign in as `admin` with the initial password you entered.
6. After confirming that the administrator account works, remove `INITIAL_ADMIN_PASSWORD` from the Render service's environment variables and redeploy. Keep `SECRET_KEY`, `DATABASE_URL`, `FLASK_DEBUG=0`, and `COOKIE_SECURE=1`.

Each push to `main` automatically triggers a Render deployment. GitHub Actions separately runs the tests on Python 3.10 through 3.13.

**Free-plan warning:** the app sleeps after 15 minutes without traffic, so its first request may take about a minute to wake. Free Render Postgres is limited and expires 30 days after creation; after its grace period, its data is deleted. This is only a temporary demo setup. Do not store real student data or rely on the free database for durable records. Upgrade the database and configure backups before any continued use.

GitHub Pages alone cannot run this project because it only hosts static files; the Flask server and database require an application host such as Render.

## Run a local demo on Windows

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
$env:SECRET_KEY = "use-a-private-random-development-secret"
$env:FLASK_DEBUG = "1"
$env:SEED_DEMO_DATA = "1"
python app.py
```

Open http://127.0.0.1:5000. The local-only demo seed creates the accounts below and fictional sample records:

| Role | Username | Demo password |
|---|---|---|
| Administrator | `admin` | `Admin@12345` |
| Teacher | `teacher` | `Teacher@123` |
| Student | `student` | `Student@123` |

These are public demonstration credentials, not secure passwords. Do not use demo seeding or these accounts in a public deployment. Seeding happens only when the database has no users; it does not reset existing accounts.

To use the `.env.example` as a local reference, copy it to `.env` and set the variables in your terminal. The application does not automatically load `.env`; set those variables in your shell or use a local environment loader that you install and configure separately. Never commit `.env`.

## Alternative: deploy to PythonAnywhere

`wsgi.py` is the production entry point. It fails closed if the secret or initial administrator password is missing, if Flask debug mode is enabled, or if demo seeding is enabled. This prevents accidentally starting a new public instance with the known demo accounts.

1. Create a PythonAnywhere account and a **Manual configuration** web app using a supported Python version.
2. Open a Bash console, clone this repository, and create a virtual environment:

   ```bash
   cd ~
   git clone https://github.com/daskunal012-ai/Student_management_Portal.git
   cd Student_management_Portal
   python3.12 -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt
   ```

   Use the Python version selected for the web app if it differs from Python 3.12.

3. Generate two private values for the deployment: a long random `SECRET_KEY` and a unique initial administrator password. In the PythonAnywhere **Web** tab, edit the WSGI configuration file. Before importing the application, add the following, replacing the username/path and both placeholder values:

   ```python
   import os
   import sys

   project_home = "/home/YOUR-PYTHONANYWHERE-USERNAME/Student_management_Portal"
   if project_home not in sys.path:
       sys.path.insert(0, project_home)

   os.environ["FLASK_DEBUG"] = "0"
   os.environ["COOKIE_SECURE"] = "1"
   os.environ["SECRET_KEY"] = "REPLACE_WITH_A_PRIVATE_RANDOM_SECRET"
   os.environ["INITIAL_ADMIN_PASSWORD"] = "REPLACE_WITH_A_UNIQUE_STRONG_PASSWORD"

   from wsgi import application
   ```

   Do not put real secrets in this repository. The PythonAnywhere WSGI configuration is server-side; restrict access to that account.

4. In the Web tab, set the virtualenv path to `/home/YOUR-PYTHONANYWHERE-USERNAME/Student_management_Portal/.venv` and configure the static files mapping `/static/` to `/home/YOUR-PYTHONANYWHERE-USERNAME/Student_management_Portal/static/`.
5. Reload the web app from the Web tab and open the PythonAnywhere web-app URL. The first successful startup creates an `admin` account using `INITIAL_ADMIN_PASSWORD`. Sign in and change that password. After the administrator is created, remove `INITIAL_ADMIN_PASSWORD` from the WSGI configuration and reload; the existing database account remains.
6. Use a persistent database configuration and backups appropriate for your usage. The default SQLite database is convenient for a small demo; never put a populated database in Git.

### Create teacher accounts

The current UI does not create teacher accounts; it only seeds a demo teacher in local demo mode. Do not enable public demo seeding to get a teacher login. For a live deployment, create teacher accounts through a secure, administrator-only provisioning workflow before school use. If provisioning manually, use a one-off PythonAnywhere console script that creates a `User(role="teacher", ...)` and calls `set_password()` with a private, unique password; never store the plaintext password in a committed script.

### Updating a deployment

From a Bash console, pull the reviewed change and install dependency updates if requirements changed:

```bash
cd ~/Student_management_Portal
git pull
. .venv/bin/activate
pip install -r requirements.txt
```

Then reload the web app in the PythonAnywhere Web tab. This starter uses `db.create_all()` for missing tables and does not include schema migrations; back up existing data and plan migrations before changing database models.

## Configuration

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Required for production sessions and CSRF signing. Keep private and use a long random value. |
| `DATABASE_URL` | Optional SQLAlchemy database URI. Defaults to local SQLite. |
| `FLASK_DEBUG` | Set to `1` only for local development. Production WSGI entry point rejects it. |
| `COOKIE_SECURE` | Set to `1` when served over HTTPS so session cookies use the Secure attribute. |
| `SEED_DEMO_DATA` | Set to `1` only for a fresh local demo database. Production WSGI rejects it. |
| `INITIAL_ADMIN_PASSWORD` | Required on the first production startup to create the initial admin when the database is empty. Remove from hosting config after creation. |
| `DEMO_ADMIN_PASSWORD` | Optional local demo-seed override for the demo administrator on initial database creation. |

If an existing database already contains users, seed/bootstrap settings do not reset their passwords.

## Security and current limitations

- Demo credentials are deliberately available for local demonstration only.
- Do not use the built-in Flask development server for deployment.
- Keep secrets and database files out of Git; use fictional data for demos.
- Student data is sensitive. Production use needs approval, secure hosting, HTTPS, backup/restore plans, privacy controls, and a security review.
- This project does not yet include automated tests, database migration tooling, password reset, rate limiting, audit logs, or production monitoring.
- Date of birth and some school configuration are currently represented with simple strings / fixed choices.
- The application is a compact starter and has most routes/models/forms in `app.py`; larger deployments should add an application factory, blueprints, tests, and migrations.

## Project documents

The repository includes `Project_Interview_Preparation_Guide.pdf`, an interview-preparation document that describes the current implementation and its limitations.
