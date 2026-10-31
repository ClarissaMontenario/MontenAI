import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { api, type Conversation } from "../api"
import { useChat } from "../chat"
import { ChatThread } from "../components/ChatThread"
import { PageHeading } from "../components/Common"
import { Icon } from "../components/Icon"
import { useDocs } from "../docs"
import { dayLabel, parseDate, relativeLabel } from "../util"

interface Props {
  initialConversationId: string | null // vem do Histórico ao clicar numa conversa
  onInitialConsumed: () => void
}

function lastActivity(conversation: Conversation): Date {
  return parseDate(conversation.updated_at ?? conversation.created_at) ?? new Date(0)
}

export function AssistantPage({ initialConversationId, onInitialConsumed }: Props) {
  const docs = useDocs()
  const chat = useChat()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [search, setSearch] = useState("")
  const [question, setQuestion] = useState("")
  const [localError, setLocalError] = useState("")
  const [selected, setSelected] = useState<string[] | null>(null) // null = todos

  const allIds = useMemo(() => docs.documents.map((doc) => doc.document_id), [docs.documents])
  const activeIds = selected ? selected.filter((id) => allIds.includes(id)) : allIds

  const loadList = useCallback(async (): Promise<Conversation[]> => {
    try {
      const { conversations: list } = await api.history()
      list.sort((a, b) => lastActivity(b).getTime() - lastActivity(a).getTime())
      setConversations(list)
      return list
    } catch {
      return []
    }
  }, [])

  const { load } = chat
  useEffect(() => {
    void loadList().then((list) => {
      if (!initialConversationId) return
      const target = list.find((item) => item.conversation_id === initialConversationId)
      if (target) load(target)
      onInitialConsumed()
    })
    // roda só ao abrir a tela
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const current = conversations.find((item) => item.conversation_id === chat.conversationId)

  const toggleDoc = (id: string) => {
    setSelected(activeIds.includes(id) ? activeIds.filter((item) => item !== id) : [...activeIds, id])
  }

  const submit = async (text = question) => {
    const trimmed = text.trim()
    if (!trimmed || chat.sending) return
    if (activeIds.length === 0) {
      setLocalError("Envie e selecione pelo menos um documento para conversar.")
      return
    }
    setLocalError("")
    setQuestion("")
    const id = await chat.send(trimmed, activeIds)
    if (id) void loadList()
  }

  const removeConversation = async (id: string) => {
    if (!window.confirm("Excluir esta conversa?")) return
    try {
      await api.deleteConversation(id)
      if (chat.conversationId === id) chat.reset()
      await loadList()
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Não foi possível excluir a conversa.")
    }
  }

  const grouped = useMemo(() => {
    const term = search.trim().toLowerCase()
    const groups: { label: string; items: Conversation[] }[] = []
    for (const item of conversations) {
      if (term && !item.title.toLowerCase().includes(term)) continue
      const label = dayLabel(lastActivity(item))
      const group = groups.find((entry) => entry.label === label)
      if (group) group.items.push(item)
      else groups.push({ label, items: [item] })
    }
    return groups
  }, [conversations, search])

  const startNew = () => {
    chat.reset()
    setLocalError("")
  }

  const starters = [
    { icon: "files" as const, text: "Resuma os principais pontos" },
    { icon: "search" as const, text: "Encontre riscos e pontos de atenção" },
    { icon: "sparkles" as const, text: "Compare os dados entre os documentos" },
  ]

  return (
    <div className="content">
      <PageHeading
        action={
          <button className="new-document" onClick={startNew} type="button">
            <Icon name="plus" size={20} />
            Nova conversa
          </button>
        }
        description="Converse com seus documentos, encontre respostas e transforme informação em conhecimento."
        title="Assistente MontenAI"
      />

      <section className="assistant-workspace">
        <aside className="conversation-panel">
          <div className="panel-label">
            <p>Conversas</p>
            <button aria-label="Nova conversa" onClick={startNew} type="button">
              <Icon name="plus" size={18} />
            </button>
          </div>
          <div className="conversation-search">
            <Icon name="search" size={18} />
            <input
              aria-label="Buscar conversas"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Buscar conversas"
              value={search}
            />
          </div>

          {grouped.length === 0 && (
            <p className="panel-empty">
              {conversations.length === 0
                ? "Suas conversas vão aparecer aqui."
                : "Nenhuma conversa encontrada."}
            </p>
          )}

          {grouped.map((group) => (
            <div className="conversation-group" key={group.label}>
              <span>{group.label}</span>
              {group.items.map((item) => (
                <div
                  className={`conversation-item ${
                    item.conversation_id === chat.conversationId ? "selected" : ""
                  }`}
                  key={item.conversation_id}
                  onClick={() => chat.load(item)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") chat.load(item)
                  }}
                  role="button"
                  tabIndex={0}
                >
                  <Icon name="message" size={18} />
                  <span>
                    <strong>{item.title}</strong>
                    <small>{relativeLabel(lastActivity(item))}</small>
                  </span>
                  <button
                    aria-label="Excluir conversa"
                    className="conversation-delete"
                    onClick={(event) => {
                      event.stopPropagation()
                      void removeConversation(item.conversation_id)
                    }}
                    type="button"
                  >
                    <Icon name="trash" size={16} />
                  </button>
                </div>
              ))}
            </div>
          ))}
        </aside>

        <div className="full-chat">
          <div className="full-chat-header">
            <div>
              <p>{current?.title ?? "Nova conversa"}</p>
              <span>
                {activeIds.length} {activeIds.length === 1 ? "documento" : "documentos"} em contexto
              </span>
            </div>
            <div className="context-docs">
              {docs.documents.map((doc) => (
                <button
                  className={activeIds.includes(doc.document_id) ? "on" : ""}
                  key={doc.document_id}
                  onClick={() => toggleDoc(doc.document_id)}
                  title={
                    activeIds.includes(doc.document_id)
                      ? "Clique para tirar do contexto"
                      : "Clique para usar este documento"
                  }
                  type="button"
                >
                  <Icon name={activeIds.includes(doc.document_id) ? "check" : "pdf"} size={15} />
                  {doc.name}
                </button>
              ))}
            </div>
          </div>

          <div className="full-chat-messages">
            {chat.messages.length === 0 && (
              <div className="starter-prompts">
                <div>
                  <span className="ai-avatar">
                    <Icon name="sparkles" size={16} />
                  </span>
                  <p>
                    <strong>Como posso ajudar?</strong>
                    <small>
                      {docs.documents.length === 0
                        ? "Envie um PDF na tela inicial ou em Meus documentos para começar."
                        : "Experimente uma destas perguntas para começar."}
                    </small>
                  </p>
                </div>
                {docs.documents.length > 0 && (
                  <div className="starter-prompt-grid">
                    {starters.map((item) => (
                      <button key={item.text} onClick={() => setQuestion(item.text)} type="button">
                        <Icon name={item.icon} size={18} />
                        {item.text}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            <ChatThread
              documents={docs.documents}
              error={chat.error || localError}
              messages={chat.messages}
              sending={chat.sending}
            />
          </div>

          <div className="full-chat-composer">
            <button
              aria-label="Adicionar documento"
              onClick={() => fileInputRef.current?.click()}
              title="Enviar um novo PDF"
              type="button"
            >
              <Icon name="plus" size={20} />
            </button>
            <input
              accept="application/pdf"
              className="hidden-input"
              onChange={(event) => {
                const file = event.target.files?.[0]
                if (file) void docs.upload(file)
                event.target.value = ""
              }}
              ref={fileInputRef}
              type="file"
            />
            <input
              aria-label="Nova pergunta"
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") void submit()
              }}
              placeholder="Faça uma pergunta sobre seus documentos..."
              value={question}
            />
            <span>
              {activeIds.length} {activeIds.length === 1 ? "documento" : "documentos"}
            </span>
            <button
              aria-label="Enviar pergunta"
              className="composer-send"
              disabled={chat.sending || !question.trim()}
              onClick={() => void submit()}
              type="button"
            >
              <Icon name="arrow-up" size={20} />
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}
