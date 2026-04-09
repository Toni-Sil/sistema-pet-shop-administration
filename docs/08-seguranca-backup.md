# 08 - Segurança e Backup

**Status:** Crítico | **Prioridade:** Alta | **Implementação:** Sprint 1

---

## Objetivo

Garantir proteção dos dados, backups criptografados e transferências seguras sem comprometer a performance do sistema.

---

## Níveis de Segurança

### 1. Criptografia de Backups (OBRIGATÓRIO)

**Impacto:** Zero no sistema em produção (executado fora do horário comercial)

#### Backup Automático com GPG

```bash
#!/bin/bash
# /opt/scripts/backup_petshop.sh
set -euo pipefail

# Configuração
DB_NAME="petshop_db"
BACKUP_DIR="/backup/encrypted"
RETENTION_DAYS=7
ADMIN_EMAIL="admin@petshop.com"

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.dump.gpg"
CHECKSUM_FILE="${BACKUP_FILE}.sha256"

# Criar diretório
mkdir -p "$BACKUP_DIR"

echo "🔒 Iniciando backup criptografado..."

# 1. Backup criptografado
pg_dump -Fc "$DB_NAME" | \
  gpg --encrypt --recipient "$ADMIN_EMAIL" > "$BACKUP_FILE"

# 2. Gerar checksum para verificar integridade
sha256sum "$BACKUP_FILE" > "$CHECKSUM_FILE"

# 3. Verificar arquivo criado
if gpg --list-packets "$BACKUP_FILE" > /dev/null 2>&1; then
  echo "✅ Backup criado: $BACKUP_FILE"
else
  echo "❌ ERRO: Falha no backup"
  exit 1
fi

# 4. Limpar backups antigos (manter 7 dias)
find "$BACKUP_DIR" -name "*.dump.gpg" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.sha256" -mtime +$RETENTION_DAYS -delete

# 5. (Opcional) Upload para cloud
# aws s3 cp "$BACKUP_FILE" s3://bucket-backup-petshop/
# gsutil cp "$BACKUP_FILE" gs://bucket-backup-petshop/

echo "✅ Backup completo!"
```

#### Agendar Backup Diário

```bash
# Adicionar ao crontab
sudo crontab -e

# Executar todos os dias às 2h da manhã
0 2 * * * /opt/scripts/backup_petshop.sh
```

---

### 2. Restauração Segura

```bash
#!/bin/bash
# /opt/scripts/restore_petshop.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
  echo "Uso: ./restore_petshop.sh backup_20260409.dump.gpg"
  exit 1
fi

echo "🔍 Verificando integridade..."
sha256sum -c "${BACKUP_FILE}.sha256"

if [ $? -ne 0 ]; then
  echo "❌ Arquivo corrompido!"
  exit 1
fi

echo "🔓 Descriptografando e restaurando..."
gpg --decrypt "$BACKUP_FILE" | pg_restore -d petshop_db

echo "✅ Restauração concluída!"
```

---

### 3. SSL/TLS no PostgreSQL (OBRIGATÓRIO)

**Impacto:** < 2% overhead - Negligenciável

#### Configuração do PostgreSQL

```conf
# postgresql.conf
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
ssl_ca_file = '/etc/ssl/certs/ca.crt'

# Forçar SSL apenas
ssl_min_protocol_version = 'TLSv1.2'
```

#### Gerar Certificados SSL

```bash
# Certificado auto-assinado (desenvolvimento)
openssl req -new -x509 -days 365 -nodes \
  -out /etc/ssl/certs/server.crt \
  -keyout /etc/ssl/private/server.key \
  -subj "/C=BR/ST=SP/L=Sao Paulo/O=PetShop/CN=petshop.local"

# Permissões
chmod 600 /etc/ssl/private/server.key
chown postgres:postgres /etc/ssl/private/server.key
```

#### Conectar com SSL

```python
# SQLAlchemy
DATABASE_URL = "postgresql://user:pass@host/db?sslmode=require"

# psycopg2
conn = psycopg2.connect(
    host="localhost",
    database="petshop_db",
    user="postgres",
    password="senha",
    sslmode="require"
)
```

---

### 4. Criptografia de Disco (RECOMENDADO)

**Impacto:** 5-10% I/O overhead - Aceitável

#### LUKS (Linux)

```bash
# Configurar partição criptografada para backups
sudo cryptsetup luksFormat /dev/sdb1
sudo cryptsetup open /dev/sdb1 backup_encrypted
sudo mkfs.ext4 /dev/mapper/backup_encrypted
sudo mount /dev/mapper/backup_encrypted /backup
```

---

## Transferência Segura Entre Servidores

### SCP (SSH File Transfer)

```bash
# Transferir backup criptografado
scp -P 22 backup.dump.gpg usuario@servidor-destino:/backup/

# Com compressão
scp -C backup.dump.gpg usuario@servidor:/backup/
```

### RSYNC (Sincronização)

```bash
# Sincronizar backups para servidor remoto
rsync -avz -e ssh /backup/encrypted/ \
  usuario@servidor:/backup/remote/
```

---

## Configuração GPG (Setup Inicial)

### Gerar Par de Chaves

```bash
# 1. Gerar chave GPG
gpg --full-generate-key

# Escolher:
# - Tipo: RSA and RSA
# - Tamanho: 4096 bits
# - Validade: 0 (não expira)
# - Nome: Admin PetShop
# - Email: admin@petshop.com

# 2. Listar chaves
gpg --list-keys

# 3. Exportar chave pública (para backup em outro servidor)
gpg --export -a "admin@petshop.com" > public.key

# 4. Importar chave em outro servidor
gpg --import public.key
```

---

## Docker Compose com Backup

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: petshop_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - /etc/ssl/certs:/etc/ssl/certs:ro
    command: >
      postgres
      -c ssl=on
      -c ssl_cert_file=/etc/ssl/certs/server.crt
      -c ssl_key_file=/etc/ssl/certs/server.key

  backup:
    image: postgres:15-alpine
    depends_on:
      - db
    volumes:
      - ./backups:/backup
      - ./scripts:/scripts
    environment:
      PGPASSWORD: ${DB_PASSWORD}
      GPG_EMAIL: ${ADMIN_EMAIL}
    entrypoint: /bin/sh
    command: -c "crond -f -l 2"
    # Adicionar crontab no Dockerfile:
    # RUN echo '0 2 * * * /scripts/backup_petshop.sh' > /etc/crontabs/root

volumes:
  postgres_data:
```

---

## Verificação de Integridade

```bash
# Sempre verificar antes de restaurar
sha256sum backup.dump.gpg
sha256sum -c backup.dump.gpg.sha256

# Testar backup (sem restaurar)
gpg --decrypt backup.dump.gpg | pg_restore --list
```

---

## Boas Práticas

### ✅ SEMPRE

- Criptografar backups com GPG (AES-256)
- Usar SSL/TLS em conexões de banco
- Armazenar backups em local separado do servidor
- Testar restauração mensalmente
- Manter múltiplas versões de backup (7-30 dias)
- Verificar integridade com SHA256
- Executar backups fora do horário comercial
- Guardar chaves GPG em local seguro (2 locais)
- Limitar acesso ao PostgreSQL por IP
- Usar senhas fortes e gerenciador de senhas

### ❌ NUNCA

- Transferir backups sem criptografia
- Armazenar backups apenas localmente
- Versionar senhas no Git
- Usar senhas fracas para GPG
- Compartilhar backups por email não criptografado
- Deixar backups em diretórios públicos
- Executar backup durante horário de pico
- Ignorar testes de restauração

---

## Política de Retenção

| Tipo | Período | Local |
|------|---------|-------|
| **Backup Diário** | 7 dias | Servidor local criptografado |
| **Backup Semanal** | 30 dias | Cloud storage (S3/GCS) |
| **Backup Mensal** | 12 meses | Cloud storage (archive) |

---

## Monitoramento de Backup

```bash
#!/bin/bash
# /opt/scripts/check_backup.sh

BACKUP_DIR="/backup/encrypted"
LAST_BACKUP=$(find "$BACKUP_DIR" -name "*.dump.gpg" -mtime -1 | head -1)

if [ -z "$LAST_BACKUP" ]; then
  echo "⚠️ ALERTA: Nenhum backup nas últimas 24h"
  # Enviar email/notificação
  exit 1
else
  echo "✅ Backup OK: $LAST_BACKUP"
fi
```

---

## Compliance LGPD

### Dados Pessoais no Sistema

- **Nome do cliente/pet:** Armazenado em texto puro
- **Telefone/Email:** Armazenado em texto puro
- **CPF:** Não obrigatório (opcional criptografar com pgcrypto se necessário)

### Anonimização para Desenvolvimento

```sql
-- Script para anonimizar dados de produção para dev
UPDATE clientes SET
  nome = 'Cliente ' || id,
  telefone = '11999999' || LPAD(id::text, 3, '0'),
  email = 'cliente' || id || '@example.com';

UPDATE pets SET
  nome = 'Pet ' || id;
```

---

## Testes de Segurança

```bash
# Teste 1: Verificar SSL ativo
psql "postgresql://user@host/db?sslmode=require" -c "SHOW ssl;"

# Teste 2: Tentar conexão sem SSL (deve falhar)
psql "postgresql://user@host/db?sslmode=disable" -c "SELECT 1;"

# Teste 3: Restaurar backup de teste
./restore_petshop.sh test_backup.dump.gpg
```

---

## Impacto de Performance

| Recurso | Overhead | Quando Ocorre | Impacto Usuário |
|---------|----------|---------------|-----------------|
| Backup GPG | 0% | Madrugada (2h) | Zero |
| SSL/TLS | 1-3% | Todas as queries | Imperceptível |
| Criptografia disco | 5-10% | I/O operações | Baixo |
| pgcrypto campo | 10-30% | Campos específicos | Evitar uso excessivo |

**Recomendação:** Implementar Backup GPG + SSL/TLS sem preocupação com performance.

---

## Recuperação de Desastres

### Cenário 1: Servidor Comprometido

```bash
# 1. Provisionar novo servidor
# 2. Instalar PostgreSQL + dependências
# 3. Restaurar último backup
gpg --decrypt backup_latest.dump.gpg | pg_restore -d petshop_db
# 4. Verificar integridade dos dados
# 5. Atualizar DNS/IP
```

### Cenário 2: Backup Corrompido

```bash
# Tentar backup anterior
for backup in $(ls -t backups/*.gpg); do
  echo "Tentando: $backup"
  gpg --decrypt "$backup" | pg_restore -d test_db && break
done
```

---

## Checklist de Implementação

- [ ] Instalar GPG no servidor
- [ ] Gerar par de chaves GPG
- [ ] Exportar chave pública (guardar em 2 locais)
- [ ] Criar script de backup criptografado
- [ ] Agendar cron para backup diário (2h)
- [ ] Configurar SSL no PostgreSQL
- [ ] Gerar certificados SSL
- [ ] Testar conexão com SSL
- [ ] Configurar retenção de backups (7 dias)
- [ ] (Opcional) Configurar upload para cloud
- [ ] Testar restauração de backup
- [ ] Documentar processo para equipe
- [ ] Definir responsável por monitoramento

---

## Referências

- Documentação PostgreSQL SSL: https://postgresql.org/docs/current/ssl-tcp.html
- GPG Manual: https://gnupg.org/documentation/
- pgBackRest: https://pgbackrest.org/
- LGPD: https://www.gov.br/lgpd
