@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if errorlevel 1 goto folder_error

rem Detect a supported Python installation.
where py >nul 2>nul
if errorlevel 1 goto try_python
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 goto try_python
set "PY_CMD=py -3"
goto check_libraries

:try_python
where python >nul 2>nul
if errorlevel 1 goto python_missing
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 goto python_missing
set "PY_CMD=python"

:check_libraries
%PY_CMD% -c "import tkinter, numpy, matplotlib" >nul 2>nul
if not errorlevel 1 goto launch

echo Installing required Python libraries...
%PY_CMD% -m pip --version >nul 2>nul
if errorlevel 1 (
    %PY_CMD% -m ensurepip --upgrade
    if errorlevel 1 goto pip_error
)
%PY_CMD% -m pip install -r "requirements.txt"
if errorlevel 1 goto pip_error

:launch
%PY_CMD% "bed_map.py"
if errorlevel 1 goto app_error
exit /b 0

:python_missing
echo ERROR: Python 3.10 or newer was not found.
echo Install Python from https://www.python.org/downloads/windows/
echo During setup, enable Add python.exe to PATH.
goto failed

:pip_error
echo ERROR: Could not install the required libraries.
echo Check the internet connection and Python installation.
goto failed

:folder_error
echo ERROR: Could not open the application directory.
goto failed

:app_error
echo ERROR: The application closed with an error.
echo Copy the error information from this window.
goto failed

:failed
echo.
pause
exit /b 1
