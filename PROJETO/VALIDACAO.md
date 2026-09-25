# Validação — Radar de Lotes V1.4.1

## Atualização automática privada

- Repositório privado; nenhuma credencial está no código ou no executável.
- Consulta autenticada à Release mais recente, com mensagens seguras para falta de credencial, rede e assets incompletos.
- Assets obrigatórios: `Instalar Radar de Lotes.exe` e `SHA256SUMS.txt`.
- Instalador recusado quando o SHA-256 não corresponde.
- Verificação automática no máximo uma vez a cada 24 horas, além da verificação manual.
- SQLite fora da pasta instalada, migrações numeradas e backup antes de migrar.
- Pipeline Windows recompila do zero em Python 3.12. Somente o GitHub Actions da `main` publica a Release privada.

`python -m pytest -q`: **32 testes aprovados**, incluindo atualização 1.4.0 → 1.4.1, checksum correto/incorreto, preservação do banco, limpeza segura do cache e ausência de publicação duplicada.

## Automações locais V1.4.1

- `RADAR.bat` contém as 15 opções previstas e delega para scripts separados.
- Build de teste não executa push, tag ou Release.
- Publicação exige branch `dev-vX.Y.Z`, confirmação `PUBLICAR`, testes e Git limpo.
- Backup da `main` antiga é criado e enviado antes do fast-forward da nova versão.
- Scripts usam Python 3.12 explicitamente e não contêm PAT, senha ou segredo.
- Workflow GitHub usa a nova pasta `PROJETO`, compila no Windows e guarda artefato validado.
- O workflow `test-build.yml` gera instalador de teste em `dev-v*` sem tag ou Release.
- O workflow `release.yml` é o único publicador final e só é disparado pela `main` ou manualmente.
- O BAT 10 apenas acompanha o GitHub Actions e abre a Release concluída.
- A sintaxe e os efeitos reais de Git/Inno/Agendador devem ser ensaiados também no computador Windows de desenvolvimento antes da próxima versão normal.

As validações de Credential Manager, Agendador, reinício, atualização sobre instalação anterior e desinstalação exigem Windows/VM real. O GitHub Actions cobre o build Windows e o autoteste do EXE, mas não substitui esse ensaio final do sistema operacional.

## Validado automaticamente

- 32 testes aprovados em 25/09/2026.
- Normalização de `395000`, `395000.00`, `395000,00`, `R$ 395.000`, `R$ 395.000,00` e `395 mil`.
- Limite de preço preservado em R$ 420.000.
- Contagem não é usada como bairro.
- Extração de telefone, WhatsApp e e-mail.
- URL do Google Maps criada somente com os dados existentes.
- Duplicidade entre fontes quando há evidência forte.
- Duplicata incompleta não apaga telefone, e-mail ou endereço completo.
- Dados complementares, fotos e contatos são combinados.
- Fontes e URLs diferentes do mesmo terreno são preservadas.
- Preço ou área ausente não gera classificação “Muito interessante”.
- “Muito interessante” exige bairro prioritário, preço e área compatíveis confirmados.
- Resultados claramente incompatíveis não ocupam a aba Novos.
- Consultas específicas e variações dos bairros prioritários foram verificadas.
- Objetos JSON-LD genéricos, menus e páginas institucionais são rejeitados.
- Migração do banco antigo para os novos campos.
- `PRAGMA integrity_check` do SQLite: OK.
- Interface criada e tela de detalhes aberta em modo gráfico offscreen.
- Empacotamento pelo PyInstaller concluído no ambiente Linux.
- Scripts do Agendador contêm `StartWhenAvailable` e `IgnoreNew`.
- Desinstalador chama a remoção das três tarefas.

## Busca real no ambiente de validação — 25/09/2026

- OLX: 7 consultas; 6 respostas HTTP 403 e 1 timeout; 0 anúncios válidos.
- Viva Real: 7 consultas; 6 respostas HTTP 403 e 1 timeout; 0 anúncios válidos.
- Imovelweb: 7 consultas; 6 respostas HTTP 403 e 1 timeout; 0 anúncios válidos.
- Chaves na Mão: 7 consultas responderam, mas 0 objetos passaram pelo filtro de anúncio real.
- Resultados públicos RSS: 6 consultas responderam sem bloqueio, mas 0 resultados relevantes passaram pelo filtro nesta execução.
- ZAP Imóveis: 7 páginas específicas testadas; 7 respostas HTTP 403; 0 anúncios válidos.
- Chaves na Mão (páginas específicas): 7 páginas testadas; houve timeout, as demais responderam, mas 0 anúncios válidos passaram pelo filtro.
- A validação anterior que indicava 2 itens na Chaves na Mão foi corrigida: eram objetos genéricos de JSON-LD e agora são rejeitados.
- Os bloqueios foram respeitados; nenhuma proteção foi contornada.
- A falha de uma fonte não interrompeu as demais.
- Nesta rede de validação não houve bairro prioritário com anúncio automaticamente aceito.
- Uma verificação independente do índice público encontrou páginas atuais com lotes em Nacional, Parque Xangri-lá, Vale das Amendoeiras, Bom Jesus e Arvoredo; os portais, porém, não disponibilizaram esses anúncios ao programa por JSON-LD público neste ambiente.
- O resultado pode ser diferente no Windows/rede do usuário, por isso o teste real no computador continua obrigatório.

## Depende de teste em Windows

- Gerar o `.exe` para Windows executando `build_windows.bat` no próprio Windows.
- Compilar `installer.iss` com Inno Setup.
- Instalar e confirmar as tarefas 08h, 14h e 20h no Agendador.
- Simular horário perdido e confirmar `StartWhenAvailable`.
- Desinstalar e confirmar que as três tarefas desapareceram.
- Confirmar os botões Ligar/WhatsApp no computador configurado.

O projeto não afirma que esses itens específicos do Windows foram executados no ambiente Linux.
