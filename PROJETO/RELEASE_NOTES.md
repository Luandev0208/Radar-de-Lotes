# Radar de Lotes 1.5.0

- Busca manual agora abre filtros escolhidos na hora, sem perfil rígido de bairros/preço/área.
- Conectores e parsers extraem mais dados públicos sem inventar informações e sem contornar bloqueios.
- Google Maps usa endereço/bairro/cidade/UF normalizados e marca localização aproximada quando necessário.
- Atualizações são verificadas em segundo plano e só aparece um aviso discreto quando existe versão nova.
- Fluxo de atualização aguarda a instância antiga encerrar e desativa reinício concorrente do Inno Setup.
- Incluído pacote de instalação compatível com ambientes que bloqueiam execução do Setup pela pasta TEMP.
- Ferramentas de desenvolvimento passam a usar AUTOMACOES local e ignorada pelo Git.
- RADAR.bat revisado: Inno em LocalAppData, opção 15 sem duplicar testes/builds e apenas uma confirmação PUBLICAR.
- .gitattributes adicionado para reduzir alterações falsas de LF/CRLF.
