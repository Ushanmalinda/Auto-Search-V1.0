@echo off
echo ============================================
echo Edge Auto-Search Tool - EXE Builder
echo ============================================
echo.

echo [1/3] Checking dependencies...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller pyautogui pyperclip
) else (
    echo Dependencies OK!
)
echo.

echo [2/3] Building executable...
echo This may take a few minutes...
pyinstaller newVersion.spec
echo.

if exist "dist\EdgeAutoSearch.exe" (
    echo ============================================
    echo [3/3] BUILD SUCCESSFUL!
    echo ============================================
    echo.
    echo Your executable is ready at:
    echo   dist\EdgeAutoSearch.exe
    echo.
    echo File size: 
    dir /B "dist\EdgeAutoSearch.exe" | find /V ""
    echo.
    echo You can now share EdgeAutoSearch.exe with your friends!
    echo.
    pause
) else (
    echo ============================================
    echo BUILD FAILED!
    echo ============================================
    echo Please check the error messages above.
    echo.
    pause
)
