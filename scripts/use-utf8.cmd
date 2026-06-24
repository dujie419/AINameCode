@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
echo UTF-8 terminal encoding enabled for this cmd session.
cmd /k
