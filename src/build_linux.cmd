@echo off
echo Creating Linux package...

if not exist "release" mkdir "release"
if not exist "release\linux" mkdir "release\linux"

REM Copy Python script
copy "file_transfer_app.py" "release\linux\file_transfer_app.py" >nul

REM Create run script for Linux
(
echo #!/bin/bash
echo echo "Installing dependencies..."
echo pip3 install flask 2^>^&1 ^| grep -v "already satisfied" ^|^| true
echo echo "Starting File Transfer App..."
echo python3 file_transfer_app.py
) > "release\linux\run.sh"

REM Create README for Linux users
(
echo File Transfer App - Linux Version
echo =================================
echo.
echo REQUIREMENTS:
echo - Python 3.6 or higher
echo - pip3
echo.
echo HOW TO RUN:
echo -----------
echo chmod +x run.sh
echo ./run.sh
echo.
echo OR manually:
echo pip3 install flask
echo python3 file_transfer_app.py
echo.
) > "release\linux\README.txt"

echo Done! Check release\linux\
echo.
echo This package contains:
echo - file_transfer_app.py (the app)
echo - run.sh (easy launcher)
echo - README.txt (instructions)
echo.
pause