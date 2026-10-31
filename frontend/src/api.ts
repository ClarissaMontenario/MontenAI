// Cliente da API do MontenAI (back end: api_v2.py).
// Todas as chamadas passam por aqui. O token fica salvo no navegador.

export const API_URL =
  (import.meta.env.VITE_API_URL as string | undefined) ?? "http://127.0.0.1:8001"

// ---------- Tipos ----------

export interface User {
  id: string
  name: string
  email: string
  preferred_language: string
  is_verified: boolean
}

export interface Session {
  kind: "user" | "guest"
  id: string
  user: User | null
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in?: number
  user: User | null
}

export interface DocumentItem {
  document_id: string
  name: string
  pages: number | null
  uploaded_at: string | null
  status: string
}

export interface Source {
  document: string
  page: number | null
  document_id: string
}

export interface ChatMessage {
  role: "user" | "assistant"
  content: string
  sources?: Source[]
  created_at?: string
}

export interface Conversation {
  conversation_id: string
  title: string
  created_at: string
  updated_at?: string
  messages: ChatMessage[]
}

// ---------- Token ----------

const TOKEN_KEY = "montenai_token"

export const tokenStore = {
  get(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY)
    } catch {
      return null
    }
  },
  set(token: string) {
    try {
      localStorage.setItem(TOKEN_KEY, token)
    } catch {
      /* navegador bloqueou o armazenamento: a sessão vale só até recarregar */
    }
  },
  clear() {
    try {
      localStorage.removeItem(TOKEN_KEY)
    } catch {
      /* ignorar */
    }
  },
}

// Chamado quando o servidor responde 401 com um token salvo (sessão expirada).
let unauthorizedHandler: (() => void) | null = null
export function setUnauthorizedHandler(handler: (() => void) | null) {
  unauthorizedHandler = handler
}

// ---------- Requisição base ----------

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function extractMessage(detail: unknown): string {
  if (typeof detail === "string") return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (item && typeof item === "object" && "msg" in item ? String(item.msg) : ""))
      .filter(Boolean)
      .join(" ")
  }
  if (detail && typeof detail === "object") {
    const { message, hint } = detail as { message?: string; hint?: string }
    return [message, hint].filter(Boolean).join(" ")
  }
  return "Ocorreu um erro inesperado."
}

async function request<T>(
  path: string,
  init: RequestInit & { auth?: boolean } = {},
): Promise<T> {
  const { auth = true, ...options } = init
  const headers = new Headers(options.headers)
  const token = tokenStore.get()

  if (auth && token) headers.set("Authorization", `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }

  let response: Response
  try {
    response = await fetch(API_URL + path, { ...options, headers })
  } catch {
    throw new ApiError(
      0,
      "Não foi possível conectar ao servidor. Confira se o back end está rodando.",
    )
  }

  if (!response.ok) {
    let detail: unknown
    try {
      detail = (await response.json()).detail
    } catch {
      /* resposta sem JSON */
    }
    if (response.status === 401 && auth && token) unauthorizedHandler?.()
    throw new ApiError(response.status, extractMessage(detail))
  }

  return (await response.json()) as T
}

// ---------- Endpoints ----------

export const api = {
  // Autenticação
  login: (email: string, password: string) =>
    request<TokenResponse>("/api/auth/login", {
      method: "POST",
      auth: false,
      body: JSON.stringify({ email, password }),
    }),
  register: (name: string, email: string, password: string) =>
    request<TokenResponse>("/api/auth/register", {
      method: "POST",
      auth: false,
      body: JSON.stringify({ name, email, password }),
    }),
  guest: () => request<TokenResponse>("/api/auth/guest", { method: "POST", auth: false }),
  session: () => request<Session>("/api/auth/session"),

  // Documentos
  documents: () =>
    request<{ documents: DocumentItem[]; total: number; temporary: boolean }>("/api/documents"),
  uploadDocument: (file: File) => {
    const form = new FormData()
    form.append("file", file)
    return request<{ message: string; document: DocumentItem }>("/api/documents/upload", {
      method: "POST",
      body: form,
    })
  },
  deleteDocument: (id: string) =>
    request<{ message: string }>(`/api/documents/${id}`, { method: "DELETE" }),

  // Chat e histórico
  chat: (payload: { question: string; document_ids?: string[]; conversation_id?: string }) =>
    request<{ conversation_id: string; answer: string; sources: Source[] }>("/api/chat", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  history: () => request<{ conversations: Conversation[] }>("/api/history"),
  deleteConversation: (id: string) =>
    request<{ message: string }>(`/api/history/${id}`, { method: "DELETE" }),
}

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Ocorreu um erro inesperado."
}
