@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" -m pip install --no-cache-dir "pywebview==5.4" "pythonnet==3.1.0" > pip_webview.log 2>&1
echo fin %errorlevel% >> pip_webview.log
