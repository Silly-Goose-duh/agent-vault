@echo off
REM Cross-platform-ish launcher for Windows hooks: pick py -3, python, or python3
set SCRIPT=%~1
shift
if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
  "%LocalAppData%\Programs\Python\Python311\python.exe" "%SCRIPT%" %*
  exit /b %ERRORLEVEL%
)
where py >nul 2>nul && (
  py -3 "%SCRIPT%" %*
  exit /b %ERRORLEVEL%
)
where python >nul 2>nul && (
  python "%SCRIPT%" %*
  exit /b %ERRORLEVEL%
)
where python3 >nul 2>nul && (
  python3 "%SCRIPT%" %*
  exit /b %ERRORLEVEL%
)
echo Python 3 not found on PATH. Install Python 3 to use grok-build-obsidian hooks. >&2
exit /b 0
