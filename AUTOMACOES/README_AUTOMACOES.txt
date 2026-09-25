RADAR DE LOTES - GUIA RAPIDO DAS AUTOMACOES
============================================

Comece sempre dando dois cliques em RADAR.bat.

ANTES DE PROGRAMAR UMA NOVA VERSAO
1. Escolha 14 para conferir o ambiente.
2. Escolha 6 para criar dev-vX.Y.Z.
3. Nunca desenvolva diretamente no main.

PARA TESTAR
1. Escolha 5.
2. O script roda testes, gera EXE e instalador.
3. Pegue somente os arquivos de ENTREGA_PARA_TESTE.
4. Isso nao altera main, tag ou Release.

DEPOIS DA APROVACAO EXPLICITA
1. Confirme que a branch dev esta limpa e enviada.
2. Escolha 15.
3. Confira a versao e digite exatamente PUBLICAR.
4. O fluxo testa, cria backup da main antiga, atualiza main e publica a Release.

OPCOES INDIVIDUAIS
01 executar em desenvolvimento; 02 testes; 03 EXE; 04 instalador;
05 pacote para teste; 06 branch dev; 07 status; 08 backup da main;
09 atualizar main aprovada; 10 tag/Release; 11 entrega; 12 logs;
14 ambiente; TUDO_EM_UM somente depois da aprovacao.

SEGURANCA
- Nenhum BAT guarda token ou senha.
- Os scripts param quando testes ou comandos importantes falham.
- Backups remotos nunca sao apagados ou sobrescritos silenciosamente.
- O PC do usuario final nao precisa de Python, Git, gh ou Inno Setup.
- SQLite e dados reais continuam no AppData.

Leia TUTORIAL_CONFIGURACAO_COMPLETA.txt na raiz para a configuracao inicial,
publicacao, restauracao e solucao de problemas.

