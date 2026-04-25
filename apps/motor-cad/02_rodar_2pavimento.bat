@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\activate.bat" (
  echo Execute 00_instalar_dependencias.bat primeiro.
  pause
  exit /b 1
)
call .venv\Scripts\activate
python motor_v073.py --pdf "input\P02_06 - PMI - CONSTRUTORA MALLMANN.pdf" --page 0 --view 1550,450,2490,1640 --origin 1590,1600 --outdir output --name Mallmann06_2Pavimento_V073
pause
