@echo off
echo Building Windows executable...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
)

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "FileTransferApp.spec" del /q "FileTransferApp.spec"

echo Building...
pyinstaller --onefile --windowed --name "FileTransferApp" file_transfer_app.py

if %errorlevel% neq 0 (
    echo Build failed!
    pause
    exit /b 1
)

if not exist "release" mkdir "release"
copy "dist\FileTransferApp.exe" "release\FileTransferApp-Windows.exe" >nul

del /q "FileTransferApp.spec"

echo Done! Check release\FileTransferApp-Windows.exe
pause