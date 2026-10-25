@echo off
rem ifi for Windows PowerShell and Command Prompt. In the repo folder, type:
rem   .\ifi check        (PowerShell)      ifi check        (Command Prompt)
rem ifi's commands are bash scripts, so this runs them with Git Bash, which
rem comes with Git for Windows. See the launcher "ifi" next to this file.
setlocal
set "IFI_BASH=%ProgramFiles%\Git\bin\bash.exe"
if not exist "%IFI_BASH%" set "IFI_BASH=%LocalAppData%\Programs\Git\bin\bash.exe"
if not exist "%IFI_BASH%" goto nobash
"%IFI_BASH%" "%~dp0ifi" %*
exit /b %errorlevel%

:nobash
echo ifi needs Git Bash, which comes with Git for Windows: https://git-scm.com/download/win
echo If the site runs in Docker, you can also use ifi inside the container:
echo   docker compose exec web bash
echo   ifi %*
exit /b 1
