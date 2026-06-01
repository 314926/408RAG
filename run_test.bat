@echo off
chcp 65001 > nul
cd /d D:\408RAG
python test_qa.py > test_output.log 2>&1
echo Exit code: %ERRORLEVEL% >> test_output.log
