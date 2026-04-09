# Diretrizes de Desenvolvimento para IA (Skills SDD)

Este documento serve como guia para que modelos de IA possam desenvolver o sistema mantendo a consistência e a qualidade técnica esperada.

## Princípios SDD (Spec-Driven Development)
1. **Documentação Antes do Código:** Sempre verifique e atualize os arquivos na pasta `docs/` antes de realizar mudanças estruturais.
2. **Modularidade:** Desenvolva funcionalidades como módulos independentes. O core do sistema deve ser leve e expansível.
3. **Contrato de API (Schemas):** Defina os schemas Pydantic antes de implementar as rotas no FastAPI.

## Padrões de Código
- **Backend:**
  - Seguir o padrão de repositório para acesso a dados.
  - Utilizar Type Hints em todas as funções.
  - Implementar tratamento de exceções global.
- **Segurança:**
  - Sempre considerar RLS (Row Level Security).
  - Validar inputs rigorosamente para evitar injeções.
  - Não expor credenciais em logs ou respostas da API.

## Funcionalidades Chave para IA
- **Registro de Produtos:** Considerar sempre o campo `barcode` para integração com leitores.
- **Financeiro:** Garantir transacionalidade em todas as operações que envolvam saldo ou caixa.
- **Logs:** Manter trilha de auditoria para ações críticas (ex: exclusão de registros).
