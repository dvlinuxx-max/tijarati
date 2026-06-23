@echo off
REM ====================================================================
REM  بناء نسخة تنفيذية (.exe) من برنامج «تجارتي»
REM  المتطلب: pip install pyinstaller
REM ====================================================================
chcp 65001 >nul
echo.
echo ============================================
echo   بناء برنامج تجارتي - النسخة التنفيذية
echo ============================================
echo.

pyinstaller --noconfirm --clean ^
  --name "تجارتي" ^
  --onefile ^
  --windowed ^
  --collect-all customtkinter ^
  --collect-all arabic_reshaper ^
  --collect-all bidi ^
  main.py

echo.
echo ============================================
echo   تم! ستجد الملف التنفيذي داخل مجلد dist
echo ============================================
echo.
pause
