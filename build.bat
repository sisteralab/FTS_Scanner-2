@echo off
setlocal

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

if defined PYTHON_BIN (
  set "PYTHON_EXE=%PYTHON_BIN%"
) else (
  set "PYTHON_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"
)

if not exist "%PYTHON_EXE%" (
  echo Python not found: %PYTHON_EXE%
  exit /b 1
)

"%PYTHON_EXE%" "%ROOT_DIR%\tools\generate_icon.py"
if errorlevel 1 exit /b 1

"%PYTHON_EXE%" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --name "FTS_Scanner" ^
  --windowed ^
  --paths "%ROOT_DIR%\src" ^
  --hidden-import pyvisa ^
  --hidden-import pyvisa_py ^
  --add-data "%ROOT_DIR%\ximc;ximc" ^
  --add-data "%ROOT_DIR%\assets;assets" ^
  --icon "%ROOT_DIR%\assets\app_icon.ico" ^
  "%ROOT_DIR%\src\main.py"
if errorlevel 1 exit /b 1

echo Build complete: %ROOT_DIR%\dist\FTS_Scanner
