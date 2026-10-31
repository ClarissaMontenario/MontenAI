
import chromadb
import uuid
from pathlib import Path

from src.embeddings import (
    generate_embeddings,
    generate_query_embedding
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "chroma_db"

client = chromadb.PersistentClient(path=str(DB_PATH))

# Nova coleção para os embeddings do Gemini.
# A coleção antiga será preservada.
collection = client.get_or_create_collection(
    name="documents_gemini",
    metadata={"hnsw:space": "cosine"}
)


def add_documents(
    chunks,
    document_id,
    document_name,
    owner_id
):
    """Adiciona trechos identificados pelo proprietário."""

    if not chunks:
        return 0

    texts = [chunk["text"] for chunk in chunks]

    # Gera embeddings pela API Gemini.
    embeddings = generate_embeddings(texts)

    ids = [
        str(uuid.uuid4())
        for _ in chunks
    ]

    metadatas = [
        {
            "source": document_name,
            "page": chunk["page"],
            "document_id": document_id,
            "owner_id": owner_id,
        }
        for chunk in chunks
    ]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return len(chunks)


def search_documents(
    question,
    top_k=5,
    document_ids=None,
    owner_id=None
):
    """Busca trechos somente nos documentos do proprietário."""

    if not question or not question.strip():
        raise ValueError("A pergunta não pode estar vazia.")

    if not owner_id:
        raise ValueError(
            "Identificação do proprietário obrigatória."
        )

    query_embedding = generate_query_embedding(question)

    filters = [
        {"owner_id": owner_id}
    ]

    if document_ids:
        filters.append({
            "document_id": {"$in": document_ids}
        })

    where_filter = (
        filters[0]
        if len(filters) == 1
        else {"$and": filters}
    )

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter
    )

    retrieved_chunks = []

    if (
        not results["documents"]
        or not results["documents"][0]
    ):
        return retrieved_chunks

    for i, text in enumerate(results["documents"][0]):

        metadata = results["metadatas"][0][i]

        retrieved_chunks.append({
            "text": text,
            "source": metadata["source"],
            "page": metadata["page"],
            "document_id": metadata["document_id"],
            "distance": results["distances"][0][i]
        })

    return retrieved_chunks


def delete_document(document_id, owner_id):
    """Exclui somente os trechos do documento do proprietário."""

    if not owner_id:
        raise ValueError(
            "Identificação do proprietário obrigatória."
        )

    where_filter = {
        "$and": [
            {"document_id": document_id},
            {"owner_id": owner_id}
        ]
    }

    results = collection.get(
        where=where_filter,
        include=["metadatas"]
    )

    ids = results["ids"]

    if not ids:
        return 0

    collection.delete(ids=ids)

    return len(ids)


def list_documents(owner_id):
    """Lista documentos pertencentes ao usuário."""

    if not owner_id:
        raise ValueError(
            "Identificação do proprietário obrigatória."
        )

    results = collection.get(
        where={"owner_id": owner_id},
        include=["metadatas"]
    )

    documents = {}

    for metadata in results["metadatas"]:

        document_id = metadata["document_id"]

        if document_id not in documents:
            documents[document_id] = {
                "document_id": document_id,
                "name": metadata["source"],
                "owner_id": metadata["owner_id"],
                "chunks": 0
            }

        documents[document_id]["chunks"] += 1

    return list(documents.values())


def get_collection_count(owner_id=None):
    """Retorna a quantidade de trechos."""

    if owner_id:
        return collection.count(
            where={"owner_id": owner_id}
        )

    return collection.count()
