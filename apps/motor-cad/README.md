# Motor CAD — SEPLAN Itapoá

Motor para leitura de PDF vetorial de projeto arquitetônico e geração de DXF compatível com AutoCAD 2026.

## Estado atual

- **Baseline operacional:** V07.2 — Clean Native Export.
- **V07.3 anterior:** rejeitada visualmente e mantida apenas como registro histórico (não padrão operacional).

## Como rodar (baseline V07.2)

1. Execute:

```bat
00_instalar_dependencias.bat
```

2. Execute (1º pavimento):

```bat
01_rodar_1pavimento.bat
```

3. Abra no AutoCAD 2026:

```text
output\Mallmann06_1Pavimento_V072.dxf
```

## Rodar por manifesto (modo genérico inicial)

O motor pode ser executado por `input_manifest` para separar parâmetros do projeto da lógica do processamento:

```bash
python run_manifest.py --manifest manifests/mallmann_baseline_manifest.json
```

Esse modo prepara a evolução para múltiplos PDFs, múltiplas páginas e múltiplas regiões por página.

Ver especificação em: `docs/INPUT_MANIFEST.md`.

## Layers baseline

- `A-WALL`
- `A-REF`

## Regra de evolução

- Não piorar visualmente a baseline V07.2.
- OVERKILL é termômetro externo, não etapa de correção.
- Novas hipóteses (ex.: classificação de DIM/TEXT) devem ser validadas fora do DXF de produção antes de promoção.
- Nenhuma feature nova deve alterar o DXF sem passar por testes automáticos e validação visual no AutoCAD.

## Testes de baseline

Rodar checks automáticos:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
