@echo off
setlocal
cd /d "%~dp0"
set "LABEL=%~1"
if "%LABEL%"=="" set "LABEL=On-Demand Digest"
>>digest_runs.log echo [%date% %time%] starting run: %LABEL%
"C:\Users\sb737\.local\bin\claude.exe" -p "Read the file routine_prompt.md in the current directory and execute its steps exactly. The run_label for this run is: %LABEL%." --model claude-sonnet-5 >> digest_runs.log 2>&1
>>digest_runs.log echo [%date% %time%] finished run: %LABEL% exit=%errorlevel%
endlocal
