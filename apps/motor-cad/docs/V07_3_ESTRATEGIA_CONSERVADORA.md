# V07.3 — Estratégia Conservadora (DIM/TEXT)

Status: implementação inicial para separação de layers, mantendo a base geométrica da V07.2.

## Base obrigatória

A V07.2 Clean Native Export permanece como base técnica aprovada, com redução de sobreposições de 1117 para 19 no teste OVERKILL do AutoCAD 2026.

## Objetivo

Separar cotas e textos em layers próprios sem alterar geometria base:

- `A-DIM`: somente entidades com alta confiança de cota.
- `A-TEXT`: textos reais extraídos do PDF.
- `A-REF`: fallback conservador para tudo que estiver incerto.

## Regras aplicadas

- Nenhuma transformação geométrica nova para paredes.
- Nenhuma remoção/movimentação de entidades já exportadas pela lógica-base.
- Sem união global e sem colapso de paralelas fora da limpeza já existente na base.
- Compatibilidade DXF R12 / AC1009 mantida.

## Heurística conservadora desta etapa

1. Texto extraído via `page.get_text("dict")` e exportado como entidade `TEXT` em `A-TEXT`.
2. Promoção para `A-DIM` somente quando:
   - entidade já seria `A-REF` pela regra-base;
   - regra visual forte (principalmente traço laranja) ou, em casos mais restritos, traço fino com proximidade de texto de cota;
   - comprimento compatível com anotação de cota.
3. Se não atender com segurança, permanece em `A-REF`.

## Critério de segurança

Em caso de dúvida, manter `A-REF` para evitar regressão visual da V07.2.
