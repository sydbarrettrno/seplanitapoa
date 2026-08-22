# Dicionário de indicadores — Gestão à Vista

## P0 publicados

| ID | Indicador | Regra implementada |
|---|---|---|
| KPI01 | Processos recebidos | Protocolos únicos com `DataAbertura` no período. |
| KPI02 | Processos concluídos — produção | Protocolos com `DataEncerramento` formal no período. Status terminal sem data não conta como produção. |
| KPI03 | Estoque pendente | Posição atual: `DataEncerramento` vazia e `SituacaoAtual` não terminal. O filtro de período não reconstrói estoque histórico. |
| KPI04 | Tempo de tramitação | `DataEncerramento - DataAbertura` dos concluídos elegíveis no período; mediana, média e P90. |
| KPI05 | % parados > X dias | Estoque com `DiasSemMovimento > X` / estoque elegível. X configurável em 15/30/60/90/120 dias no frontend. |
| KPI11 | Pendências por setor/gargalo operacional | Categoria operacional derivada de `StatusOperacional`; nomes de pessoas/empresas não são publicados. |

## Não publicar como número ainda

- **KPI06 — % concluído dentro do prazo:** falta DIM_PRAZOS oficial e regra de suspensão/espera externa.
- **KPI07 — diligências por processo:** exige histórico completo de eventos.
- **KPI08 — fiscalizações realizadas:** status não comprova ato executado.
- **KPI09 — denúncias recebidas/respondidas:** taxonomia ainda combina Denúncia/Fiscalização.
- **KPI10 — projetos públicos por etapa:** exige base complementar de carteira de projetos.

## Terminalidade para estoque

São terminais para a posição atual no modelo publicado: `Encerrado administrativo`, `Arquivado` e `Cancelado`.

A produção do período continua exigindo `DataEncerramento` formal.
