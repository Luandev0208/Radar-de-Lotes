# Radar de Lotes — V1.4

Programa local para Windows que organiza lotes novos, interessantes e descartados. Os dados ficam em SQLite no próprio computador.

O repositório está separado em `PROJETO` (código, testes e empacotamento) e `AUTOMACOES` (menu e BAT). Para administrar o projeto no Windows, abra `AUTOMACOES\RADAR.bat`. O tutorial completo está em `TUTORIAL_CONFIGURACAO_COMPLETA.txt` na raiz.

Os cards permitem abrir o anúncio, pesquisar a localização no Google Maps, consultar contatos disponíveis e ver detalhes e histórico de preço. Dados ausentes não são inventados.

Anúncios duplicados são mesclados sem apagar dados já encontrados. Todas as fontes e URLs conhecidas do mesmo terreno ficam disponíveis na tela de detalhes.

Na aba **Novos**, terrenos claramente incompatíveis ficam ocultos para não poluir a tela principal. Um lote só recebe **Muito interessante** quando bairro prioritário, preço dentro do limite e área entre 350 e 380 m² estão confirmados. Dados ausentes recebem **Pode ser interessante — precisa confirmar**.

## Atualizações privadas

O Radar consulta a Release mais recente do repositório privado `Luandev0208/Radar-de-Lotes` no máximo uma vez por dia. Em **ATUALIZAÇÕES**, configure uma única vez um fine-grained personal access token limitado somente a este repositório, com a permissão **Contents: Read-only**. Não conceda permissões administrativas.

O token fica no **Gerenciador de Credenciais do Windows**, sob o identificador `RadarDeLotes.GitHubReadToken`. Ele não é salvo no SQLite, em arquivo, em log ou dentro do executável e não volta a ser exibido. O instalador só é executado depois de seu SHA-256 ser comparado com `SHA256SUMS.txt` da mesma Release.

O banco continua em `%LOCALAPPDATA%\Radar de Lotes\radar.db`, fora da pasta do programa. Antes de uma migração é criado um backup `pre-migration-*.db`; as alterações de esquema são registradas em `schema_migrations`.

## Testar no computador de desenvolvimento

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -q
python main.py
```

## Gerar o executável

No Windows, com Python 3.12 e Inno Setup 6 instalados, execute `build_windows.bat`. Ele limpa os artefatos antigos, roda os testes, gera um executável único, executa o autoteste do EXE e compila um instalador novo em:

`installer_output\Instalar Radar de Lotes.exe`

Python é necessário apenas para desenvolvimento. Depois da instalação, o atalho, a busca manual, as notificações e as tarefas agendadas executam diretamente `Radar de Lotes.exe`; não chamam `py`, `python`, arquivos `.py` ou `.venv`.

## Publicar uma nova versão

1. Atualize e teste o código mantendo o repositório privado.
2. Abra `AUTOMACOES\RADAR.bat` e crie uma branch `dev-vX.Y.Z` pela opção 6.
3. Gere o instalador de teste pela opção 5; isso não altera `main`.
4. Somente depois da aprovação explícita, use a opção 15 e digite `PUBLICAR`.
5. O fluxo cria o backup da `main` antiga, testa, compila, publica `main`, tag, SHA-256 e Release privada.

`VERSION` é a fonte central de versão. O build gera o arquivo temporário usado pelo Inno Setup.

O instalador cria buscas às 08:00, 14:00 e 20:00 com recuperação automática se o computador estiver desligado. Ao desinstalar, essas três tarefas são removidas. Ao abrir o programa, uma busca atrasada também é executada, sem iniciar duas buscas ao mesmo tempo.

## Dados e backups

O banco, os logs e os backups ficam no AppData do usuário e não são apagados quando o programa é atualizado.

## Limitação importante da busca automática

Portais imobiliários alteram páginas e podem bloquear automação. A V1.2 consulta resultados públicos indexados e conectores separados para OLX, Viva Real, Imovelweb, Chaves na Mão e ZAP Imóveis, com páginas/consultas específicas para Nacional, Xangri-lá, Parque Xangri-lá, Vale das Amendoeiras, Bom Jesus e Arvoredo. Se uma fonte bloquear ou mudar a página, isso é registrado e as outras continuam. Nenhuma proteção, login, CAPTCHA ou telefone oculto é contornado.

## Próxima manutenção de fontes

Cada fonte deve ser adicionada em `radar_lotes/connectors.py`. Não contorne CAPTCHA, login ou bloqueios. Prefira páginas públicas com dados Schema.org/JSON-LD.

## Validação no Windows

Depois de gerar o instalador:

1. Instale e abra o Radar.
2. Confirme no Agendador de Tarefas as tarefas `Radar de Lotes 08h`, `14h` e `20h`.
3. Execute `BUSCAR AGORA` e confira o arquivo de log no AppData.
4. Desinstale pelo Windows e confirme que as três tarefas desapareceram.
5. Em máquina sem Python e VS Code, confirme o atalho, **Buscar agora** e `Radar de Lotes.exe --scheduled`.
6. Configure a credencial de leitura e confirme que uma atualização preserva lotes, status e histórico.
