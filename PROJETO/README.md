# Radar de Lotes — v1.5.x

Programa local para Windows que organiza anúncios individuais de lotes em **Novos**, **Interessantes** e **Descartados**. Banco, histórico e backups ficam no AppData do usuário.

## Busca por filtros

Ao clicar em **BUSCAR AGORA**, o usuário escolhe os filtros da busca. Não existe mais um perfil rígido obrigatório.

A região padrão é **Belo Horizonte e Região Metropolitana**. Deixar a cidade sem seleção específica NÃO libera buscas no Brasil inteiro: o Radar continua aceitando somente anúncios cuja localização possa ser confirmada em BH ou em cidades da região metropolitana cadastradas no programa.

Filtros disponíveis:
- região/cidade;
- um ou vários bairros;
- preço mínimo e máximo;
- área mínima e máxima;
- dimensões;
- topografia;
- murado;
- opção de mostrar somente anúncios com preço informado, ativada por padrão.

Os últimos filtros ficam salvos para as buscas agendadas. Se nunca houve filtros definidos, a busca agendada não inventa critérios.

## Somente anúncios de lotes, não páginas de pesquisa

Os conectores descartam links que parecem páginas de categoria, busca ou resultados. O Radar tenta salvar apenas URLs com sinais fortes de anúncio individual, como páginas de imóvel/anúncio/propriedade ou URLs com identificador de anúncio.

Resultados públicos também precisam indicar explicitamente lote/terreno e uma cidade confirmável da Região Metropolitana de Belo Horizonte.

O objetivo é evitar casos em que **VER ANÚNCIO** abre apenas uma busca vazia da OLX ou de outro portal.

## Preço confirmado

Por padrão, anúncios sem preço informado são ignorados. Um preço só é preenchido quando aparece explicitamente em dado estruturado público do anúncio ou em texto com formato de preço, como **R$ 395.000** ou **395 mil**.

A interface mostra quando o preço foi encontrado no anúncio. O usuário pode desativar esse filtro caso queira analisar anúncios sem preço.

## Google Maps

O Radar agora guarda latitude e longitude quando o próprio anúncio disponibiliza coordenadas públicas em JSON-LD. Quando existem coordenadas válidas, o Google Maps abre diretamente nelas.

Sem coordenadas, o Maps usa endereço + bairro + cidade + MG + Brasil. Se não houver cidade confirmada, o botão de Maps não é criado, evitando mandar o usuário para outra cidade ou estado. Endereços sem número continuam marcados como aproximados.

A migração para o novo banco adiciona latitude/longitude sem apagar os lotes antigos e faz backup preventivo antes da mudança.

## Atualizações

O app verifica atualizações públicas em segundo plano. Sem versão nova, não exibe botão fixo. Quando existe uma versão nova, mostra apenas um aviso pequeno e clicável.

O download é validado por SHA-256, não exige conta/PAT/token no PC final e o fluxo espera a instância antiga fechar antes de instalar. O Inno Setup não faz reinício concorrente.

## Windows App Control

O build gera:
- `Instalar Radar de Lotes.exe`;
- `Radar-de-Lotes-Instalador-Compatibilidade.zip`;
- `SHA256SUMS.txt`.

O ZIP de compatibilidade usa Inno Setup com `UseSetupLdr=no` para evitar o Setup Loader executado pela pasta TEMP. Nenhuma política de segurança é desativada ou contornada.

## Pacote COMPLETO de teste

O GitHub Actions de branch `dev-v*` agora também gera:

`Radar-de-Lotes-vX.Y.Z-COMPLETO.zip`

Esse arquivo contém:
- `AUTOMACOES/RADAR.bat`;
- `FERRAMENTAS_DESENVOLVIMENTO`;
- todo o `PROJETO`;
- testes e workflows;
- `ENTREGA_PARA_TESTE` com instaladores e SHA-256;
- `REVISAO_FUTURA_WORK.md`;
- arquivo de orientação.

Assim, o ZIP completo é diferente do artifact anterior que continha somente os instaladores.

## Ferramentas locais

`AUTOMACOES/` permanece ignorada pelo Git para que trocar de branch não substitua o BAT durante sua própria execução.

O template versionado fica em:
`FERRAMENTAS_DESENVOLVIMENTO/RADAR_LOCAL_TEMPLATE.bat`

E o instalador local em:
`FERRAMENTAS_DESENVOLVIMENTO/INSTALAR_RADAR_LOCAL.bat`.

## Segurança e fontes

O Radar não burla CAPTCHA, login, anti-bot, AppLocker, WDAC ou outras proteções. Quando uma fonte não fornece determinada informação publicamente, o campo permanece sem confirmação.
