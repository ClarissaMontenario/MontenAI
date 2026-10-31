from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from src.database import Base, engine
from src.auth import router as auth_router

import fitz
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.document_loader import load_pdf
from src.document_manager import calculate_file_hash
from src.rag_pipeline import ask_question
from src.text_splitter import split_documents
from src.vector_store import add_documents, delete_document, list_documents, get_collection_count

load_dotenv()
ROOT = Path(__file__).resolve().parent
UPLOAD_DIR = ROOT / "data" / "uploads"
HISTORY_PATH = ROOT / "chat_history.json"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESS_LOCK = Lock()

app = FastAPI(title="MontenAI API", version="1.0.0")
# Rotas de autenticação
app.include_router(auth_router)


# Criar tabelas do banco na inicialização
@app.on_event("startup")
def initialize_database():
    Base.metadata.create_all(bind=engine)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000)
    document_ids: list[str] | None = None
    conversation_id: str | None = None


def _read_history():
    if not HISTORY_PATH.exists():
        return []
    try:
        return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def _write_history(items):
    HISTORY_PATH.write_text(json.dumps(items[-300:], ensure_ascii=False, indent=2), encoding="utf-8")


def _document_details():
    items = list_documents()
    result = []
    for item in items:
        doc_id = item["document_id"]
        file_path = next((p for p in UPLOAD_DIR.glob("*.pdf") if p.name == item["name"]), None)
        pages = set()
        try:
            # Chroma metadata gives exact pages represented in the indexed chunks.
            from src.vector_store import collection
            rows = collection.get(where={"document_id": doc_id}, include=["metadatas"])
            pages = {m.get("page") for m in (rows.get("metadatas") or []) if m.get("page") is not None}
        except Exception:
            pass
        stat = file_path.stat() if file_path and file_path.exists() else None
        result.append({
            **item,
            "pages": len(pages),
            "size_bytes": stat.st_size if stat else None,
            "uploaded_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat() if stat else None,
            "status": "Processado",
        })
    result.sort(key=lambda x: x.get("uploaded_at") or "", reverse=True)
    return result


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "MontenAI", "indexed_chunks": get_collection_count()}


@app.get("/api/documents")
def documents():
    docs = _document_details()
    return {"documents": docs, "total": len(docs), "pages": sum(d["pages"] for d in docs), "chunks": get_collection_count()}


@app.post("/api/documents/upload")
def upload_document(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Envie um arquivo PDF.")
    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="O arquivo está vazio.")
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="O PDF ultrapassa o limite de 50 MB.")

    digest = calculate_file_hash(content)
    with PROCESS_LOCK:
        indexed_names = {item["name"] for item in list_documents()}
        existing = next((p for p in UPLOAD_DIR.glob("*.pdf")
                         if p.name in indexed_names and calculate_file_hash(p.read_bytes()) == digest), None)
        if existing:
            raise HTTPException(status_code=409, detail=f"Este PDF já está indexado: {existing.name}")

        safe_name = Path(file.filename).name.replace("\x00", "")
        stored_name = f"{digest[:12]}_{safe_name}"
        destination = UPLOAD_DIR / stored_name
        destination.write_bytes(content)
        document_id = str(uuid.uuid4())
        try:
            extracted = load_pdf(destination)
            chunks = split_documents(extracted)
            if not chunks:
                raise ValueError("Não foi possível extrair conteúdo do PDF.")
            add_documents(chunks, document_id, stored_name)
            return {
                "message": "Documento processado e indexado.",
                "document": {
                    "document_id": document_id,
                    "name": stored_name,
                    "pages": len({p["page"] for p in extracted}),
                    "chunks": len(chunks),
                    "status": "Processado",
                },
            }
        except Exception as exc:
            destination.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=f"Falha ao processar o PDF: {exc}") from exc


@app.delete("/api/documents/{document_id}")
def remove_document(document_id: str):
    removed = delete_document(document_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Documento não encontrado no índice.")
    # Keep original file by default: deleting the index must not destroy the user's upload.
    return {"message": "Documento removido da biblioteca indexada.", "chunks_removed": removed}


@app.post("/api/chat")
def chat(payload: ChatRequest):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Digite uma pergunta.")
    conversation_id = payload.conversation_id or str(uuid.uuid4())
    history = _read_history()
    conversation = next((x for x in history if x["conversation_id"] == conversation_id), None)
    messages = conversation["messages"] if conversation else []
    try:
        result = ask_question(
            question=question,
            top_k=8,
            document_ids=payload.document_ids,
            chat_history=messages,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Não foi possível gerar a resposta: {exc}") from exc

    now = datetime.now(timezone.utc).isoformat()
    messages.extend([
        {"role": "user", "content": question, "created_at": now},
        {"role": "assistant", "content": result["answer"], "sources": result["sources"], "created_at": now},
    ])
    if conversation is None:
        conversation = {"conversation_id": conversation_id, "title": question[:72], "messages": messages, "created_at": now}
        history.insert(0, conversation)
    else:
        conversation["messages"] = messages
        conversation["updated_at"] = now
        history.remove(conversation)
        history.insert(0, conversation)
    _write_history(history)
    return {"conversation_id": conversation_id, "answer": result["answer"], "sources": result["sources"]}


@app.get("/api/history")
def history():
    return {"conversations": _read_history()}


