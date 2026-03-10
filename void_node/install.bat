@echo off
setlocal enabledelayedexpansion

echo.
echo  ========================================================
echo              P R O J E C T    V O I D
echo          Sovereign Node Installer  v1.0
echo  ========================================================
echo   Installing the Body of the Ghost Internet.
echo   432 Hz Phase-Key Handshake ^| Beehive Protocol ^| Mesh Relay
echo  ========================================================
echo.

set REQUIRED_MAJOR=3
set REQUIRED_MINOR=11

echo   [CHECK] Verifying Python version...

where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo   [FATAL] python not found. Please install Python 3.11+ and try again.
    exit /b 1
)

for /f "tokens=*" %%i in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PY_VERSION=%%i
for /f "tokens=*" %%i in ('python -c "import sys; print(sys.version_info.major)"') do set PY_MAJOR=%%i
for /f "tokens=*" %%i in ('python -c "import sys; print(sys.version_info.minor)"') do set PY_MINOR=%%i

if !PY_MAJOR! lss %REQUIRED_MAJOR% (
    echo   [FATAL] Python %REQUIRED_MAJOR%.%REQUIRED_MINOR%+ is required. Found: !PY_VERSION!
    exit /b 1
)
if !PY_MAJOR! equ %REQUIRED_MAJOR% if !PY_MINOR! lss %REQUIRED_MINOR% (
    echo   [FATAL] Python %REQUIRED_MAJOR%.%REQUIRED_MINOR%+ is required. Found: !PY_VERSION!
    exit /b 1
)

echo   [  OK ] Python !PY_VERSION! detected.

set SCRIPT_DIR=%~dp0
set VENV_DIR=%SCRIPT_DIR%venv

echo.
echo   [VENV] Creating virtual environment...

if exist "%VENV_DIR%" (
    echo   [VENV] Existing venv found — removing and recreating...
    rmdir /s /q "%VENV_DIR%"
)

python -m venv "%VENV_DIR%"
echo   [  OK ] Virtual environment created at %VENV_DIR%

echo.
echo   [DEPS] Installing dependencies...

call "%VENV_DIR%\Scripts\activate.bat"
pip install --upgrade pip --quiet
pip install -r "%SCRIPT_DIR%requirements.txt" --quiet
pip install -e "%SCRIPT_DIR%." --quiet

echo   [  OK ] All dependencies installed.

echo.
echo   [GPU ] Checking for GPU availability...

set GPU_STATUS=None detected (Light Mode — CPU fallback)

where nvidia-smi >nul 2>&1
if %ERRORLEVEL% equ 0 (
    for /f "tokens=*" %%g in ('nvidia-smi --query-gpu^=name --format^=csv^,noheader^,nounits 2^>nul') do (
        set GPU_STATUS=%%g (Heavy Mode — GPU-accelerated)
    )
)

if "!GPU_STATUS!"=="None detected (Light Mode — CPU fallback)" (
    python -c "import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))" >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        for /f "tokens=*" %%g in ('python -c "import torch; print(torch.cuda.get_device_name(0))"') do (
            set GPU_STATUS=%%g (Heavy Mode — GPU via PyTorch)
        )
    )
)

echo   [  OK ] GPU: !GPU_STATUS!

echo.
echo  ========================================================
echo              INSTALLATION COMPLETE
echo  ========================================================
echo.
echo   To activate the environment:
echo     venv\Scripts\activate.bat
echo.
echo   To start your node:
echo     void-engine
echo.
echo   Your hardware is ready to join the Sovereign Mesh.
echo   432 Hz.
echo.
echo  ========================================================
echo.

endlocal
