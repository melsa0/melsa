@echo off
REM ============================================================================
REM  bkg2d — 2D Background Subtraction Library — Windows Build
REM ============================================================================

REM Try system gcc first, then MSYS2
where gcc >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    if exist C:\msys64\ucrt64\bin\gcc.exe (
        set PATH=C:\msys64\ucrt64\bin;%PATH%
    ) else if exist C:\msys64\mingw64\bin\gcc.exe (
        set PATH=C:\msys64\mingw64\bin;%PATH%
    ) else (
        echo [HATA] gcc bulunamadi! MSYS2 veya MinGW kurun.
        exit /b 1
    )
)

echo.
echo === bkg2d — 2D Background Subtraction ===
echo.

echo [BUILD] Derleniyor...
gcc -std=c11 -O2 -Wall -Wextra -Iinclude -o bkg2d.exe src/bkg2d.c src/bkg2d_main.c -lm

if %ERRORLEVEL% NEQ 0 (
    echo [HATA] Derleme basarisiz!
    exit /b 1
)
echo [OK] bkg2d.exe olusturuldu.
echo.

echo [RUN] Calistiriliyor...
echo.
bkg2d.exe

echo.
echo === Tamamlandi ===
