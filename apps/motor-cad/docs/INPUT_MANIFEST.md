# Input Manifest (engine genérica)

O manifesto define **parâmetros por projeto** sem hardcode no motor.

## Estrutura mínima

- `project_id`
- `project_name`
- `processing_version`
- `output_root`
- `documents[]`
  - `source_pdf`
  - `output_dir`
  - `clean.coord_tol`
  - `clean.gap_tol`
  - `pages[]`
    - `page_index`
    - `regions[]`
      - `region_id`
      - `region_type`
      - `bbox` (x0,y0,x1,y1)
      - `origin` (x,y)
      - `scale`
      - `output_name`
      - `notes`

## Objetivo

Separar lógica de processamento da configuração por amostra/projeto.

## Exemplo

Use: `manifests/mallmann_baseline_manifest.json`.
