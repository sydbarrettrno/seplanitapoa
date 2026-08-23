# SEPLAN | Gestão à Vista

Dashboard institucional da Secretaria de Planejamento de Itapoá-SC para acompanhamento dos protocolos 2025+.

## Fonte oficial dos números

O **Excel é a fonte de verdade** do dashboard.

Fluxo de atualização:

`BASE2326.xlsx → scripts/importar_excel.py → validação/sanitização → data/safe_chunks → GitHub → Vercel`

O arquivo Excel bruto **não é publicado** no GitHub porque contém dados pessoais e observações livres. O importador lê a aba `BASE23-26`, mantém apenas os campos necessários aos indicadores, reutiliza a classificação já consolidada quando disponível e grava somente o transporte público sanitizado.

**Carga atual:** `BASE2326.xlsx`, 6.975 protocolos de 2025+, com dados até 22/08/2026.

Para atualizar no Windows:

```bat
scripts\ATUALIZAR_DASHBOARD.bat "C:\caminho\BASE2326.xlsx"
```

O script valida a base, executa os testes, publica somente `data/metadata.json` e `data/safe_chunks/` e faz `git push`; o Vercel publica automaticamente o novo commit.

Também é possível executar somente a importação:

```powershell
python scripts\importar_excel.py "C:\caminho\BASE2326.xlsx"
```

Se houver uma nova planilha de classificação consolidada, ela pode ser aplicada junto à importação:

```powershell
python scripts\importar_excel.py "C:\caminho\BASE2326.xlsx" --classificacao "C:\caminho\SEPLAN_StatusReal_V08_Taxonomia_Consolidada.xlsx"
```

## Arquitetura

- **Frontend:** HTML + CSS + JavaScript nativos, sem framework e sem etapa de build.
- **Backend:** Python padrão em `api/index.py`, compatível com Vercel Python Functions.
- **Regra de negócio:** `backend/core.py` concentra filtros, métricas, auditoria e drill-down.
- **Fonte operacional:** Excel local/privado.
- **Dados publicados:** transporte sanitizado em partes Base64 dentro de `data/safe_chunks/`; o backend recompõe o GZIP em memória e valida tamanho + SHA-256 antes da carga.
- **Privacidade:** não são publicados nomes de requerentes/responsáveis, CPF/CNPJ, observações livres nem inscrição imobiliária exata.
- **Deploy:** GitHub `main` → Vercel, frontend e API no mesmo domínio.

Não existe dependência de Node/npm para executar o dashboard localmente.

## Rodar localmente

```powershell
python scripts\validate.py
python -m unittest discover -s tests -v
python scripts\dev.py
```

Acesse:

- Dashboard: `http://localhost:8000`
- Saúde do backend: `http://localhost:8000/api?action=health`

A publicação deve ser bloqueada se a auditoria da base falhar. O workflow `.github/workflows/ci.yml` executa validação e testes em cada push/PR.

## Indicadores

Os 11 indicadores oficiais da Chefia permanecem como referência do produto. Indicadores sem fonte suficiente aparecem explicitamente como **não integrados**, sem números inferidos.

Consulte `docs/INDICADORES.md` e `docs/AUDITORIA.md`.
