@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\activate.bat" (
  echo Execute 00_instalar_dependencias.bat primeiro.
  pause
  exit /b 1
)
call .venv\Scripts\activate
python motor_v072.py --pdf "input\P02_06 - PMI - CONSTRUTORA MALLMANN.pdf" --page 0 --view 240,450,1160,1640 --origin 280,1600 --outdir output --name Mallmann06_1Pavimento_V072
pause
