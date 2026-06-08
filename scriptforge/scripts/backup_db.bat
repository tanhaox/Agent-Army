@echo off
setlocal enabledelayedexpansion

REM ── ScriptForge PostgreSQL Backup Script ──
REM Runs daily via Windows Task Scheduler at 03:00

set PG_DUMP="C:\Program Files\PostgreSQL\18\bin\pg_dump.exe"
set PGHOST=localhost
set PGPORT=5432
set PGDATABASE=scriptforge
set PGUSER=scriptforge
set PGPASSWORD=sf_dev_2024

set BACKUP_DIR=%~dp0..\backend\backups
set RETAIN_DAYS=7

REM Create backup dir if not exists
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM Generate timestamp
for /f "tokens=1-6 delims=/:. " %%a in ("%date% %time%") do (
    set TIMESTAMP=%%a%%b%%c_%%d%%e%%f
)
set TIMESTAMP=%TIMESTAMP: =0%

set BACKUP_FILE=%BACKUP_DIR%\backup_scriptforge_%TIMESTAMP%.sql

REM Run pg_dump
echo [%date% %time%] Starting backup: %BACKUP_FILE%
%PG_DUMP% -h %PGHOST% -p %PGPORT% -U %PGUSER% -d %PGDATABASE% --no-password -F p -f "%BACKUP_FILE%"

if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] ERROR: pg_dump failed with exit code %ERRORLEVEL%
    if exist "%BACKUP_FILE%" del "%BACKUP_FILE%"
    exit /b 1
)

REM Compress with gzip if available
where gzip >nul 2>&1
if %ERRORLEVEL% equ 0 (
    gzip "%BACKUP_FILE%"
    set BACKUP_FILE=%BACKUP_FILE%.gz
    echo [%date% %time%] Compressed to: !BACKUP_FILE!
)

for %%A in ("%BACKUP_FILE%") do set SIZE=%%~zA
echo [%date% %time%] Backup completed: %BACKUP_FILE% (%SIZE% bytes)

REM Cleanup old backups (older than RETAIN_DAYS)
echo [%date% %time%] Cleaning backups older than %RETAIN_DAYS% days...
forfiles /p "%BACKUP_DIR%" /m backup_scriptforge_* /d -%RETAIN_DAYS% /c "cmd /c echo Deleting: @path & del @path" 2>nul

echo [%date% %time%] Done.
endlocal
