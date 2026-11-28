@echo off
rem setup.bat - first-run setup for this tutorial (Windows).
rem Finds Python 3.11-3.13, creates .venv, installs requirements.txt, creates .env from
rem .env.example, and runs the offline tests. Safe to run again. NO_PAUSE=1 skips the final pause.
rem SETUP_PYTHON=<path to python.exe> picks a Python instead of searching for one.
rem NEXTOP_WHEEL=<path to a nextop .whl> (or the path as the first argument: setup.bat C:\dl\nextop-....whl)
rem installs that wheel in place of nextop from PyPI, to try a nextop build before it is published. Without it,
rem nextop comes from PyPI as requirements.txt pins it.
setlocal EnableExtensions DisableDelayedExpansion
if not "%~1"=="" set "NEXTOP_WHEEL=%~f1"
cd /d "%~dp0"
set "PYTHONPATH="
set "VIRTUAL_ENV="
set "PYTHONUTF8=1"
set "NEXTOP_EXTRAS=[pdf]"
set "NEEDS_NODE=0"
set "NEXT_CMD=python get_paper.py"
set "STATUS=1"

echo ============================================================
echo  nextop Tutorial 5: PDF to PowerPoint - setup
echo  Folder: %CD%
echo ============================================================

if not exist "requirements.txt" (
    echo ERROR: requirements.txt is missing. Run setup.bat from the tutorial folder.
    goto :end
)

rem ---- 1. Python ---------------------------------------------------------
if exist ".venv\Scripts\python.exe" call :check_venv
if exist ".venv\Scripts\python.exe" goto :have_venv

call :find_python
if not defined PY goto :no_python
echo [1/5] Creating .venv with: %PY%
%PY% -m venv .venv
if errorlevel 1 goto :venv_failed
if not exist ".venv\Scripts\python.exe" goto :venv_failed
goto :venv_ready

:have_venv
echo [1/5] .venv already exists, using it.

:venv_ready
set "VPY=%CD%\.venv\Scripts\python.exe"
set "PATH=%CD%\.venv\Scripts;%PATH%"
"%VPY%" --version

rem ---- 2. Libraries ------------------------------------------------------
echo [2/5] Installing libraries from requirements.txt (the first time takes a few minutes)...
"%VPY%" -m pip install --disable-pip-version-check --upgrade pip
if errorlevel 1 goto :pip_failed
if defined NEXTOP_WHEEL goto :wheel_install
"%VPY%" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :pip_failed
goto :libs_done

:wheel_install
if not exist "%NEXTOP_WHEEL%" goto :no_wheel
echo       nextop from the local wheel: %NEXTOP_WHEEL%
findstr /v /r /c:"^nextop" requirements.txt > "%TEMP%\nextop_tutorial_requirements.txt"
"%VPY%" -m pip install --disable-pip-version-check "%NEXTOP_WHEEL%%NEXTOP_EXTRAS%" -r "%TEMP%\nextop_tutorial_requirements.txt"
if errorlevel 1 goto :pip_failed

:libs_done
if not defined NEXTOP_WHEEL call :sync_nextop
if errorlevel 1 goto :pip_failed
echo       Libraries installed.

rem ---- 3. .env -----------------------------------------------------------
echo [3/5] Settings file .env
if exist ".env" (
    echo       .env already exists, it was kept as it is.
) else (
    copy /y ".env.example" ".env" >nul
    echo       Created .env from .env.example.
)
echo       Names in .env - fill the EMPTY ones you need with a text editor, see README "Settings":
for /f "tokens=1 delims==" %%K in ('findstr /r /c:"^[A-Z][A-Z0-9_]*=" ".env.example"') do call :show_name %%K
echo       The default LLM is OpenAI: put your OpenAI API key in LLM_API_KEY. For another
echo       OpenAI-compatible API, change "base_url" in project.json and "model" in workers\*\worker.json.

rem ---- 4. Tools outside Python ------------------------------------------
set "NODE_MISSING=0"
if "%NEEDS_NODE%"=="1" (
    echo [4/5] Checking Node.js - the filesystem MCP server runs with npx
    where npx >nul 2>&1 && (echo       npx found.) || set "NODE_MISSING=1"
) else (
    echo [4/5] No tools outside Python needed.
)
if "%NODE_MISSING%"=="1" goto :no_node

rem ---- 5. Offline tests --------------------------------------------------
echo [5/5] Running the offline tests - no model, no internet mail
"%VPY%" -m pytest -q tests
if errorlevel 1 goto :tests_failed

call :read_version
set "STATUS=0"
echo.
echo ============================================================
echo  Setup OK
echo  nextop installed: %NEXTOP_VERSION%
echo ============================================================
echo  Next steps, in this folder:
echo    1. Fill .env (LLM_API_KEY is your OpenAI API key)
echo    2. .venv\Scripts\activate
echo    3. %NEXT_CMD%
echo  Then follow README.md from there.
goto :end

rem ---- helpers and error exits ------------------------------------------
:sync_nextop
rem requirements.txt pins nextop (e.g. nextop[pdf]==0.4.0). If another nextop version is installed (an older
rem one, or a wheel from an earlier run), install the pinned one in its place.
set "NEXTOP_PIN="
for /f "usebackq tokens=*" %%L in (`findstr /b /c:"nextop" requirements.txt`) do set "NEXTOP_PIN=%%L"
if not defined NEXTOP_PIN goto :eof
for /f "tokens=2 delims==" %%P in ("%NEXTOP_PIN%") do set "NEXTOP_WANT=%%P"
call :read_version
if "%NEXTOP_VERSION%"=="%NEXTOP_WANT%" goto :eof
echo       nextop installed: %NEXTOP_VERSION%; this tutorial needs %NEXTOP_WANT%, installing %NEXTOP_PIN%
"%VPY%" -m pip install --disable-pip-version-check "%NEXTOP_PIN%"
goto :eof

:read_version
set "NEXTOP_VERSION=not installed"
for /f "usebackq delims=" %%V in (`python -c "import nextop; print(nextop.__version__)" 2^>nul`) do set "NEXTOP_VERSION=%%V"
goto :eof

:show_name
findstr /r /c:"^%~1=." ".env" >nul 2>&1
if errorlevel 1 (echo         %~1  - EMPTY& goto :eof)
findstr /r /c:"^%~1=.*example" ".env" >nul 2>&1
if errorlevel 1 (echo         %~1  - has a value) else (echo         %~1  - placeholder, replace it)
goto :eof

:check_venv
".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if (3, 11) <= sys.version_info[:2] <= (3, 13) else 1)" >nul 2>&1
if not errorlevel 1 goto :eof
echo .venv is broken or has a Python outside 3.11-3.13, making it again...
rmdir /s /q ".venv"
goto :eof

:find_python
set "PY="
if defined SETUP_PYTHON call :try_python "%SETUP_PYTHON%"
if defined PY goto :eof
if defined SETUP_PYTHON (
    echo SETUP_PYTHON is set but is not a working Python 3.11-3.13: %SETUP_PYTHON%
    goto :eof
)
call :try_python py -3.12
if not defined PY call :try_python py -3.13
if not defined PY call :try_python py -3.11
if not defined PY call :try_python py -3
if not defined PY call :try_python python
goto :eof

:try_python
%* -c "import sys; sys.exit(0 if (3, 11) <= sys.version_info[:2] <= (3, 13) else 1)" >nul 2>&1
if not errorlevel 1 set "PY=%*"
goto :eof

:no_python
echo.
echo No Python 3.11, 3.12 or 3.13 was found on this computer.
where winget >nul 2>&1
if errorlevel 1 goto :no_winget
echo Installing Python 3.12 with winget...
winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
echo.
echo When the install has finished: CLOSE this window, open a NEW terminal
echo (so the new Python is found) and run setup.bat again.
goto :end

:no_winget
echo winget is not available. Install Python 3.12 from https://www.python.org/downloads/
echo (tick "Add python.exe to PATH"), then open a new terminal and run setup.bat again.
goto :end

:venv_failed
echo.
echo ERROR: could not create .venv with %PY%.
goto :end

:no_wheel
echo.
echo ERROR: NEXTOP_WHEEL points to a file that does not exist: %NEXTOP_WHEEL%
goto :end

:pip_failed
echo.
echo ERROR: installing the libraries failed. Check the internet connection and the messages above,
echo then run setup.bat again.
goto :end

:no_node
echo.
echo Setup NOT complete: Node.js is missing.
echo This tutorial starts the filesystem MCP server with npx, which comes with Node.js.
echo Install Node.js LTS, for example:  winget install -e --id OpenJS.NodeJS.LTS
echo then open a NEW terminal and run setup.bat again.
goto :end

:tests_failed
echo.
echo ============================================================
echo  Setup finished, but some offline tests FAILED - see the messages above.
echo ============================================================
goto :end

:end
if not "%NO_PAUSE%"=="1" pause
endlocal & exit /b %STATUS%
