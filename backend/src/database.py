
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Caminho principal do backend
ROOT = Path(__file__).resolve().parent.parent

# Banco local para desenvolvimento.
# Na hospedagem, DATABASE_URL apontará para PostgreSQL.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{ROOT / 'montenai.db'}"
)

# Configuração da conexão
connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

# Gerenciador de sessões
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Classe base dos modelos
class Base(DeclarativeBase):
    pass


# Dependência para as rotas FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
