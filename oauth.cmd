@echo off
cd /d "%~dp0"
python setup_oauth.py --client-secret client_secret.json --account-label %1
