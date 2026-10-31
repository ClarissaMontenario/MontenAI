
import os
from functools import lru_cache
from google import genai
from google.genai import types

MODEL_NAME = "gemini-embedding-001"
EMBEDDING_DIMENSION = 768


@lru_cache(maxsize=1)
def get_embedding_client():
    """Inicializa e reutiliza o cliente Gemini."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY não configurada."
        )

    return genai.Client(api_key=api_key)


def generate_embeddings(texts):
    """Gera embeddings de documentos em pequenos lotes."""

    if not texts:
        return []

    client = get_embedding_client()
    embeddings = []

    batch_size = 10

    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]

        response = client.models.embed_content(
            model=MODEL_NAME,
            contents=batch,
            config=types.EmbedContentConfig(
                output_dimensionality=EMBEDDING_DIMENSION,
                task_type="RETRIEVAL_DOCUMENT"
            )
        )

        embeddings.extend(
            item.values
            for item in response.embeddings
        )

    return embeddings


def generate_query_embedding(question):
    """Gera embedding para uma pergunta de busca."""

    if not question or not question.strip():
        raise ValueError(
            "A pergunta não pode estar vazia."
        )

    client = get_embedding_client()

    response = client.models.embed_content(
        model=MODEL_NAME,
        contents=question,
        config=types.EmbedContentConfig(
            output_dimensionality=EMBEDDING_DIMENSION,
            task_type="RETRIEVAL_QUERY"
        )
    )

    return response.embeddings[0].values
