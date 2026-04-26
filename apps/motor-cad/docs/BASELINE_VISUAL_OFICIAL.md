# Baseline Visual Oficial — Motor CAD (V07.2)

Status de validação visual no AutoCAD 2026: **PENDENTE**

## Identificação da baseline congelada

- Commit utilizado: `2478500`
- Motor geométrico: `apps/motor-cad/motor_v072.py`
- Runner por manifesto: `apps/motor-cad/run_manifest.py`
- PDF de origem: `apps/motor-cad/input/P02_06 - PMI - CONSTRUTORA MALLMANN.pdf`

## Comandos utilizados

### 1) Execução direta pelo motor V07.2

```bash
python motor_v072.py \
  --pdf "input/P02_06 - PMI - CONSTRUTORA MALLMANN.pdf" \
  --page 0 \
  --view 240,450,1160,1640 \
  --origin 280,1600 \
  --outdir <tmp>/old \
  --name baseline_oficial
```

### 2) Execução por manifesto

```bash
python run_manifest.py --manifest <tmp>/manifest_tmp.json
```

> Observação: o manifesto temporário usado no teste mantém a mesma região da fixture baseline e altera apenas diretórios/nome de saída para comparação em ambiente temporário.

## Hashes oficiais registrados

- SHA-256 do PDF de entrada:
  - `15da48530d30c72fc2d164af67959c507551fd52bacf825c17033fcbf0fc613b`
- SHA-256 do DXF via `motor_v072.py`:
  - `72db98f79ca9071b04258237256915b6d22227736f9fce817ab8bc64cff7bae1`
- SHA-256 do DXF via `run_manifest.py`:
  - `72db98f79ca9071b04258237256915b6d22227736f9fce817ab8bc64cff7bae1`
- Resultado de equivalência:
  - `DXF_EQUAL = True`

## Métricas registradas

- `final_lines`: `8654`
- `A-WALL`: `2951`
- `A-REF`: `5703`
- `removed_or_merged_before_export`: `3070`

## Checklist de validação visual no AutoCAD 2026

- [ ] Abrir o DXF no AutoCAD 2026 sem erros de importação.
- [ ] Confirmar que a visualização geral da planta está íntegra.
- [ ] Confirmar que paredes principais estão preservadas.
- [ ] Confirmar ausência de degradação visual em relação à referência aprovada.
- [ ] Rodar OVERKILL apenas como termômetro externo e registrar resultado.
- [ ] Registrar decisão final de validação visual (Aprovado/Rejeitado).

## Decisão final

- Status atual: **PENDENTE**
- Responsável pela validação visual: ______________________
- Data da validação: ____/____/________
- Parecer: ______________________________________________
