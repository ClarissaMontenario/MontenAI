// TELA DE LOGIN PROVISÓRIA.
// Serve para testar o login de verdade. Pode ser refeita com o visual do Figma:
// basta manter as chamadas de useAuth() (login, register e loginAsGuest).

import { useState, type FormEvent } from "react"
import { errorMessage } from "../api"
import { useAuth } from "../auth"
import { Logo } from "../components/Logo"

export function LoginPage() {
  const { login, register, loginAsGuest, notice } = useAuth()
  const [mode, setMode] = useState<"login" | "register">("login")
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [busy, setBusy] = useState(false)

  const run = async (action: () => Promise<void>) => {
    setBusy(true)
    setError("")
    try {
      await action()
    } catch (err) {
      setError(errorMessage(err))
      setBusy(false)
    }
    // Quando dá certo a tela some sozinha (a sessão passa a existir).
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (mode === "register") {
      if (name.trim().length < 2) return setError("Informe seu nome.")
      if (password.length < 8) return setError("A senha precisa ter pelo menos 8 caracteres.")
      void run(() => register(name, email, password))
    } else {
      void run(() => login(email, password))
    }
  }

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={submit}>
        <Logo className="login-logo" />
        <p className="login-title">{mode === "login" ? "Entrar na sua conta" : "Criar conta"}</p>

        {notice && <p className="login-notice">{notice}</p>}

        {mode === "register" && (
          <label>
            Nome
            <input autoComplete="name" onChange={(e) => setName(e.target.value)} value={name} />
          </label>
        )}
        <label>
          E-mail
          <input
            autoComplete="email"
            onChange={(e) => setEmail(e.target.value)}
            required
            type="email"
            value={email}
          />
        </label>
        <label>
          Senha
          <input
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            onChange={(e) => setPassword(e.target.value)}
            required
            type="password"
            value={password}
          />
        </label>

        {error && (
          <p className="login-error" role="alert">
            {error}
          </p>
        )}

        <button className="new-document login-submit" disabled={busy} type="submit">
          {busy ? "Aguarde…" : mode === "login" ? "Entrar" : "Criar conta"}
        </button>
        <button
          className="login-link"
          onClick={() => {
            setMode(mode === "login" ? "register" : "login")
            setError("")
          }}
          type="button"
        >
          {mode === "login" ? "Não tem conta? Cadastre-se" : "Já tem conta? Entrar"}
        </button>

        <div className="login-divider">ou</div>
        <button
          className="select-file login-guest"
          disabled={busy}
          onClick={() => void run(loginAsGuest)}
          type="button"
        >
          Continuar como visitante
        </button>
        <p className="login-hint">
          Visitantes podem enviar até 3 PDFs. Tudo é temporário e a sessão dura 2 horas.
        </p>
      </form>
    </div>
  )
}
