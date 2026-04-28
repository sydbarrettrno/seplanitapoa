# SEPLAN Pipeline — MVP 0 Inventário Documental

MVP inicial da SEPLAN IA para inventariar documentos de entrada, classificar arquivos por heurística simples e gerar saídas rastreáveis.

## Escopo

Este módulo:

- lista arquivos recursivamente;
- calcula SHA-256;
- registra extensão e tamanho;
- tenta contar páginas de PDFs quando houver biblioteca disponível;
- classifica documentos por nome e extensão;
- gera evidências, confiança e necessidade de revisão;
- produz JSON, CSV, HTML e log de auditoria.

Este MVP não executa OCR, não gera DXF, não aplica legislação, não cria API, não usa banco de dados e não altera `apps/motor-cad/`.

## Uso

```bash
python apps/seplan-pipeline/run_pipeline.py --input "<PASTA>" --output output/seplan_pipeline --mode inventory
```

## Saídas

A execução cria uma pasta por rodada:

```text
output/seplan_pipeline/<run_id>/
  input_inventory.json
  document_classification.json
  audit_log.json
  inventory_report.html
  inventory_report.csv
```

## Testes

```bash
python -m unittest discover -s apps/seplan-pipeline/tests -v
```
