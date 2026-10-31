import { useEffect, useRef } from "react"
import type { ChatMessage, DocumentItem } from "../api"
import { groupSources, pagesRange } from "../util"
import { Icon } from "./Icon"
import { Markdown } from "./Markdown"

interface Props {
  messages: ChatMessage[]
  sending: boolean
  error?: string
  documents: DocumentItem[]
  compact?: boolean // versão menor, usada no cartão da tela inicial
}

export function ChatThread({ messages, sending, error, documents, compact = false }: Props) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" })
  }, [messages.length, sending, error])

  return (
    <div className={`thread ${compact ? "compact" : ""}`}>
      {messages.map((message, index) => {
        if (message.role === "user") {
          return (
            <div className="msg-user" key={index}>
              {message.content}
            </div>
          )
        }
        const sources = groupSources(message.sources ?? [], documents)
        return (
          <div className="msg-ai-row" key={index}>
            <span className="ai-avatar">
              <Icon name="sparkles" size={compact ? 15 : 18} />
            </span>
            <div className="msg-ai">
              <Markdown>{message.content}</Markdown>
              {sources.length > 0 && (
                <div className="source-list">
                  {sources.map((source) => (
                    <span className="source-chip" key={source.documentId}>
                      <Icon name="pdf" size={15} />
                      <strong>{source.name}</strong>
                      <small>{pagesRange(source.pages)}</small>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )
      })}

      {sending && (
        <div className="msg-ai-row">
          <span className="ai-avatar">
            <Icon name="sparkles" size={compact ? 15 : 18} />
          </span>
          <div className="msg-ai typing" aria-label="Analisando seus documentos">
            <i />
            <i />
            <i />
            <span>Analisando seus documentos…</span>
          </div>
        </div>
      )}

      {error && (
        <div className="thread-error" role="alert">
          <Icon name="alert" size={18} />
          {error}
        </div>
      )}
      <div ref={endRef} />
    </div>
  )
}
