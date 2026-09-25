@echo off
setlocal
set BLENDER=F:\SteamLibrary\steamapps\common\Blender\blender.exe
set ROOT=.
echo ============================================================
echo  AC6Mech pipeline   Blender: %BLENDER%
echo  output: %ROOT%\assets\mech
echo ============================================================
for %%S in (01_ac6_build 02_ac6_export 03_ac6_render 04_ac6_verify) do (
  if exist "%ROOT%\scripts\%%S.py" (
    echo.
    echo [STAGE] %%S start  %time%
    "%BLENDER%" -b --python-exit-code 1 --python "%ROOT%\scripts\%%S.py"
    if errorlevel 1 (
      echo [FAIL] %%S exit code %errorlevel%  %time%
      pause
      exit /b 1
    )
    echo [OK] %%S done  %time%
  ) else (
    echo [SKIP] %%S.py not ready
  )
)
echo.
echo [DONE] all stages finished  %time%
pause
