
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database import get_db
from src.models import User
from src.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_guest_token,
    decode_access_token,
)


# ==========================================
# CONFIGURAÇÃO
# ==========================================

router = APIRouter(
    prefix="/api/auth",
    tags=["Autenticação"],
)

bearer_scheme = HTTPBearer()


# ==========================================
# MODELOS DE ENTRADA E SAÍDA
# ==========================================

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    preferred_language: str
    is_verified: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ==========================================
# CADASTRO
# ==========================================

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    email = str(payload.email).lower().strip()

    existing = db.scalar(
        select(User).where(User.email == email)
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Este e-mail já está cadastrado.",
        )

    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Este e-mail já está cadastrado.",
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


# ==========================================
# LOGIN
# ==========================================

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    email = str(payload.email).lower().strip()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if not user or not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


# ==========================================
# IDENTIFICAR USUÁRIO AUTENTICADO
# ==========================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
):
    unauthorized = HTTPException(
        status_code=401,
        detail="Sessão inválida ou expirada.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(
            credentials.credentials
        )

        user_id = payload.get("sub")
        token_type = payload.get("typ")

        if not user_id or token_type != "user":
            raise unauthorized

    except Exception:
        raise unauthorized

    user = db.get(User, user_id)

    if not user:
        raise unauthorized

    return user


# ==========================================
# IDENTIFICAR USUÁRIO OU VISITANTE
# ==========================================

def get_current_principal(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
):
    unauthorized = HTTPException(
        status_code=401,
        detail="Sessão inválida ou expirada.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(
            credentials.credentials
        )

        identity = payload.get("sub")
        token_type = payload.get("typ")

        if not identity:
            raise unauthorized

        # Sessão de visitante
        if (
            token_type == "guest"
            and identity.startswith("guest:")
        ):
            return {
                "kind": "guest",
                "id": identity,
                "user": None,
            }

        # Conta cadastrada
        if token_type == "user":
            user = db.get(User, identity)

            if user:
                return {
                    "kind": "user",
                    "id": user.id,
                    "user": user,
                }

        raise unauthorized

    except HTTPException:
        raise

    except Exception:
        raise unauthorized


# ==========================================
# DADOS DA CONTA
# ==========================================

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    user: User = Depends(get_current_user),
):
    return user

# ==========================================
# IDENTIFICAR SESSÃO (USUÁRIO OU VISITANTE)
# ==========================================

@router.get("/session")
def get_current_session(
    principal: dict = Depends(get_current_principal),
):
    if principal["kind"] == "guest":
        return {
            "kind": "guest",
            "id": principal["id"],
            "user": None,
        }

    return {
        "kind": "user",
        "id": principal["id"],
        "user": principal["user"],
    }

# ==========================================
# ACESSO COMO VISITANTE
# ==========================================

@router.post("/guest")
def create_guest_session():
    token = create_guest_token()

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 7200,
        "user": None,
    }
