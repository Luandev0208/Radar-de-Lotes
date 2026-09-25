# REGISTRO PARA REVISÃO FUTURA NO WORK — Radar de Lotes

Base histórica: v1.4.3.
Linha atual de desenvolvimento: v1.5.0 e v1.5.1 de teste do updater.

Este arquivo deve ser entregue ao Work futuramente para AUDITAR e CORRIGIR o que já foi implementado, sem reconstruir o projeto do zero.

## Alterações acumuladas

### Busca com filtros
- Removido o perfil rígido antigo como regra principal.
- Busca manual abre filtros.
- Região padrão agora significa Belo Horizonte e Região Metropolitana, não "qualquer lugar" quando cidade fica vazia.
- Lista de cidades metropolitanas usada para validação da localização.
- Bairros livres, preço mínimo/máximo, área mínima/máxima, dimensões, topografia e murado.
- Checkbox "Mostrar somente anúncios com preço informado", ligado por padrão.
- Filtros salvos para execução agendada.
- Sem filtros salvos, a tarefa agendada não inventa uma busca.

### Qualidade dos resultados
- Resultados precisam ser lote/terreno.
- Páginas genéricas de busca/categoria/resultados são rejeitadas por heurística de URL.
- Links com sinais de anúncio individual são priorizados.
- Resultados públicos fora de BH/RMBH são rejeitados.
- Objetivo específico: impedir que VER ANÚNCIO leve apenas a uma página de pesquisa da OLX/Viva/ZAP/etc.

### Preço
- Por padrão, item sem preço informado é rejeitado.
- Preço é aceito apenas quando aparece explicitamente em offers/price público ou texto com formato claro de preço.
- UI identifica preço encontrado no anúncio.
- Usuário pode permitir anúncios sem preço desmarcando o filtro.

### Google Maps
- Adicionados latitude e longitude ao modelo e ao SQLite.
- Schema passou para v3 com backup pré-migração.
- JSON-LD tenta capturar geo.latitude/geo.longitude.
- Se houver coordenadas, Maps abre pelas coordenadas.
- Sem coordenadas, consulta usa endereço + bairro + cidade + MG + Brasil.
- Se não houver cidade confirmável, não gerar botão de Maps em vez de abrir local errado.
- Localização aproximada continua indicada quando não há número/coordenadas.

### Updater
- Verificação discreta em background.
- Sem botão fixo de atualizações.
- Aviso pequeno clicável apenas quando há versão nova.
- SHA-256 mantido.
- Updater público sem PAT/token.
- Helper espera PID antigo encerrar.
- /NORESTARTAPPLICATIONS e RestartApplications=no.
- Uma única abertura explícita após instalação.

### Windows App Control / Error 4551
- Mantido instalador EXE tradicional para compatibilidade com versões antigas.
- Criado pacote `Radar-de-Lotes-Instalador-Compatibilidade.zip`.
- Pacote compatível usa `UseSetupLdr=no`.
- Updater novo prefere o pacote compatível quando disponível.
- NÃO desativar/contornar WDAC, AppLocker, Smart App Control ou segurança do Windows.
- Teste físico obrigatório no PC do pai que apresentou Error 4551.

### RADAR.bat / automações de desenvolvimento
- AUTOMACOES/ local e no .gitignore.
- Template versionado em FERRAMENTAS_DESENVOLVIMENTO.
- Trocar de branch não substitui o BAT local.
- Inno Setup detectado também em %LOCALAPPDATA%.
- Opção 15 pede PUBLICAR uma vez.
- Evita repetir testes/builds caros.
- Backup remoto idempotente.
- Sem force push.
- pytest local usa basetemp próprio.
- .gitattributes para CRLF/LF previsível.

### Entrega completa
O artifact antigo tinha somente instaladores. Isso confundiu o usuário porque não continha código/BATs.

O workflow de teste agora também deve produzir:
`Radar-de-Lotes-vX.Y.Z-COMPLETO.zip`

Conteúdo esperado:
- AUTOMACOES/RADAR.bat;
- FERRAMENTAS_DESENVOLVIMENTO;
- PROJETO completo;
- testes/workflows;
- ENTREGA_PARA_TESTE;
- instaladores + SHA-256;
- este arquivo de revisão.

## v1.5.1
A v1.5.1 continua reservada para o teste real de atualização após a v1.5.0 ser instalada no PC do pai. Ela deve herdar todas as correções da v1.5.0 e mudar o mínimo possível além da versão/notas.

Fluxo a validar:
v1.5.0 instalada
→ detectar v1.5.1
→ aviso discreto
→ download do pacote compatível
→ SHA-256
→ fechar Radar antigo
→ instalar sem erro _MEI e sem execução bloqueada em TEMP
→ abrir uma única v1.5.1
→ preservar banco/status/histórico/filtros.

## Pontos para auditoria futura do Work
- Testar parsers/conectores com páginas reais atuais sem burlar bloqueios.
- Revisar heurística de URL de anúncio para reduzir falso positivo e falso negativo.
- Testar coordenadas/mapas com anúncios reais.
- Testar migração v2 -> v3 em cópia de banco real.
- Testar o pacote completo gerado no Actions.
- Testar BAT em CMD real com caminhos contendo espaços.
- Testar Error 4551 no PC afetado.
- Testar updater real 1.5.0 -> 1.5.1.
- Revisar identidade visual/ícone profissional ainda pendente.
