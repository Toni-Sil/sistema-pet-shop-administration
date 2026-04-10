# 19 - LGPD: Exclusão e Portabilidade de Dados

## Objetivo

Atender aos direitos dos titulares de dados previstos na LGPD (Lei 13.709/2018): direito ao esquecimento, portabilidade e transparência sobre o uso de dados.

---

## 1. Dados pessoais armazenados

| Entidade | Dados pessoais |
|---|---|
| Clientes (tutores) | Nome, telefone, e-mail, endereço |
| Pets | Nome, foto, dados de saúde |
| Usuários (funcionários) | Nome, e-mail, senha (hash) |
| Logs de segurança | IP aproximado, dispositivo |

---

## 2. Direito ao esquecimento (exclusão)

### Fluxo de solicitação

1. Cliente (tutor) solicita exclusão de seus dados ao dono da loja.
2. Dono da loja acessa painel → Clientes → [cliente] → "Excluir dados pessoais".
3. Sistema executa **anonimização** (não exclusão física imediata), preservando integridade referencial:
   - Nome → "Cliente Removido"
   - Telefone, e-mail, endereço → NULL
   - Pets: mantidos anonimizados (histórico clínico pode ter valor para a loja)
4. Registro de exclusão em log de auditoria (quem solicitou, quando, quais dados).
5. Após 90 dias: exclusão física dos registros anonimizados.

### Restrições

- Dados fiscais (notas emitidas) **não podem ser excluídos** antes do prazo legal (5 anos).
- Dados que constituem obrigação legal têm precedência sobre o direito ao esquecimento.

---

## 3. Portabilidade de dados

- Dono da loja pode exportar todos os dados de um cliente em formato CSV/JSON:
  - Dados cadastrais.
  - Histórico de visitas e serviços.
  - Histórico de compras (sem dados fiscais de terceiros).
- Disponível no painel em: Clientes → [cliente] → "Exportar dados".

---

## 4. Consentimento e transparência

- Política de privacidade exibida no link público de agendamento.
- Checkbox de consentimento ao cadastrar cliente via link público.
- Dono da loja é o **controlador de dados**; o sistema é o **operador** (conforme LGPD).

---

## 5. Exclusão de conta da loja (churn)

Quando um pet shop cancela o plano:

1. Período de carência de 30 dias (dados mantidos, acesso suspenso).
2. Exportação completa disponível durante a carência.
3. Após 30 dias: exclusão definitiva de todos os dados da instância.
4. XMLs fiscais transferidos para responsabilidade do cliente antes da exclusão.
