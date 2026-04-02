@echo off
chcp 65001 >nul
title 修仙世界模拟器
cd /d "%~dp0"
echo ====================================
echo   修仙世界模拟器 - 启动中...
echo ====================================
echo.
echo 首次使用请先在设置中配置AI模型（如DeepSeek/MiniMax/Ollama）
echo 访问：http://localhost:5173
echo.
echo 按 Ctrl+C 停止服务
echo ====================================
echo.
"C:\Users\30682\AppData\Local\Programs\Python\Python312\python.exe" src\server\main.py --dev
pause
