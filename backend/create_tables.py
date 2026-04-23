from app.database import Base, engine
# Import all models to register them with Base.metadata
from app.models.store import Store
from app.models.user import User
from app.models.cliente import Cliente, Pet
from app.models.pet_vaccine import PetVaccine
from app.models.prontuario import Prontuario
from app.models.produto import Produto
from app.models.venda import Venda, VendaPagamento, ItemVenda
from app.models.agendamento import Agendamento
from app.models.hotel import Hospedagem
from app.models.pacote import Pacote
from app.models.financeiro import Despesa
from app.models.service import Service

print("Criando tabelas no banco de dados...")
Base.metadata.create_all(bind=engine)
print("Tabelas criadas com sucesso!")
