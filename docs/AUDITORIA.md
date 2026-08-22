# Auditoria e critérios de publicação

A carga é validada pelo backend antes de responder ao dashboard.

Critérios bloqueantes atuais:

1. `ProtocoloID` obrigatório e único.
2. Último trâmite não pode ser anterior à abertura.
3. Encerramento não pode ser anterior à abertura.
4. O dataset público não pode conter CPF/CNPJ, nome do requerente/responsável, observações livres ou inscrição imobiliária exata.
5. O total carregado deve coincidir com `data/metadata.json`.

Base derivada atual:

- 6.957 protocolos.
- 2025: 4.165.
- 2026: 2.792.
- Atualização da fonte: 20/08/2026 18:58:21.

A base de dashboard é derivada de `SEPLAN_2025_MAIS_PROCESSADO.csv` e `SEPLAN_BASE_REFINADA_2025_MAIS_V03.csv`. Os arquivos-fonte completos não são publicados neste repositório.
