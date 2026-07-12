@echo off
rem Copies the reviewed permissions template into .claude\settings.json.
rem Running this script IS the act of granting the scheduled digest runs
rem their unattended permissions - run it yourself, don't automate it.
cd /d "%~dp0"
if not exist .claude mkdir .claude
copy /Y settings.template.json .claude\settings.json >nul
echo Done - .claude\settings.json is in place:
type .claude\settings.json
