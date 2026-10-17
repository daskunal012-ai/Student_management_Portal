# Security policy

## Scope

This repository is a learning/demo project and is not currently recommended for production use with real student records.

## Reporting a vulnerability

Please do not publish credentials, student data, or exploitable details in a public issue. Use GitHub's private vulnerability reporting feature for this repository if it is enabled. Otherwise, contact the repository owner privately through GitHub to coordinate a report.

## Deployment reminders

- Never deploy the known demo accounts or enable `SEED_DEMO_DATA` on a public host.
- Set a long, private `SECRET_KEY` and a unique initial administrator password.
- Do not commit `.env`, database files, or real student information.
- Use HTTPS and a production WSGI server; do not expose Flask debug mode.
- Review authorization, backups, privacy controls, and applicable school policies before any real-data use.
