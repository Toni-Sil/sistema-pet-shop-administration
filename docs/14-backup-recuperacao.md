# 14 - Backup e Recuperação de Dados

## Objetivo

Garantir que nenhum pet shop perca dados em caso de falha no VPS, erro humano ou desastre de infraestrutura, com processo de recuperação claro e testado.

---

## 1. Estratégia de backup

### 1.1 Frequência

| Tipo | Frequência | Retenção |
|---|---|---|
| Backup completo do banco (pg_dump) | Diário (02h da manhã) | 30 dias |
| Backup incremental (WAL Archiving) | Contínuo | 7 dias |
| Backup de arquivos (uploads, XMLs fiscais) | Diário | 90 dias |
| Snapshot do VPS | Semanal | 4 semanas |

### 1.2 Destino dos backups

- **Primário:** bucket de objeto externo ao VPS (ex.: Backblaze B2, AWS S3, MinIO remoto).
- **Secundário:** backup local no VPS (para restauração rápida).
- XMLs fiscais: armazenados separadamente por no mínimo **5 anos** (obrigação legal).

### 1.3 Criptografia

- Backups criptografados em repouso (AES-256) antes de enviar ao bucket.
- Chave de criptografia armazenada em secret manager, separada do backup.

---

## 2. Processo de restauração

### 2.1 Restauração completa (pane total no VPS)

```bash
# 1. Subir novo VPS com Docker instalado
# 2. Baixar último backup completo do bucket
# 3. Restaurar banco de dados
pg_restore -U postgres -d petshop_db backup_YYYY-MM-DD.dump

# 4. Restaurar arquivos (uploads, XMLs)
# 5. Subir containers via docker-compose
docker compose up -d

# 6. Verificar integridade dos dados
```

**RTO estimado (Recovery Time Objective):** até 2 horas.
**RPO estimado (Recovery Point Objective):** até 24 horas (perda máxima de 1 dia de dados em caso extremo).

### 2.2 Restauração pontual (erro humano)

- Possível restaurar banco para qualquer ponto nas últimas 7 dias via WAL.
- Admin pode solicitar restauração pontual via painel de suporte.

---

## 3. Testes de backup

- Backup deve ser **testado mensalmente**: restaurar em ambiente de homologação e validar integridade.
- Checklist de teste:
  - [ ] Banco restaurado com sucesso.
  - [ ] Dados de vendas, clientes e pets intactos.
  - [ ] XMLs fiscais acessíveis.
  - [ ] Sistema funcional após restauração.

---

## 4. Notificações

- Se backup falhar: notificar administrador do sistema via e-mail/WhatsApp imediatamente.
- Relatório semanal de status de backup enviado ao desenvolvedor.

---

## 5. Responsabilidades

| Responsável | Tarefa |
|---|---|
| Sistema (automático) | Executar backup diário e enviar ao bucket |
| Desenvolvedor | Monitorar falhas e testar restore mensalmente |
| Dono da loja | Não precisa fazer nada; pode solicitar restore via suporte |
