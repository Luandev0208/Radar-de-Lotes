# Radar de Lotes — v1.5.1

Aplicativo local para Windows que organiza lotes em **Novos**, **Interessantes** e **Descartados**, com dados persistidos em SQLite no AppData do usuário.

## Busca por filtros

A busca não usa mais um perfil rígido de bairros/preço/área. Ao clicar em **BUSCAR AGORA**, o usuário escolhe os filtros da busca naquele momento:

- cidade;
- um ou vários bairros;
- preço mínimo e máximo;
- área mínima e máxima;
- dimensões;
- topografia;
- murado.

Campos vazios significam que aquele critério não limita a busca. Quando uma informação não está disponível no anúncio, o Radar não inventa o valor e marca o lote para confirmação.

Os últimos filtros escolhidos ficam salvos apenas para permitir buscas agendadas coerentes. Se nunca houve uma busca com filtros definidos, a busca agendada não inventa critérios.

## Dados dos anúncios

Os conectores usam apenas páginas e dados públicos. O Radar tenta extrair preço, área, dimensões, topografia, murado, endereço, contatos, imobiliária/corretor, descrição, fotos e código do anúncio quando essas informações estão realmente disponíveis.

CAB e CAM só são preenchidos quando aparecem explicitamente no material público consultado. CAPTCHA, login, bloqueios e proteções dos portais não são contornados.

## Google Maps

O Maps recebe endereço, bairro, cidade e estado normalizados. Endereços incompletos são identificados como localização aproximada e o botão mostra **APROX.** para não dar falsa precisão.

## Atualizações

O app verifica atualizações públicas em segundo plano. Se não houver versão nova, nenhum botão fixo é mostrado. Quando há uma nova versão, aparece apenas um aviso discreto clicável no topo.

Downloads continuam sendo validados por SHA-256 e não exigem conta, PAT, token, Git ou GitHub CLI no computador do usuário final.

O fluxo de atualização espera a instância antiga encerrar antes de iniciar o instalador e desativa reinícios concorrentes do Inno Setup.

## Compatibilidade com Windows App Control

Além do instalador EXE tradicional, o build gera:

`Radar-de-Lotes-Instalador-Compatibilidade.zip`

Esse pacote usa Inno Setup com `UseSetupLdr=no`, contendo `Setup.exe` e os arquivos `Setup-*.bin`. Ele evita que o Setup Loader copie e execute o instalador pela pasta TEMP, o que ajuda em máquinas onde uma política de Controle de Aplicativo bloqueia execução a partir de TEMP.

Nenhuma política de segurança é desativada ou burlada.

## Ferramentas de desenvolvimento

A pasta `AUTOMACOES/` é local e ignorada pelo Git. Para criar o menu local pela primeira vez, execute:

`FERRAMENTAS_DESENVOLVIMENTO\INSTALAR_RADAR_LOCAL.bat`

Isso copia o `RADAR.bat` para `AUTOMACOES\RADAR.bat`. Como ele fica fora do controle de versão, trocar de branch não substitui o BAT enquanto ele está rodando.

O menu mantém as opções individuais e a opção **15 - FAZER TUDO DE UMA VEZ**. A opção 15 pede `PUBLICAR` uma única vez e evita repetir testes/builds caros.

## Dados e backups

Banco, logs e backups ficam fora da pasta do programa, em AppData, e não são apagados ao atualizar. Migrações continuam com backup preventivo.

## Revisão futura

O arquivo `REVISAO_FUTURA_WORK.md` registra tudo que foi alterado nesta versão e os pontos que devem ser auditados posteriormente pelo Work.
