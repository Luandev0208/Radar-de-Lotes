# Radar de Lotes 1.5.0

- Busca manual por filtros, limitada a Belo Horizonte e Região Metropolitana.
- Cidade vazia não permite resultados de outros estados: a localização precisa ser confirmada na RMBH.
- Por padrão, somente anúncios com preço informado são exibidos.
- Links de páginas de busca/categoria são descartados; o Radar prioriza anúncios individuais de lotes.
- Google Maps agora usa coordenadas públicas do anúncio quando disponíveis e, no fallback, endereço + cidade + MG + Brasil.
- Banco atualizado de forma compatível para armazenar latitude/longitude, com backup antes da migração.
- Atualizações automáticas discretas, SHA-256 e reinício único preservados.
- Pacote de compatibilidade com Windows App Control preservado.
- O build de teste agora entrega também um ZIP COMPLETO com código, BATs, instaladores e registro para revisão futura.
