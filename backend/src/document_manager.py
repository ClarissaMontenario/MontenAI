import hashlib
from pathlib import Path


def calculate_file_hash(file_bytes):
    """
    Calcula o hash SHA-256 de um arquivo.
    Permite identificar arquivos duplicados.
    """

    return hashlib.sha256(file_bytes).hexdigest()


def save_uploaded_file(uploaded_file, upload_dir="data/uploads"):
    """
    Salva o PDF e identifica se ele já existe.
    """

    upload_path = Path(upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)

    file_bytes = uploaded_file.getvalue()

    file_hash = calculate_file_hash(file_bytes)

    existing_files = list(upload_path.glob("*.pdf"))

    for existing_file in existing_files:

        existing_bytes = existing_file.read_bytes()

        existing_hash = calculate_file_hash(existing_bytes)

        if existing_hash == file_hash:
            return {
                "status": "duplicate",
                "path": existing_file,
                "hash": file_hash
            }

    safe_name = Path(uploaded_file.name).name

    destination = upload_path / f"{file_hash[:12]}_{safe_name}"

    destination.write_bytes(file_bytes)

    return {
        "status": "saved",
        "path": destination,
        "hash": file_hash
    }