import sys
import os
from datetime import datetime, timedelta

# Mock para teste
class MockProduct:
    def __init__(self, name, stock):
        self.name = name
        self.stock = stock

def test_prediction_logic(stock, sales_30d):
    velocity = sales_30d / 30
    if velocity > 0:
        days_left = int(stock / velocity)
        suggestion = int(velocity * 30)
        return days_left, suggestion
    return 0, 0

# Cenário: Ração Golden 15kg
# Estoque: 10 unidades
# Vendas no último mês: 15 unidades
days, suggest = test_prediction_logic(10, 15)

print(f"--- TESTE IA PREDITIVA ---")
print(f"Produto: Ração Golden 15kg")
print(f"Estoque Atual: 10 un")
print(f"Vendas/Mês: 15 un")
print(f"Resultado IA: Acaba em {days} dias.")
print(f"Sugestão de Compra: {suggest} un para o próximo mês.")
print(f"--------------------------")

if days == 20 and suggest == 15:
    print("LOGICA VALIDADA COM SUCESSO!")
else:
    print("Ajuste necessário na precisão.")
