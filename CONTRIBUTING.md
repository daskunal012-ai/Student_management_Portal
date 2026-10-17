# Contributing

Thanks for your interest in improving the School Management Portal.

## Before opening a change

- Keep changes focused and explain the user-facing or technical problem.
- Do not include real student information, credentials, `.env` files, or local database files.
- Add or update tests for behavior changes.
- Update the README when setup or deployment instructions change.

## Local checks

```powershell
python -m pip install -r requirements-dev.txt
$env:SECRET_KEY = "local-test-secret"
$env:FLASK_DEBUG = "1"
$env:SEED_DEMO_DATA = "1"
python -m pytest -q
```

## Pull requests

Describe the change, how it was verified, and any known limitations. Include screenshots for significant interface changes, using fictional data only.
