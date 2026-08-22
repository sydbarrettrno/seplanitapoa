# Dataset derivado do dashboard

O backend carrega `data/transport/part-*.b64`, que em conjunto formam o dataset derivado em formato columnar v2, comprimido em GZIP e codificado em Base64.

`data/metadata.json` registra a ordem das partes, o tamanho e o SHA-256 do GZIP. Antes de responder qualquer indicador, o backend valida Base64, checksum, descompressão, total de registros, unicidade de `ProtocoloID`, coerência temporal e ausência de campos pessoais proibidos.

O navegador não acessa o dataset bruto. A exposição ocorre somente pela API, com os campos necessários ao dashboard e sem CPF/CNPJ, requerente ou observações livres.
