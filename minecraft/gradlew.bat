@echo off
python "%~dp0..\tools\gradle.py" %*
exit /b %errorlevel%
