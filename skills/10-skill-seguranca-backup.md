# Skill: Segurança e Backup

## Objetivo

Implementar práticas de segurança e backup criptografado no sistema pet shop, garantindo proteção de dados sem comprometer a performance.

---

## Quando Usar Esta Skill

- Criar scripts de backup automatizado
- Configurar SSL/TLS no PostgreSQL  
- Implementar criptografia de dados
- Setup de restauração de desastres
- Configurar monitoramento de backups

---

## Princípios de Implementação

### 1. **Backup SEMPRE Fora do Horário Comercial**

```python
# ❌ ERRADO: Backup durante horário de uso
# backup_task.schedule(hour=14)  # 14h = pet shop aberto

# ✅ CORRETO: Backup na madrugada
# backup_task.schedule(hour=2)   # 2h = pet shop fechado
```

###2. **Criptografia em Camadas**

| Camada | O Que Protege | Implementar |
|--------|---------------|-------------|
| **Transporte** | Dados em trânsito | SSL/TLS |
| **Backup** | Arquivos de backup | GPG |
| **Disco** | Storage físico | LUKS (opcional) |

### 3. **Nunca Armazenar Senhas em Código**

```python
# ❌ ERRADO
DB_PASSWORD = "senha123"

# ✅ CORRETO
import os
DB_PASSWORD = os.getenv("DB_PASSWORD")
```

---

## Scripts de Implementação

### Backup Criptografado com GPG

```python
# scripts/backup.py
import subprocess
import os
from datetime import datetime

def backup_database():
    \"\"\"Backup criptografado do PostgreSQL\"\"\"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_name = os.getenv("DB_NAME", "petshop_db")
    backup_dir = "/backup/encrypted"
    backup_file = f"{backup_dir}/{db_name}_{timestamp}.dump.gpg"
    
    # 1. Criar backup criptografado
    dump_cmd = f"pg_dump -Fc {db_name}"
    encrypt_cmd = f"gpg --encrypt --recipient admin@petshop.com"
    
    subprocess.run(
        f"{dump_cmd} | {encrypt_cmd} > {backup_file}",
        shell=True,
        check=True
    )
    
    # 2. Gerar checksum
    subprocess.run(
        f"sha256sum {backup_file} > {backup_file}.sha256",
        shell=True,
        check=True
    )
    
    # 3. Limpar backups antigos (7 dias)
    subprocess.run(
        f"find {backup_dir} -name '*.gpg' -mtime +7 -delete",
        shell=True
    )
    
    print(f"✅ Backup criado: {backup_file}")
```

### Restauração Segura

```python
# scripts/restore.py
import subprocess
import sys

def restore_database(backup_file: str):
    \"\"\"Restaurar backup criptografado\"\"\"
    
    # 1. Verificar integridade
    result = subprocess.run(
        f"sha256sum -c {backup_file}.sha256",
        shell=True,
        capture_output=True
    )
    
    if result.returncode != 0:
        print("❌ Arquivo corrompido!")
        sys.exit(1)
    
    # 2. Descriptografar e restaurar
    decrypt_cmd = f"gpg --decrypt {backup_file}"
    restore_cmd = "pg_restore -d petshop_db"
    
    subprocess.run(
        f"{decrypt_cmd} | {restore_cmd}",
        shell=True,
        check=True
    )
    
    print("✅ Restauração concluída!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python restore.py backup.dump.gpg")
        sys.exit(1)
    
    restore_database(sys.argv[1])
```

---

## Configuração SSL/TLS no PostgreSQL

### Arquivo de Configuração

```python
# config/database.py
from sqlalchemy import create_engine
import os

def get_database_url():
    \"\"\"URL de conexão com SSL\"\"\"
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME", "petshop_db")
    
    # SSL obrigatório em produção
    sslmode = "require" if os.getenv("ENV") == "production" else "prefer"
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}?sslmode={sslmode}"

engine = create_engine(get_database_url())
```

### Verificação de SSL

```python
# tests/test_security.py
import psycopg2
import os

def test_ssl_connection():
    \"\"\"Testar se SSL está ativo\"\"\"
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode="require"
    )
    
    cursor = conn.cursor()
    cursor.execute("SHOW ssl;")
    ssl_status = cursor.fetchone()[0]
    
    assert ssl_status == "on", "SSL não está ativo!"
    print("✅ SSL ativo")
    
    cursor.close()
    conn.close()
```

---

## Monitoramento de Backups

### Script de Verificação

```python
# scripts/check_backup.py
from pathlib import Path
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage

def check_recent_backup():
    \"\"\"Verificar se houve backup nas últimas 24h\"\"\"
    backup_dir = Path("/backup/encrypted")
    yesterday = datetime.now() - timedelta(days=1)
    
    recent_backups = [
        f for f in backup_dir.glob("*.dump.gpg")
        if datetime.fromtimestamp(f.stat().st_mtime) > yesterday
    ]
    
    if not recent_backups:
        send_alert("⚠️ Nenhum backup nas últimas 24h!")
        return False
    
    print(f"✅ Backup OK: {recent_backups[0].name}")
    return True

def send_alert(message: str):
    \"\"\"Enviar alerta por email\"\"\"
    msg = EmailMessage()
    msg['Subject'] = 'Alerta de Backup - Pet Shop'
    msg['From'] = 'backup@petshop.com'
    msg['To'] = 'admin@petshop.com'
    msg.set_content(message)
    
    # Configurar SMTP
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT", 587)
    
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.send_message(msg)
```

---

## Tarefas Agendadas (Celery)

```python
# tasks/backup_tasks.py
from celery import Celery
from celery.schedules import crontab
from scripts.backup import backup_database
from scripts.check_backup import check_recent_backup

app = Celery('petshop_tasks')

@app.task
def daily_backup():
    \"\"\"Backup diário às 2h da manhã\"\"\"
    backup_database()

@app.task
def check_backup_status():
    \"\"\"Verificar status do backup a cada 6h\"\"\"
    check_recent_backup()

# Configuração de agenda
app.conf.beat_schedule = {
    'backup-diario': {
        'task': 'tasks.backup_tasks.daily_backup',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM
    },
    'verificar-backup': {
        'task': 'tasks.backup_tasks.check_backup_status',
        'schedule': crontab(hour='*/6'),  # A cada 6h
    },
}
```

---

## Docker Compose com Segurança

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./ssl:/etc/ssl/certs:ro
    command: >
      postgres
      -c ssl=on
      -c ssl_cert_file=/etc/ssl/certs/server.crt
      -c ssl_key_file=/etc/ssl/certs/server.key
    networks:
      - petshop_network

  api:
    build: .
    environment:
      DB_HOST: db
      DB_NAME: ${DB_NAME}
      DB_USER: ${DB_USER}
      DB_PASSWORD: ${DB_PASSWORD}
      ENV: production
    depends_on:
      - db
    networks:
      - petshop_network

  backup:
    image: postgres:15-alpine
    volumes:
      - ./backups:/backup
      - ./scripts:/scripts
      - ./gpg:/root/.gnupg:ro
    environment:
      PGPASSWORD: ${DB_PASSWORD}
      DB_NAME: ${DB_NAME}
    entrypoint: /bin/sh
    command: -c "crond -f"
    networks:
      - petshop_network

volumes:
  postgres_data:

networks:
  petshop_network:
    driver: bridge
```

---

## Variáveis de Ambiente

```bash
# .env.example
# Database
DB_NAME=petshop_db
DB_USER=postgres
DB_PASSWORD=sua_senha_forte_aqui
DB_HOST=localhost
DB_PORT=5432

# Ambiente
ENV=production

# Backup
BACKUP_RETENTION_DAYS=7
GPG_EMAIL=admin@petshop.com

# Alertas
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
ADMIN_EMAIL=admin@petshop.com
```

---

## Checklist de Segurança

### Setup Inicial

```python
# scripts/security_setup.py
import subprocess
import os

def setup_security():
    \"\"\"Configuração inicial de segurança\"\"\"
    
    tasks = [
        ("Instalando GPG", "apt-get install -y gnupg"),
        ("Gerando chave GPG", "gpg --batch --gen-key gpg_config"),
        ("Criando diretório de backup", "mkdir -p /backup/encrypted"),
        ("Gerando certificado SSL", "./scripts/generate_ssl.sh"),
    ]
    
    for description, command in tasks:
        print(f"📋 {description}...")
        result = subprocess.run(command, shell=True, capture_output=True)
        
        if result.returncode == 0:
            print(f"  ✅ {description} - OK")
        else:
            print(f"  ❌ {description} - FALHOU")
            print(f"     Erro: {result.stderr.decode()}")

if __name__ == "__main__":
    setup_security()
```

---

## Testes de Segurança

```python
# tests/test_backup.py
import pytest
from scripts.backup import backup_database
from scripts.restore import restore_database
import subprocess

def test_backup_encryption():
    \"\"\"Testar se backup é criptografado\"\"\"
    backup_database()
    
    # Verificar se arquivo é GPG
    result = subprocess.run(
        "file /backup/encrypted/*.gpg | grep 'GPG'",
        shell=True,
        capture_output=True
    )
    
    assert result.returncode == 0, "Backup não está criptografado!"

def test_backup_integrity():
    \"\"\"Testar integridade do backup\"\"\"
    backup_file = "/backup/encrypted/test.dump.gpg"
    
    # Verificar checksum
    result = subprocess.run(
        f"sha256sum -c {backup_file}.sha256",
        shell=True,
        capture_output=True
    )
    
    assert result.returncode == 0, "Checksum inválido!"

def test_restore():
    \"\"\"Testar restauração de backup\"\"\"
    # Criar backup de teste
    backup_database()
    
    # Restaurar em banco de teste
    latest_backup = subprocess.check_output(
        "ls -t /backup/encrypted/*.gpg | head -1",
        shell=True
    ).decode().strip()
    
    # Deve restaurar sem erros
    restore_database(latest_backup)
```

---

## Boas Práticas

### ✅ SEMPRE

1. **Criptografar backups** com GPG antes de armazenar
2. **Usar SSL/TLS** em todas as conexões de banco
3. **Verificar integridade** com SHA256 antes de restaurar
4. **Testar restauração** mensalmente
5. **Logs de auditoria** para acesso a backups
6. **Variáveis de ambiente** para senhas
7. **Retenção definida** (7 dias local, 30 dias cloud)

### ❌ NUNCA

1. Armazenar senhas em código ou versionamento
2. Fazer backup sem criptografia
3. Executar backup durante horário de uso
4. Ignorar falhas de backup
5. Usar mesma senha em dev e produção

---

## Referências de Implementação

- Consultar: `docs/08-seguranca-backup.md`
- PostgreSQL SSL: https://postgresql.org/docs/current/ssl-tcp.html
- GPG Python: https://gnupg.readthedocs.io/
- Celery Beat: https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html
