// Login e sessão. Qualquer tela pode usar:  const { session, login, register, loginAsGuest, logout } = useAuth()
// A tela de login (pages/LoginPage.tsx) é só um visual provisório: pode ser
// trocada à vontade, desde que continue chamando essas funções.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import { api, setUnauthorizedHandler, tokenStore, type Session, type TokenResponse } from "./api"

interface AuthContextValue {
  session: Session | null
  loading: boolean // true enquanto confirma com o servidor se o token salvo ainda vale
  notice: string // aviso para a tela de login (ex.: "Sua sessão expirou")
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  loginAsGuest: () => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState<boolean>(() => tokenStore.get() !== null)
  const [notice, setNotice] = useState("")

  const logout = useCallback((message = "") => {
    tokenStore.clear()
    setSession(null)
    setNotice(message)
  }, [])

  // Ao abrir o site: se já existe token salvo, confirma que ele ainda é válido.
  useEffect(() => {
    if (!tokenStore.get()) return
    let cancelled = false
    api
      .session()
      .then((current) => {
        if (!cancelled) setSession(current)
      })
      .catch(() => {
        if (!cancelled) tokenStore.clear()
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  // Se qualquer chamada voltar 401 (token expirado), volta para o login.
  useEffect(() => {
    setUnauthorizedHandler(() => logout("Sua sessão expirou. Entre novamente."))
    return () => setUnauthorizedHandler(null)
  }, [logout])

  const startSession = useCallback((response: TokenResponse, kind: "user" | "guest") => {
    tokenStore.set(response.access_token)
    setNotice("")
    setSession({ kind, id: response.user?.id ?? "guest", user: response.user })
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      loading,
      notice,
      login: async (email, password) => {
        startSession(await api.login(email.trim(), password), "user")
      },
      register: async (name, email, password) => {
        startSession(await api.register(name.trim(), email.trim(), password), "user")
      },
      loginAsGuest: async () => {
        startSession(await api.guest(), "guest")
      },
      logout: () => logout(),
    }),
    [session, loading, notice, startSession, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error("useAuth precisa estar dentro de <AuthProvider>")
  return context
}
