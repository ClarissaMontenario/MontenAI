def split_documents(
    documents,
    chunk_size=1000,
    chunk_overlap=200
):
    """
    Divide documentos em chunks, preservando
    a página e a origem de cada trecho.
    """

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "O overlap deve ser menor que o tamanho do chunk."
        )

    chunks = []

    for document in documents:

        text = document["text"]
        start = 0

        while start < len(text):

            end = start + chunk_size

            # Evita cortar uma palavra ao meio
            if end < len(text):
                last_space = text.rfind(" ", start, end)

                if last_space > start:
                    end = last_space

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "page": document["page"],
                    "source": document["source"]
                })

            if end >= len(text):
                break

            start = end - chunk_overlap

    return chunks