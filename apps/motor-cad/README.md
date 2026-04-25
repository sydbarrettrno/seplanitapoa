# Motor CAD — SEPLAN Itapoá

Motor experimental para leitura de PDF vetorial de projeto arquitetônico e geração de DXF compatível com AutoCAD 2026.

## Versões incluídas

- V07.2 — Clean Native Export (base técnica aprovada).
- V07.3 — Separação conservadora de cotas/textos em layers dedicados.

## Como rodar

1. Execute:

```bat
00_instalar_dependencias.bat
```

2. Execute V07.3 (1º pavimento):

```bat
01_rodar_1pavimento.bat
```

3. Abra no AutoCAD 2026:

```text
output\Mallmann06_1Pavimento_V073.dxf
```

## Layers atuais

- `A-WALL` — geometria principal de paredes (mantida da V07.2).
- `A-REF` — referências e entidades incertas.
- `A-DIM` — entidades de cota promovidas de forma conservadora.
- `A-TEXT` — textos reais extraídos do PDF.

## Regras de evolução (V07.3)

- Não alterar a geometria base da V07.2.
- Se houver dúvida de classificação, manter em `A-REF`.
- Não aplicar interpretação semântica global (portas, janelas, mobiliário etc. ficam fora desta etapa).
- DXF deve permanecer compatível com R12 / AC1009 e abrir no AutoCAD 2026.
