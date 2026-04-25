# Motor CAD — SEPLAN Itapoá

Motor para leitura de PDF vetorial de projeto arquitetônico e geração de DXF compatível com AutoCAD 2026.

## Estado atual

- **Baseline operacional:** V07.2 — Clean Native Export.
- **V07.3 anterior:** mantida apenas como experimento rejeitado (não padrão operacional).

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

## Layers baseline

- `A-WALL`
- `A-REF`

## Regra de evolução

- Não piorar visualmente a baseline V07.2.
- OVERKILL é termômetro externo, não etapa de correção.
- Novas hipóteses (ex.: classificação de DIM/TEXT) devem ser validadas fora do DXF de produção antes de promoção.

## Testes de baseline

Rodar checks automáticos:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
