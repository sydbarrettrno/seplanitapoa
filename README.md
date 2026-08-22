# SEPLAN | Gestão à Vista

Dashboard institucional da Secretaria de Planejamento de Itapoá-SC para acompanhamento dos protocolos 2025+.

## Arquitetura

- **Frontend:** HTML + CSS + JavaScript nativos, sem framework e sem etapa de build.
- **Backend:** Python padrão em `api/index.py`, compatível com Vercel Python Functions.
- **Regra de negócio:** `backend/core.py` concentra filtros, métricas, auditoria e drill-down.
- **Dados publicados:** `data/transport/part-*.b64` (GZIP codificado em Base64, validado por checksum), derivado e sem CPF/CNPJ, requerente ou observações livres.
- **Deploy:** um único projeto Vercel; frontend e API no mesmo domínio.

Não existe dependência de Node/npm para executar o dashboard localmente.

## Rodar localmente

```powershell
python scripts/dev.py
```

Acesse:

- Dashboard: `http://localhost:8000`
- Saúde do backend: `http://localhost:8000/api?action=health`

## Validar antes de publicar

```powershell
python scripts/validate.py
python -m unittest discover -s tests -v
```

A publicação deve ser bloqueada se a auditoria da base falhar. O workflow `.github/workflows/ci.yml` executa estas verificações em cada push/PR.

## Indicadores

P0 funcionais: recebidos, concluídos formais, estoque atual, tempo de tramitação (mediana/média/P90), percentual parado por limite configurável, fluxo mensal, aging e gargalos operacionais.

Os indicadores que ainda exigem fonte complementar aparecem explicitamente como **não integrados**, sem números inferidos: prazo oficial, diligências, fiscalizações realizadas, denúncias recebidas/respondidas e projetos públicos por etapa.

Consulte `docs/INDICADORES.md` e `docs/AUDITORIA.md`.
