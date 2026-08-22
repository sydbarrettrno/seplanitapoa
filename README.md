# SEPLAN | Gestão à Vista

Dashboard institucional da Secretaria de Planejamento de Itapoá-SC para acompanhamento dos protocolos 2025+.

## Arquitetura

- **Frontend:** HTML + CSS + JavaScript nativos, sem framework e sem etapa de build.
- **Backend:** Python padrão em `api/index.py`, compatível com Vercel Python Functions.
- **Regra de negócio:** `backend/core.py` concentra filtros, métricas, auditoria e drill-down.
- **Dados publicados:** transporte sanitizado em partes Base64 dentro de `data/safe_chunks/`; o backend recompõe o GZIP em memória e valida tamanho + SHA-256 antes da carga.
- **Privacidade:** não são publicados nomes de requerentes/responsáveis, CPF/CNPJ, observações livres nem inscrição imobiliária exata. O gargalo público é uma categoria operacional derivada do status.
- **Deploy:** frontend e API no mesmo domínio.

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

P0 funcionais: recebidos, concluídos formais, estoque atual, tempo de tramitação (mediana/média/P90), percentual parado por limite configurável, fluxo mensal, aging, categorias, status e gargalos operacionais.

Indicadores que ainda exigem fonte complementar aparecem explicitamente como **não integrados**, sem números inferidos: prazo oficial, diligências, fiscalizações realizadas, denúncias recebidas/respondidas e projetos públicos por etapa.

Consulte `docs/INDICADORES.md` e `docs/AUDITORIA.md`.
