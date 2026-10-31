from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import UUID

import fitz
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.auth import get_current_principal, router as auth_router
from src.database import Base, engine, get_db
from src.document_loader import load_pdf
from src.document_manager import calculate_file_hash
from src.models import Conversation, Document, Message
from src.rag_pipeline import ask_question
from src.text_splitter import split_documents
from src.vector_store import add_documents, delete_document, get_collection_count


load_dotenv()

ROOT = Path(__file__).resolve().parent
UPLOAD_DIR = ROOT / "data" / "uploads"
GUEST_DIR = ROOT / "data" / "guest_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
GUEST_DIR.mkdir(parents=True, exist_ok=True)

# Dados temporários de visitantes ficam na memória deste processo.
# Se o servidor reiniciar (ex.: uvicorn --reload), eles são perdidos.
GUEST_UPLOAD_LIMIT = 3
GUEST_CONVERSATIONS: dict[str, dict] = {}
GUEST_UPLOADS: dict[str, dict] = {}
GUEST_LOCK = Lock()
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
GUEST_INDEX = GUEST_DIR / "index.json"


def load_guest_index() -> None:
    """Recarrega do disco os PDFs de visitantes (sobrevive a reinícios do servidor)."""
    try:
        data = json.loads(GUEST_INDEX.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return
    with GUEST_LOCK:
        for owner, docs in data.items():
            alive = {
                doc_id: item
                for doc_id, item in docs.items()
                if (GUEST_DIR / item["stored_name"]).exists()
            }
            if alive:
                GUEST_UPLOADS[owner] = alive


def save_guest_index() -> None:
    """Grava o índice no disco. Chamar com GUEST_LOCK já adquirido."""
    tmp = GUEST_INDEX.with_suffix(".tmp")
    tmp.write_text(json.dumps(GUEST_UPLOADS, ensure_ascii=False), encoding="utf-8")
    tmp.replace(GUEST_INDEX)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    load_guest_index()
    yield


app = FastAPI(title="MontenAI API", version="2.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
   allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://monten-ai.vercel.app",
],
app.include_router(auth_router)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def get_owned_document(document_id: str, owner_id: str, db: Session) -> Document:
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == owner_id,
        )
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    return document


def serialize_message(message: Message) -> dict:
    return {
        "role": message.role,
        "content": message.content,
        "sources": json.loads(message.sources_json) if message.sources_json else [],
        "created_at": message.created_at.isoformat(),
    }


def forbidden_documents(invalid_ids: list[str], scope: str, session_empty: bool = False):
    """Monta um 403 que diz exatamente quais IDs foram rejeitados e por quê."""
    detail = {
        "message": f"Um ou mais documentos não pertencem {scope}.",
        "invalid_document_ids": invalid_ids,
    }
    if session_empty:
        detail["hint"] = (
            "Nenhum documento encontrado para esta sessão de visitante. "
            "A sessão pode ter expirado ou o servidor reiniciado: envie o PDF novamente."
        )
    return HTTPException(status_code=403, detail=detail)


def unique_ids(ids: list[UUID] | None) -> list[str] | None:
    """Converte para str minúscula e remove duplicados mantendo a ordem."""
    if not ids:
        return None
    return list(dict.fromkeys(str(item) for item in ids))


# --------------------------------------------------------------------------- #
# Saúde e documentos
# --------------------------------------------------------------------------- #

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "MontenAI",
        "version": "2.1.0",
        "indexed_chunks": get_collection_count(),
    }


@app.get("/api/documents")
def get_documents(
    principal=Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    owner_id = principal["id"]

    if principal["kind"] == "guest":
        with GUEST_LOCK:
            guest_docs = list(GUEST_UPLOADS.get(owner_id, {}).values())
        return {
            "documents": [
                {
                    "document_id": item["document_id"],
                    "name": item["filename"],
                    "pages": item["page_count"],
                    "uploaded_at": None,
                    "status": "Temporário",
                }
                for item in guest_docs
            ],
            "total": len(guest_docs),
            "temporary": True,
        }

    documents = db.scalars(
        select(Document)
        .where(Document.user_id == owner_id)
        .order_by(Document.created_at.desc())
    ).all()
    return {
        "documents": [
            {
                "document_id": doc.id,
                "name": doc.filename,
                "pages": doc.page_count,
                "uploaded_at": doc.created_at.isoformat(),
                "status": "Processado",
            }
            for doc in documents
        ],
        "total": len(documents),
        "temporary": False,
    }


def read_and_validate_pdf(file: UploadFile) -> tuple[str, bytes, int]:
    safe_name = Path(file.filename or "").name.replace("\x00", "")
    if not safe_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Envie um arquivo PDF.")

    content = file.file.read(MAX_UPLOAD_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="O PDF está vazio.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="O PDF ultrapassa o limite de 50 MB.")

    try:
        with fitz.open(stream=content, filetype="pdf") as pdf:
            page_count = pdf.page_count
        if page_count < 1:
            raise ValueError("PDF sem páginas.")
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="O arquivo enviado não é um PDF válido.",
        ) from exc

    return safe_name, content, page_count


def index_pdf(destination: Path, document_id: str, stored_name: str, owner_id: str):
    extracted = load_pdf(destination)
    chunks = split_documents(extracted)
    if not chunks:
        raise ValueError("Não foi possível extrair conteúdo do PDF.")
    add_documents(chunks, document_id, stored_name, owner_id=owner_id)


@app.post("/api/documents/upload")
def upload_document(
    file: UploadFile = File(...),
    principal=Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    safe_name, content, page_count = read_and_validate_pdf(file)
    owner_id = principal["id"]
    digest = calculate_file_hash(content)

    # ---------------------------- Visitante ---------------------------- #
    if principal["kind"] == "guest":
        with GUEST_LOCK:
            guest_docs = GUEST_UPLOADS.get(owner_id, {})
            if len(guest_docs) >= GUEST_UPLOAD_LIMIT:
                raise HTTPException(
                    status_code=429,
                    detail="Limite de 3 PDFs por sessão de visitante.",
                )
            if any(item["file_hash"] == digest for item in guest_docs.values()):
                raise HTTPException(
                    status_code=409,
                    detail="Este PDF já foi enviado nesta sessão.",
                )

        document_id = str(uuid.uuid4())
        stored_name = f"{document_id}_{safe_name}"
        destination = GUEST_DIR / stored_name
        destination.write_bytes(content)
        indexed = False
        try:
            # Processamento pesado fica fora do lock para não travar outros visitantes.
            index_pdf(destination, document_id, stored_name, owner_id)
            indexed = True
            with GUEST_LOCK:
                GUEST_UPLOADS.setdefault(owner_id, {})[document_id] = {
                    "document_id": document_id,
                    "filename": safe_name,
                    "stored_name": stored_name,
                    "file_hash": digest,
                    "page_count": page_count,
                }
                save_guest_index()
        except Exception as exc:
            if indexed:
                delete_document(document_id, owner_id=owner_id)
            destination.unlink(missing_ok=True)
            raise HTTPException(
                status_code=500,
                detail=f"Falha ao processar PDF: {exc}",
            ) from exc

        return {
            "message": "PDF temporário processado.",
            "document": {
                "document_id": document_id,
                "name": safe_name,
                "pages": page_count,
                "status": "Temporário",
            },
        }

    # ------------------------- Usuário logado -------------------------- #
    existing = db.scalar(
        select(Document).where(
            Document.user_id == owner_id,
            Document.file_hash == digest,
        )
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Este PDF já está cadastrado na sua conta.",
        )

    document_id = str(uuid.uuid4())
    stored_name = f"{owner_id}_{document_id}_{safe_name}"
    destination = UPLOAD_DIR / stored_name
    destination.write_bytes(content)
    indexed = False
    try:
        index_pdf(destination, document_id, stored_name, owner_id)
        indexed = True

        document = Document(
            id=document_id,
            user_id=owner_id,
            filename=safe_name,
            stored_name=stored_name,
            file_hash=digest,
            page_count=page_count,
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return {
            "message": "Documento processado e indexado.",
            "document": {
                "document_id": document.id,
                "name": document.filename,
                "pages": document.page_count,
                "status": "Processado",
            },
        }
    except Exception as exc:
        db.rollback()
        if indexed:
            delete_document(document_id, owner_id=owner_id)
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao processar PDF: {exc}",
        ) from exc


@app.delete("/api/documents/{document_id}")
def remove_document(
    document_id: UUID,
    principal=Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    document_id = str(document_id)
    owner_id = principal["id"]

    if principal["kind"] == "guest":
        with GUEST_LOCK:
            guest_docs = GUEST_UPLOADS.get(owner_id, {})
            item = guest_docs.get(document_id)
            if item is None:
                raise HTTPException(status_code=404, detail="Documento não encontrado.")
            try:
                removed_chunks = delete_document(document_id, owner_id=owner_id)
                (GUEST_DIR / item["stored_name"]).unlink(missing_ok=True)
                guest_docs.pop(document_id, None)
                save_guest_index()
            except Exception as exc:
                raise HTTPException(
                    status_code=500,
                    detail=f"Falha ao excluir documento temporário: {exc}",
                ) from exc
        return {
            "message": "Documento temporário excluído.",
            "document_id": document_id,
            "chunks_removed": removed_chunks,
        }

    document = get_owned_document(document_id, owner_id, db)
    file_path = UPLOAD_DIR / document.stored_name
    try:
        removed_chunks = delete_document(document_id, owner_id=owner_id)
        db.delete(document)
        db.commit()
        file_path.unlink(missing_ok=True)
        return {
            "message": "Documento excluído com sucesso.",
            "document_id": document_id,
            "chunks_removed": removed_chunks,
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao excluir documento: {exc}",
        ) from exc


# --------------------------------------------------------------------------- #
# Chat
# --------------------------------------------------------------------------- #

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000)
    document_ids: list[UUID] | None = None
    conversation_id: str | None = None


def run_rag(question: str, document_ids, history, owner_id: str) -> dict:
    try:
        return ask_question(
            question=question,
            top_k=8,
            document_ids=document_ids,
            chat_history=history,
            owner_id=owner_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Não foi possível gerar a resposta: {exc}",
        ) from exc


@app.post("/api/chat")
def chat(
    payload: ChatRequest,
    principal=Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Digite uma pergunta.")

    owner_id = principal["id"]
    conversation_id = payload.conversation_id or str(uuid.uuid4())
    document_ids = unique_ids(payload.document_ids)

    # ---------------------------- Visitante ---------------------------- #
    if principal["kind"] == "guest":
        with GUEST_LOCK:
            guest_docs = GUEST_UPLOADS.get(owner_id, {})
            if document_ids:
                invalid = [doc_id for doc_id in document_ids if doc_id not in guest_docs]
                if invalid:
                    raise forbidden_documents(
                        invalid,
                        scope="a esta sessão",
                        session_empty=not guest_docs,
                    )

            guest_data = GUEST_CONVERSATIONS.setdefault(owner_id, {})
            conversation = guest_data.get(conversation_id)
            if conversation is None:
                if payload.conversation_id:
                    raise HTTPException(status_code=404, detail="Conversa não encontrada.")
                conversation = {
                    "conversation_id": conversation_id,
                    "title": question[:72],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "messages": [],
                }
                guest_data[conversation_id] = conversation
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in conversation["messages"]
            ]

        result = run_rag(question, document_ids, history, owner_id)

        now = datetime.now(timezone.utc).isoformat()
        with GUEST_LOCK:
            conversation["messages"].extend([
                {"role": "user", "content": question, "created_at": now, "sources": []},
                {
                    "role": "assistant",
                    "content": result["answer"],
                    "created_at": now,
                    "sources": result["sources"],
                },
            ])
        return {
            "conversation_id": conversation_id,
            "answer": result["answer"],
            "sources": result["sources"],
        }

    # ------------------------- Usuário logado -------------------------- #
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == owner_id,
        )
    )
    if payload.conversation_id and conversation is None:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")

    if document_ids:
        owned_ids = set(
            db.scalars(
                select(Document.id).where(
                    Document.user_id == owner_id,
                    Document.id.in_(document_ids),
                )
            ).all()
        )
        invalid = [doc_id for doc_id in document_ids if doc_id not in owned_ids]
        if invalid:
            raise forbidden_documents(invalid, scope="à sua conta")

    history = []
    if conversation:
        history = [
            {"role": message.role, "content": message.content}
            for message in conversation.messages
        ]

    result = run_rag(question, document_ids, history, owner_id)

    now = datetime.now(timezone.utc)
    if conversation is None:
        conversation = Conversation(
            id=conversation_id,
            user_id=owner_id,
            title=question[:72],
            created_at=now,
            updated_at=now,
        )
        db.add(conversation)
        db.flush()

    db.add_all([
        Message(
            conversation_id=conversation.id,
            role="user",
            content=question,
            created_at=now,
        ),
        Message(
            conversation_id=conversation.id,
            role="assistant",
            content=result["answer"],
            sources_json=json.dumps(result["sources"], ensure_ascii=False),
            created_at=now,
        ),
    ])
    conversation.updated_at = now
    db.commit()
    return {
        "conversation_id": conversation.id,
        "answer": result["answer"],
        "sources": result["sources"],
    }


# --------------------------------------------------------------------------- #
# Histórico
# --------------------------------------------------------------------------- #

@app.get("/api/history")
def get_history(
    principal=Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    owner_id = principal["id"]
    if principal["kind"] == "guest":
        with GUEST_LOCK:
            conversations = list(GUEST_CONVERSATIONS.get(owner_id, {}).values())
        conversations.sort(key=lambda item: item["created_at"], reverse=True)
        return {"conversations": conversations}

    conversations = db.scalars(
        select(Conversation)
        .where(Conversation.user_id == owner_id)
        .order_by(Conversation.updated_at.desc())
    ).all()
    return {
        "conversations": [
            {
                "conversation_id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "messages": [serialize_message(message) for message in conversation.messages],
            }
            for conversation in conversations
        ]
    }


@app.delete("/api/history/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    principal=Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    owner_id = principal["id"]
    if principal["kind"] == "guest":
        with GUEST_LOCK:
            guest_data = GUEST_CONVERSATIONS.get(owner_id, {})
            conversation = guest_data.pop(conversation_id, None)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversa não encontrada.")
        return {"message": "Conversa temporária excluída."}

    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == owner_id,
        )
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")
    db.delete(conversation)
    db.commit()
    return {"message": "Conversa excluída com sucesso."}