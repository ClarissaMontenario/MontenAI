# MontenAI — interface React integrada ao backend Python

Esta versão mantém os módulos atuais do MontenAI (extração/OCR de PDF, divisão em chunks, embeddings, ChromaDB e RAG com Groq) e acrescenta uma API FastAPI para a interface React do Figma.

## Estrutura

- `backend/`: código Python existente, API FastAPI, `src/`, assets, dashboard e scripts.
- `frontend/`: aplicação React + Vite com a identidade visual enviada.
- `backend/data/uploads/`: PDFs enviados pela interface (criada automaticamente).
- `backend/chroma_db/`: banco vetorial (criado automaticamente; não incluído no ZIP).

## Requisitos

- Windows 10/11
- Python 3.11 ou 3.12 recomendado para compatibilidade com os pacotes usados
- Node.js 20.19+ ou 22.12+
- Uma chave Groq válida

## 1. Configurar o backend

Abra PowerShell na pasta `MontenAI_Integrado\backend` e execute:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Abra o arquivo `backend\.env` e substitua `cole_sua_chave_aqui` pela sua chave Groq. Não envie esse arquivo a terceiros.

Se o comando `py -3.12` não funcionar, use o caminho do Python instalado na sua máquina para criar o ambiente virtual.

## 2. Iniciar o backend

Dê dois cliques em `backend\run_api.bat`, ou execute no PowerShell:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

A API fica em `http://127.0.0.1:8000`; documentação técnica em `http://127.0.0.1:8000/docs`.

## 3. Iniciar o frontend

Abra outro terminal na pasta `MontenAI_Integrado\frontend`:

```powershell
npm install
npm run dev
```

Abra o endereço mostrado pelo Vite, normalmente `http://127.0.0.1:5173`.

Mantenha os dois terminais abertos enquanto usa o MontenAI.

## Funcionalidades conectadas

- Listagem real dos PDFs indexados no ChromaDB.
- Upload de PDF (limite de 50 MB), prevenção de duplicados por SHA-256, extração/OCR e indexação.
- Perguntas ao RAG com Groq, histórico contextual e referências a documento/página.
- Histórico persistido em `backend/chat_history.json`.
- Exclusão de um documento do índice vetorial. O PDF original permanece em `data/uploads` por segurança.
- Contadores de documentos e páginas com base no conteúdo indexado.

## Manter o Streamlit

O `backend/app.py` original foi mantido. Para abrir a versão Streamlit antiga, execute:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

O painel de avaliação também foi mantido em `backend/dashboard.py` e pode ser iniciado com `run_dashboard.bat`.

## Observações importantes

- O arquivo `.env`, o ambiente `.venv` e o banco `chroma_db` não são distribuídos.
- O primeiro processamento pode demorar porque o FastEmbed baixa/carrega o modelo de embeddings. PDFs com páginas digitalizadas/fotos também passam pelo modelo visual da Groq.
- A API foi validada por compilação estática dos módulos Python. O fluxo completo depende da instalação das dependências e de uma chave Groq válida; não foi possível executar a inferência real neste ambiente.
- Esta primeira integração mantém um único serviço local. Para acesso simultâneo por outros computadores, será necessário rever host, CORS, autenticação e implantação.
