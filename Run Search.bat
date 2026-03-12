@echo off
title Clarity OS T4 - Local Document Search

echo.
echo ========================================
echo   Clarity OS T4 - Local Document Search
echo ========================================
echo.
echo Welcome! Let's search your documents.
echo.

REM Create results directory if it doesn't exist
if not exist "results" mkdir results

REM Check for saved default folder
set "default_folder="
if exist "default_folder.txt" set /p default_folder=<default_folder.txt

REM Ask for folder to search
if "%default_folder%"=="" (
    echo.
    echo Which folder would you like to search?
    echo Examples: 
    echo   .              (current folder)
    echo   Documents      (Documents folder)
    echo   C:\MyDocs      (full path)
    echo.
    set /p search_folder="Enter folder path: "
) else (
    echo Using saved folder: %default_folder%
    echo.
    echo Press Enter to use this folder, or type a new path:
    set /p search_folder="Folder path [%default_folder%]: "
    if "%search_folder%"=="" set "search_folder=%default_folder%"
)

REM Save the folder as default
echo %search_folder%>default_folder.txt

REM Ask for search type
echo.
echo What would you like to do?
echo   1. Search for specific text
echo   2. Ask a question (search + summarize)
echo.
set /p search_type="Choose 1 or 2: "

REM Ask for query
echo.
if "%search_type%"=="1" (
    set /p search_query="Enter text to search for: "
) else (
    set /p search_query="Enter your question: "
)

REM Set environment variables
set CLARITY_BOOT_DOC_PATH=boot_doc.json
set CLARITY_MAX_FILES=5000
set CLARITY_MAX_MATCHES=2000
set CLARITY_MAX_FILE_SIZE=10485760

echo.
echo Searching your documents...
echo This may take a moment...
echo.

REM Run the search and save results
if "%search_type%"=="1" (
    python -m clarity.main search --root "%search_folder%" --query "%search_query%" > results\last_answer.txt 2>&1
) else (
    python -m clarity.main ask --root "%search_folder%" --question "%search_query%" > results\last_answer.txt 2>&1
)

REM Get coverage information
python -m clarity.main sources --last > results\last_sources.txt 2>&1

echo.
echo ========================================
echo   Search Complete!
echo ========================================
echo.
echo Results saved to:
echo   results\last_answer.txt
echo   results\last_sources.txt
echo.
echo Would you like to:
echo   1. View the answer now
echo   2. View the sources/citations
echo   3. Search again
echo   4. Exit
echo.

set /p next_action="Choose 1-4: "

if "%next_action%"=="1" (
    echo.
    echo === ANSWER ===
    type results\last_answer.txt
    echo.
    pause
) else if "%next_action%"=="2" (
    echo.
    echo === SOURCES/CITATIONS ===
    type results\last_sources.txt
    echo.
    pause
) else if "%next_action%"=="3" (
    goto :start
) else (
    goto :end
)

:start
cls
goto :eof

:end
echo.
echo Thanks for using Clarity OS T4!
echo Your results are saved in the results folder.
pause
