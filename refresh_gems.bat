@echo off
cls
echo.
echo ====================================================================
echo == Refreshing Jekyll Dependencies for Cross-Platform Builds      ==
echo ====================================================================
echo.
echo This script will create a new 'Gemfile.lock' that works on both
echo your local Windows machine and the Linux-based GitHub Actions.
echo.

REM Step 1: Delete the old Gemfile.lock to ensure a clean slate.
echo [1/4] Deleting old Gemfile.lock...
if exist Gemfile.lock (
    del Gemfile.lock
    echo      Done.
) else (
    echo      Gemfile.lock not found, skipping.
)
echo.

REM Step 2: Run bundle install to generate a new lock file for Windows.
echo [2/4] Running 'bundle install' to create a new lock file...
bundle install
if %errorlevel% neq 0 (
    echo.
    echo ERROR: 'bundle install' failed. Please check the errors above.
    goto :end_script
)
echo      Done.
echo.

REM Step 3: Add the Linux platform for GitHub Actions compatibility.
echo [3/4] Adding Linux platform to Gemfile.lock...
bundle lock --add-platform x86_64-linux
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to add Linux platform.
    goto :end_script
)
echo      Done.
echo.

REM Step 4: Verify that the Linux platform was added successfully.
echo [4/4] Verifying 'Gemfile.lock'...
findstr /C:"x86_64-linux" Gemfile.lock > nul
if %errorlevel% equ 0 (
    echo      SUCCESS! The platform 'x86_64-linux' was found in Gemfile.lock.
    echo.
    echo ====================================================================
    echo ==  PROCESS COMPLETE!                                           ==
    echo ====================================================================
    echo.
    echo Your 'Gemfile.lock' is now ready.
    echo.
    echo IMPORTANT: Please 'git add Gemfile.lock' and commit this updated
    echo            file to your repository now.
) else (
    echo.
    echo      ERROR: Verification failed. The Linux platform was not added.
)
echo.

:end_script
echo Press any key to exit...
pause > nul
