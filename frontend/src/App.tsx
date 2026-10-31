import { useState } from "react"
import { AuthProvider, useAuth } from "./auth"
import { useChat } from "./chat"
import { Icon, type IconName } from "./components/Icon"
import { Logo } from "./components/Logo"
import { DocsProvider } from "./docs"
import type { NavKey } from "./nav"
import { AssistantPage } from "./pages/AssistantPage"
import { DocumentsPage } from "./pages/DocumentsPage"
import { HistoryPage } from "./pages/HistoryPage"
import { HomePage } from "./pages/HomePage"
import { LoginPage } from "./pages/LoginPage"
import { initials } from "./util"

const navItems: { label: NavKey; icon: IconName }[] = [
  { label: "Início", icon: "home" },
  { label: "Assistente", icon: "sparkles" },
  { label: "Meus documentos", icon: "files" },
  { label: "Histórico", icon: "history" },
]

function Shell() {
  const { session, logout } = useAuth()
  const [activeNav, setActiveNav] = useState<NavKey>("Início")
  const [pendingConversation, setPendingConversation] = useState<string | null>(null)
  // A conversa da tela inicial fica aqui para não se perder ao trocar de aba.
  const homeChat = useChat()

  const isGuest = session?.kind === "guest"
  const displayName = session?.user?.name ?? "Visitante"

  const openConversation = (id: string) => {
    setPendingConversation(id)
    setActiveNav("Assistente")
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-wrap">
          <Logo />
        </div>

        <nav aria-label="Navegação principal" className="nav-list">
          {navItems.map((item) => (
            <button
              className={`nav-item ${activeNav === item.label ? "active" : ""}`}
              key={item.label}
              onClick={() => setActiveNav(item.label)}
              type="button"
            >
              <span className="nav-icon">
                <Icon name={item.icon} size={22} />
              </span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-spacer" />

        {isGuest && (
          <div className="guest-note">
            <p>Modo visitante</p>
            <span>Seus documentos são temporários: até 3 PDFs e sessão de 2 horas.</span>
            <button onClick={logout} type="button">
              Entrar com uma conta
            </button>
          </div>
        )}

        <div className="profile">
          <div className="avatar">{initials(displayName)}</div>
          <div className="profile-copy">
            <p>{displayName}</p>
            <span>{isGuest ? "Sessão de visitante" : session?.user?.email}</span>
          </div>
          <button
            aria-label="Sair"
            className="icon-button plain"
            onClick={logout}
            title="Sair"
            type="button"
          >
            <Icon name="logout" size={21} />
          </button>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <p className="eyebrow">{activeNav === "Início" ? "Visão geral" : activeNav}</p>
          <div className="top-actions">
            <button aria-label="Notificações" className="icon-button" type="button">
              <Icon name="bell" size={21} />
            </button>
            <div className="top-divider" />
            <div className="mini-avatar">{initials(displayName)}</div>
          </div>
        </header>

        {activeNav === "Início" && <HomePage chat={homeChat} goTo={setActiveNav} />}
        {activeNav === "Assistente" && (
          <AssistantPage
            initialConversationId={pendingConversation}
            onInitialConsumed={() => setPendingConversation(null)}
          />
        )}
        {activeNav === "Meus documentos" && <DocumentsPage />}
        {activeNav === "Histórico" && <HistoryPage onOpen={openConversation} />}
      </main>
    </div>
  )
}

function Gate() {
  const { session, loading } = useAuth()

  if (loading) return <div className="splash">Carregando…</div>
  if (!session) return <LoginPage />

  // key: ao trocar de conta, todo o estado (documentos, conversas) é recriado do zero.
  return (
    <DocsProvider key={session.id}>
      <Shell />
    </DocsProvider>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <Gate />
    </AuthProvider>
  )
}
