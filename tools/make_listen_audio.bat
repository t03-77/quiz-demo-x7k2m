@echo off
rem 聞き流し用の音声(解説型・覚える用の要点)を VOICEVOX で作る(AIP-C01)。途中で閉じても、次回は続きから作る
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0.."
python tools\make_listen_audio.py %*
echo.
pause
