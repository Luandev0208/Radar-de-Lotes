# Radar de Lotes 1.4.1

- Identificação visual clara da versão 1.4.1 e confirmação após atualização.
- GitHub Actions passa a ser o único responsável pela tag e Release final.
- BAT local acompanha o workflow sem tentar publicar uma Release concorrente.
- Instalador baixado é validado por SHA-256 e removido após a atualização.
- Limpeza restrita à pasta temporária controlada pelo Radar, sem tocar em Downloads ou Desktop.
- SQLite, lotes, status, histórico, configurações, backups, credencial e tarefas são preservados.
