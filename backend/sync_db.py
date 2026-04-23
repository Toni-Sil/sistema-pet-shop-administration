from app.database import engine, Base
import importlib
import pkgutil
import app.models

# Import all models dynamically
def import_all_models():
    for _, name, _ in pkgutil.iter_modules(app.models.__path__):
        importlib.import_module(f"app.models.{name}")

print("Syncing database...")
import_all_models()
Base.metadata.create_all(bind=engine)
print("Database synced successfully!")
