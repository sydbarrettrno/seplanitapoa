# Dataset sanitizado do dashboard

O repositório público contém apenas uma visão derivada e sanitizada em `data/safe_transport.json.gz`.

O transporte guarda somente números de protocolo, datas codificadas como deslocamento, macroprocesso, categoria e status operacional. Não publica nomes de requerentes/responsáveis, CPF/CNPJ, observações livres nem inscrição imobiliária exata. O gargalo exibido é derivado determinísticamente do status pelo backend.

`data/metadata.json` registra o tamanho e o SHA-256 do artefato GZIP. Antes de responder indicadores, o backend valida checksum, total de registros, unicidade de `ProtocoloID`, coerência temporal e ausência dos campos proibidos.
