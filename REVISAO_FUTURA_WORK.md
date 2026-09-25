# REGISTRO PARA REVISÃO FUTURA NO WORK — Radar de Lotes

Base usada: v1.4.3.
Versão de desenvolvimento criada neste chat: v1.5.0.
Branch: dev-v1.5.0.

## Objetivo deste arquivo
Quando houver tokens disponíveis no Work, usar este registro para auditar a implementação real, testar em Windows e corrigir qualquer ponto incompleto. Não reconstruir o projeto do zero.

## Alterações implementadas
1. Busca com filtros escolhidos na hora:
   - cidade;
   - múltiplos bairros livres;
   - preço mínimo/máximo;
   - área mínima/máxima;
   - dimensões;
   - topografia;
   - murado.
   - O perfil rígido antigo deixou de comandar a classificação e a aba Novos.
   - Filtros usados ficam salvos para buscas agendadas; sem filtros salvos, a busca agendada não inventa critérios.

2. Dados dos anúncios:
   - parsing ampliado para dimensões, topografia, murado, CAB e CAM explícitos, contatos, preço e área;
   - bairros podem vir dos filtros, não apenas da lista antiga;
   - CAB/CAM não são inferidos quando ausentes;
   - deduplicação continua exigindo evidências fortes;
   - anti-bot/login/CAPTCHA continuam sem bypass.

3. Google Maps:
   - normalização de endereço, bairro, cidade e MG;
   - remoção de duplicações;
   - diferencia localização completa de aproximada;
   - botão mostra APROX. quando não há endereço completo.

4. Atualizador:
   - botão fixo ATUALIZAÇÕES removido;
   - verificação em background a cada janela segura;
   - aviso pequeno e clicável apenas se houver versão nova;
   - SHA-256 mantido;
   - updater público, sem PAT/token;
   - helper espera PID antigo encerrar antes de iniciar o Setup;
   - usa /NORESTARTAPPLICATIONS e RestartApplications=no;
   - apenas uma abertura do app após o Setup.

5. Windows App Control / Error 4551:
   - mantido instalador único legado para compatibilidade com atualizadores antigos;
   - criado segundo pacote ZIP compatível usando Inno Setup UseSetupLdr=no;
   - esse modo gera Setup.exe + Setup-*.bin e evita o SetupLdr executado da pasta TEMP;
   - updater v1.5.0 prefere o pacote compatível quando ele existe;
   - nenhuma política de segurança é desativada ou burlada.
   - IMPORTANTE PARA REVISÃO: testar fisicamente no PC que apresentou Error 4551.

6. Build e GitHub Actions:
   - build_windows.bat não roda pytest novamente;
   - GitHub Actions mantém job de testes antes do build;
   - cache de pip adicionado;
   - Release passa a carregar EXE legado, ZIP de compatibilidade e SHA256SUMS.txt.

7. Ferramentas locais:
   - AUTOMACOES/ adicionada ao .gitignore;
   - template e instalador do RADAR.bat ficam em FERRAMENTAS_DESENVOLVIMENTO;
   - após instalar localmente, trocar branch não substitui o BAT;
   - Inno detectado também em %LOCALAPPDATA%;
   - opção 15 pede PUBLICAR uma vez e evita repetir testes/EXE/instalador;
   - backup remoto é idempotente;
   - sem force push;
   - pytest local usa --basetemp exclusivo para reduzir o PermissionError de cleanup.

8. Line endings:
   - .gitattributes define CRLF para BAT/CMD/PS1 e LF para Python/YAML/Markdown.

## Pontos que o Work deve auditar depois
- Rodar suíte completa de testes e revisar testes de regressão.
- Testar o ZIP UseSetupLdr=no no PC do pai que bloqueou o Setup temporário.
- Testar atualização real v1.5.0 -> versão seguinte usando o pacote compatível.
- Confirmar se todos os portais ainda expõem JSON-LD suficiente; melhorar apenas por meios públicos permitidos.
- Revisar UX dos filtros em diferentes resoluções.
- Auditar a geração do pacote ZIP e SHA no GitHub Actions.
- Revisar o BAT em CMD real e os caminhos com espaços.
- Revisar assinatura digital futuramente, caso exista certificado legítimo; não contornar Windows App Control.
- Auditar identidade visual/ícone quando incorporado ao build.
