@echo off
setlocal
cd /d "%~dp0"
set "LABEL=%~1"
if "%LABEL%"=="" set "LABEL=On-Demand Digest"
echo [%date% %time%] starting run: %LABEL%>> digest_runs.log
"C:\Users\sb737\.local\bin\claude.exe" -p "Read the file routine_prompt.md in the current directory and execute its steps exactly. The run_label for this run is: %LABEL%." --model claude-sonnet-5 >> digest_runs.log 2>&1
echo [%date% %time%] finished run: %LABEL% exit=%errorlevel%>> digest_runs.log
endlocal
