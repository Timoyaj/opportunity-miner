@echo off
REM OpportunityMiner AI Runner Script
setlocal enabledelayedexpansion

cd /d "%~dp0"

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="health" goto health
if "%1"=="scan" goto scan
if "%1"=="report" goto report
if "%1"=="ui" goto ui
if "%1"=="test" goto test
if "%1"=="all" goto all

:help
echo ===============================================================================
echo OpportunityMiner AI - End-to-End Command Runner
echo ===============================================================================
echo Usage:
echo   run.bat health    - Check public source feed availability
echo   run.bat scan      - Ingest, filter, cluster, and score opportunities
echo   run.bat report    - Generate daily Markdown and JSON executive briefing
echo   run.bat ui        - Launch Streamlit Opportunity CRM Dashboard
echo   run.bat test      - Run automated pytest verification suite
echo   run.bat all       - Run health check, full scan, and generate report
echo ===============================================================================
goto end

:health
echo [*] Checking source feed connectivity...
python -m opportunity_miner.cli health
goto end

:scan
echo [*] Executing OpportunityMiner Scan across active sources...
python -m opportunity_miner.cli scan --sources all
goto end

:report
echo [*] Generating Daily Intelligence Briefing...
python -m opportunity_miner.cli report
goto end

:ui
echo [*] Starting Streamlit CRM Dashboard on port 8501...
streamlit run src/opportunity_miner/ui/app.py --server.port 8501
goto end

:test
echo [*] Running automated unit test suite...
pytest -v
goto end

:all
echo [*] Running end-to-end pipeline (Health -> Scan -> Report)...
python -m opportunity_miner.cli health
python -m opportunity_miner.cli scan --sources all
python -m opportunity_miner.cli report
goto end

:end
