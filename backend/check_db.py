
import chromadb
from pathlib import Path

print("ETAPA 1 - Iniciando")

PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "chroma_db"

print("ETAPA 2 - Caminho:", DB_PATH)

client = chromadb.PersistentClient(path=str(DB_PATH))

print("ETAPA 3 - Conexão realizada")

collections = client.list_collections()

print("ETAPA 4 - Coleções encontradas:", len(collections))

for item in collections:
    collection = client.get_collection(item.name)
    print(f"{item.name}: {collection.count()} chunks")

print("ETAPA 5 - Teste concluído")

