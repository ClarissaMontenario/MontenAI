import { useEffect, useMemo, useState } from "react"
import { api, errorMessage, type Conversation } from "../api"
import { ErrorBanner, PageHeading } from "../components/Common"
import { Icon } from "../components/Icon"
import { useDocs } from "../docs"
import { dayLabel, groupSources, parseDate, timeLabel } from "../util"

function lastActivity(conversation: Conversation): Date {
  return parseDate(conversation.updated_at ?? conversation.created_at) ?? new Date(0)
}

// Deixa a resposta da IA (em Markdown) como uma prévia simples de texto.
function snippet(conversation: Conversation): string {
  const answer = conversation.messages.find((message) => message.role === "assistant")
  if (!answer) return ""
  // Pega só linhas de texto corrido (pula tabelas, divisórias e títulos vazios).
  const firstLines = answer.content
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith("|") && !/^[-=*_\s]{3,}$/.test(line))
    .slice(0, 3)
    .join(" ")
  const text = firstLines
    .replace(/[*_#>`]/g, "")
    .replace(/\s+/g, " ")
    .trim()
  return text.length > 170 ? text.slice(0, 170).trimEnd() + "…" : text
}

export function HistoryPage({ onOpen }: { onOpen: (conversationId: string) => void }) {
  const { documents } = useDocs()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [search, setSearch] = useState("")

  useEffect(() => {
    api
      .history()
      .then((data) => {
        const list = data.conversations
        list.sort((a, b) => lastActivity(b).getTime() - lastActivity(a).getTime())
        setConversations(list)
      })
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [])

  const remove = async (conversation: Conversation) => {
    if (!window.confirm(`Excluir a conversa "${conversation.title}"?`)) return
    try {
      await api.deleteConversation(conversation.conversation_id)
      setConversations((current) =>
        current.filter((item) => item.conversation_id !== conversation.conversation_id),
      )
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  const groups = useMemo(() => {
    const term = search.trim().toLowerCase()
    const result: { label: string; items: Conversation[] }[] = []
    for (const item of conversations) {
      const matches =
        !term ||
        item.title.toLowerCase().includes(term) ||
        item.messages.some((message) => message.content.toLowerCase().includes(term))
      if (!matches) continue
      const label = dayLabel(lastActivity(item))
      const group = result.find((entry) => entry.label === label)
      if (group) group.items.push(item)
      else result.push({ label, items: [item] })
    }
    return result
  }, [conversations, search])

  return (
    <div className="content">
      <PageHeading
        description="Revise suas conversas e perguntas anteriores. Clique em uma para continuar de onde parou."
        title="Histórico"
      />

      <ErrorBanner message={error} onClose={() => setError("")} />

      <section className="history-overview">
        <div className="history-search">
          <Icon name="search" size={20} />
          <input
            aria-label="Buscar no histórico"
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Buscar no histórico..."
            value={search}
          />
        </div>
      </section>

      <section className="timeline">
        {loading ? (
          <p className="empty-state">Carregando seu histórico…</p>
        ) : groups.length === 0 ? (
          <p className="empty-state">
            {conversations.length === 0
              ? "Você ainda não conversou com o assistente. Suas conversas vão aparecer aqui."
              : "Nenhuma conversa encontrada."}
          </p>
        ) : (
          groups.map((group) => (
            <div className="timeline-group" key={group.label}>
              <p className="timeline-day">{group.label}</p>
              <div className="timeline-items">
                {group.items.map((item) => {
                  const sources = groupSources(
                    item.messages.flatMap((message) => message.sources ?? []),
                    documents,
                  )
                  const questions = item.messages.filter((m) => m.role === "user").length
                  return (
                    <div
                      className="timeline-entry"
                      key={item.conversation_id}
                      onClick={() => onOpen(item.conversation_id)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") onOpen(item.conversation_id)
                      }}
                      role="button"
                      tabIndex={0}
                    >
                      <span className="timeline-icon">
                        <Icon name="message" size={22} />
                      </span>
                      <span className="timeline-copy">
                        <span className="timeline-meta">
                          <i>Conversa</i>
                          <small>
                            {timeLabel(lastActivity(item))} · {questions}{" "}
                            {questions === 1 ? "pergunta" : "perguntas"}
                          </small>
                        </span>
                        <strong>{item.title}</strong>
                        {snippet(item) && <p>{snippet(item)}</p>}
                        {sources.length > 0 && (
                          <span className="timeline-docs">
                            {sources.slice(0, 3).map((source) => (
                              <span className="timeline-document" key={source.documentId}>
                                <Icon name="pdf" size={15} />
                                {source.name}
                              </span>
                            ))}
                          </span>
                        )}
                      </span>
                      <button
                        aria-label="Excluir conversa"
                        className="row-delete"
                        onClick={(event) => {
                          event.stopPropagation()
                          void remove(item)
                        }}
                        title="Excluir conversa"
                        type="button"
                      >
                        <Icon name="trash" size={19} />
                      </button>
                      <span className="timeline-arrow">
                        <Icon name="chevron" size={20} />
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          ))
        )}
      </section>
    </div>
  )
}
