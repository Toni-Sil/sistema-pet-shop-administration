#!/bin/bash
# Script de configuração do banco de dados para desenvolvimento local
# Execute com: sudo bash setup_db.sh  (precisa de senha sudo)

echo "🐘 Configurando banco de dados PostgreSQL..."

# Cria usuário e banco via postgres do sistema
su postgres -c "psql" <<'EOF'
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'admin') THEN
    CREATE USER admin WITH SUPERUSER PASSWORD 'admin123';
    RAISE NOTICE 'Usuário admin criado.';
  ELSE
    RAISE NOTICE 'Usuário admin já existe.';
  END IF;
END
$$;

SELECT 'CREATE DATABASE petshop_db OWNER admin'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'petshop_db')\gexec

GRANT ALL PRIVILEGES ON DATABASE petshop_db TO admin;
\c petshop_db
GRANT ALL ON SCHEMA public TO admin;
ALTER SCHEMA public OWNER TO admin;
\q
EOF

echo ""
echo "✅ Banco configurado!"
echo ""
echo "▶ Próximos passos:"
echo ""
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  alembic upgrade head    # Cria as tabelas"
echo "  python seed.py          # Popula com dados demo"
echo "  uvicorn app.main:app --reload --port 8000"
echo ""
echo "  # Em outro terminal:"
echo "  cd frontend && npm run dev"
echo ""
echo "  🌐 Frontend: http://localhost:8080"
echo "  🔌 Backend:  http://localhost:8000/docs"
echo "  👤 Login: admin@demo.com / admin123"
