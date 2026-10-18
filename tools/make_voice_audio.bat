@echo off
rem 音声モード用の読み上げ音声を VOICEVOX で作る(AIP-C01)。途中で閉じても、次回は続きから作る
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0.."
python tools\make_voice_audio.py %*
echo.
pause
