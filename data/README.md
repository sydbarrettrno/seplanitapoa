# Dataset sanitizado do dashboard

O repositório público contém somente uma visão derivada e sanitizada do corpus 2025+.

O transporte está em `data/safe_chunks/`: partes Base64 de um GZIP validado. O backend concatena as partes na ordem registrada em `data/metadata.json`, decodifica Base64, verifica tamanho e SHA-256, descomprime o payload e só então libera os indicadores.

O dataset público guarda números de protocolo, datas codificadas como deslocamento, macroprocesso, categoria e status operacional. Não publica nomes de requerentes/responsáveis, CPF/CNPJ, observações livres nem inscrição imobiliária exata. O gargalo exibido é derivado determinísticamente do status pelo backend.

Antes de responder indicadores, o backend também valida total de registros, unicidade de `ProtocoloID`, coerência temporal e ausência dos campos proibidos.
