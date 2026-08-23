@echo off
setlocal
cd /d "%~dp0\.."

if "%~1"=="" (
  set /p XLSX=Informe o caminho completo do Excel BASE2326.xlsx: 
) else (
  set "XLSX=%~1"
)

if not exist "%XLSX%" (
  echo [ERRO] Excel nao encontrado: %XLSX%
  exit /b 1
)

python scripts\importar_excel.py "%XLSX%"
if errorlevel 1 exit /b 1

python scripts\validate.py
if errorlevel 1 exit /b 1

python -m unittest discover -s tests -v
if errorlevel 1 exit /b 1

git add data\metadata.json data\safe_chunks
git diff --cached --quiet
if not errorlevel 1 (
  echo Nenhuma alteracao de dados encontrada.
  exit /b 0
)

git commit -m "data: atualizar dashboard pelo Excel"
if errorlevel 1 exit /b 1

git push origin main
if errorlevel 1 exit /b 1

echo.
echo Dashboard atualizado. O Vercel publicara automaticamente o novo commit.
endlocal
