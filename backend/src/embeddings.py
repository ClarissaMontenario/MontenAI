
from functools import lru_cache
from fastembed import TextEmbedding

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@lru_cache(maxsize=1)
def get_embedding_model():
    """Carrega o modelo apenas quando necessário e reutiliza."""
    return TextEmbedding(model_name=MODEL_NAME)


def generate_embeddings(texts):
    """Transforma textos em vetores numéricos."""

    if not texts:
        return []

    model = get_embedding_model()
    embeddings = model.embed(texts)

    return [embedding.tolist() for embedding in embeddings]


def generate_query_embedding(question):
    """Gera o embedding de uma pergunta."""

    if not question or not question.strip():
        raise ValueError("A pergunta não pode estar vazia.")

    return generate_embeddings([question])[0]
