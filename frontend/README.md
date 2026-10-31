# MontenAI – Front end

React + Vite + Tailwind. Conversa com o back end FastAPI (`api_v2.py`).

## Como rodar

1. Back end (numa janela do terminal, na pasta do back end):

   ```
   .venv\Scripts\python.exe -m uvicorn api_v2:app --host 127.0.0.1 --port 8000
   ```

   Atenção: o `run_api.bat` atual sobe o `api:app` (versão antiga, sem login). Troque `api:app` por `api_v2:app`.

2. Front end (nesta pasta):

   ```
   npm install
   npm run dev
   ```

   Abra http://localhost:5173 (a porta precisa ser 5173, é a única liberada no CORS do back end).

Se o back end estiver em outro endereço, copie `.env.example` para `.env` e ajuste `VITE_API_URL`.

## Onde mexer

| O quê | Arquivo |
| --- | --- |
| Logo | `public/montenai-logo.png` |
| Tela de login (provisória) | `src/pages/LoginPage.tsx` |
| Lógica de login / sessão | `src/auth.tsx` (`useAuth()`) |
| Chamadas à API | `src/api.ts` |
| Tamanho das fontes | variáveis `--fs-*` no topo de `src/index.css` |
| Telas | `src/pages/` |

## Login

`useAuth()` oferece `login`, `register`, `loginAsGuest`, `logout` e `session`.
O token fica salvo no navegador e, se expirar (visitante dura 2 horas), o site volta para o login com um aviso.
Para refazer a tela de login com o visual do Figma, troque só o conteúdo de `LoginPage.tsx` e mantenha essas chamadas.
