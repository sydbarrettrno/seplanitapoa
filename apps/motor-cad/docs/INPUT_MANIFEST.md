# Input Manifest (engine genérica) — v0.1

O `input_manifest` separa parâmetros por projeto da lógica do motor.

Objetivos:
- processar múltiplos PDFs;
- processar múltiplas páginas por PDF;
- processar múltiplas regiões por página;
- garantir rastreabilidade e repetibilidade;
- evitar hardcode no código da engine.

Schema formal v0.1:
- `docs/schemas/input_manifest.schema.json`

## Estrutura mínima

```json
{
  "documents": [
    {
      "source_pdf": "input/projeto.pdf",
      "pages": [
        {
          "page_index": 0,
          "regions": [
            {
              "bbox": [100, 100, 1000, 1400],
              "origin": [100, 1400]
            }
          ]
        }
      ]
    }
  ]
}
```

## Campos obrigatórios (v0.1)

- `documents` (array)
- `documents[].source_pdf`
- `documents[].pages` (array)
- `documents[].pages[].page_index` (inteiro)
- `documents[].pages[].regions` (array)
- `documents[].pages[].regions[].bbox` (array com 4 números)
- `documents[].pages[].regions[].origin` (array com 2 números)

## Campos opcionais

Raiz:
- `manifest_version`
- `project_id`
- `project_name`
- `processing_version`
- `output_root`
- `notes`
- `tags`
- `expected`
- `export`
- `audit`

Documento (`documents[]`):
- `doc_id`
- `source_pdf_sha256`
- `output_dir`
- `clean.coord_tol`
- `clean.gap_tol`
- `notes`
- `tags`
- `expected`
- `export`
- `audit`

Região (`regions[]`):
- `region_id`
- `region_type`
- `drawing_type`
- `building_block`
- `level_id`
- `level_name`
- `scale`
- `output_name`
- `output_dir`
- `notes`
- `tags`

## Exemplo com múltiplas páginas

```json
{
  "project_id": "projeto_x",
  "documents": [
    {
      "source_pdf": "input/projeto_x.pdf",
      "pages": [
        {
          "page_index": 0,
          "regions": [{ "bbox": [100, 100, 900, 1200], "origin": [100, 1200] }]
        },
        {
          "page_index": 1,
          "regions": [{ "bbox": [120, 120, 920, 1220], "origin": [120, 1220] }]
        }
      ]
    }
  ]
}
```

## Exemplo com múltiplas regiões por página

```json
{
  "project_id": "projeto_y",
  "documents": [
    {
      "source_pdf": "input/projeto_y.pdf",
      "pages": [
        {
          "page_index": 0,
          "regions": [
            {
              "region_id": "bloco_a_terreo",
              "region_type": "floor_plan",
              "drawing_type": "floor_plan",
              "building_block": "A",
              "level_id": "L01",
              "level_name": "Térreo",
              "bbox": [200, 300, 1200, 1800],
              "origin": [200, 1800]
            },
            {
              "region_id": "bloco_a_cobertura",
              "region_type": "roof_plan",
              "drawing_type": "roof_plan",
              "building_block": "A",
              "level_id": "L02",
              "level_name": "Cobertura",
              "bbox": [1300, 300, 2200, 1800],
              "origin": [1300, 1800]
            }
          ]
        }
      ]
    }
  ]
}
```

## Como adicionar novo projeto ao golden set

1. Copie `manifests/mallmann_baseline_manifest.json` para um novo arquivo em `manifests/`.
2. Atualize `project_id`, `doc_id`, `source_pdf`, páginas e regiões.
3. Se possível, preencha `source_pdf_sha256` para rastreabilidade.
4. Valide o manifesto com a suíte de testes.
5. Execute o manifesto no motor.
6. Faça validação visual no AutoCAD antes de promover baseline.

## Como validar o manifesto

```bash
python -m unittest discover -s apps/motor-cad/tests -v
```

## Como rodar por manifesto

```bash
python run_manifest.py --manifest manifests/mallmann_baseline_manifest.json
```

## Observação

OVERKILL segue como métrica externa de auditoria, não etapa de correção da engine.
