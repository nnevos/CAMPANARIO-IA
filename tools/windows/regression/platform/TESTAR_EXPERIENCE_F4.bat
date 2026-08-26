@echo off
setlocal
cd /d "%~dp0\..\..\..\.."
echo Campanario - F4 Experience / Learning
uv run pytest -q tests/test_experience_learning.py tests/test_chat_service.py tests/test_platform_foundation_closure.py
endlocal
