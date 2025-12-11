@echo off
echo ================================================
echo   Building Thai ID Card Reader .exe
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install dependencies
echo [1/3] Installing dependencies...
pip install -r requirements.txt

REM Build exe
echo.
echo [2/3] Building executable...
pyinstaller --onefile --windowed --name="ThaiIDReader" thai_id_reader.py

REM Check if build was successful
if exist "dist\ThaiIDReader.exe" (
    echo.
    echo [3/3] Build successful!
    echo.
    echo ================================================
    echo   ThaiIDReader.exe created in dist\ folder
    echo ================================================
    echo.
    echo You can now distribute dist\ThaiIDReader.exe
    echo.
) else (
    echo.
    echo ERROR: Build failed!
    echo.
)

pause
