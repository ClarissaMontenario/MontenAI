import { useRef, useState, type DragEvent } from "react"
import { useAuth } from "../auth"
import type { useChat } from "../chat"
import { ChatThread } from "../components/ChatThread"
import { DocIcon, ErrorBanner } from "../components/Common"
import { Icon } from "../components/Icon"
import { useDocs } from "../docs"
import type { NavKey } from "../nav"
import { useDeleteDoc } from "../useDeleteDoc"
import { pagesLabel, parseDate, relativeLabel } from "../util"

type ChatState = ReturnType<typeof useChat>

export function HomePage({ chat, goTo }: { chat: ChatState; goTo: (key: NavKey) => void }) {
  const { session } = useAuth()
  const docs = useDocs()
  const del = useDeleteDoc()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [question, setQuestion] = useState("")

  const firstName = session?.user?.name.split(" ")[0]
  const uploaded = docs.lastUploaded
  const busy = docs.uploading !== ""
  const hasDocs = docs.documents.length > 0
  const recent = docs.documents.slice(0, 5)

  const pickFile = (file?: File) => {
    if (file) void docs.upload(file)
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragging(false)
    if (!busy) pickFile(event.dataTransfer.files[0])
  }

  const ask = async () => {
    const text = question.trim()
    if (!text || chat.sending || !hasDocs) return
    setQuestion("")
    await chat.send(
      text,
      docs.documents.map((doc) => doc.document_id),
    )
  }

  return (
    <div className="content">
      <section className="welcome">
        <div>
          <p className="welcome-title">
            Olá, {firstName ?? "visitante"} <span>✦</span>
          </p>
          <p className="welcome-subtitle">
            Transforme documentos complexos em conhecimento claro e acionável.
          </p>
        </div>
        <button
          className="new-document"
          disabled={busy}
          onClick={() => fileInputRef.current?.click()}
          type="button"
        >
          <Icon name="plus" size={20} />
          Novo documento
        </button>
      </section>

      <input
        accept="application/pdf"
        className="hidden-input"
        onChange={(event) => {
          pickFile(event.target.files?.[0])
          event.target.value = "" // permite escolher o mesmo arquivo de novo depois
        }}
        ref={fileInputRef}
        type="file"
      />

      <section className="dashboard-grid">
        <div className="main-column">
          <div
            className={`upload-card ${dragging ? "dragging" : ""} ${uploaded ? "uploaded" : ""}`}
            onDragEnter={(event) => {
              event.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDragOver={(event) => event.preventDefault()}
            onDrop={handleDrop}
          >
            <div className="upload-orb">
              <div className="upload-orb-inner">
                {busy ? (
                  <span className="spinner" />
                ) : uploaded ? (
                  <Icon name="check" size={30} />
                ) : (
                  <Icon name="upload" size={30} />
                )}
              </div>
            </div>

            <div className="upload-copy">
              <p className="upload-title">
                {busy
                  ? `Processando ${docs.uploading}…`
                  : uploaded
                    ? `${uploaded.name} está pronto`
                    : "Envie um documento para começar"}
              </p>
              <p className="upload-subtitle">
                {busy
                  ? "Estamos lendo e indexando o documento. PDFs digitalizados levam um pouco mais."
                  : uploaded
                    ? `${pagesLabel(uploaded.pages)} · já pode fazer perguntas ao assistente`
                    : "Arraste e solte seu PDF aqui ou selecione um arquivo"}
              </p>
            </div>

            {!busy && (
              <div className="upload-actions">
                {uploaded && (
                  <button
                    className="danger-button"
                    disabled={del.busyId === uploaded.document_id}
                    onClick={() => void del.ask(uploaded)}
                    type="button"
                  >
                    <Icon name="trash" size={18} />
                    Excluir arquivo
                  </button>
                )}
                <button
                  className="select-file"
                  onClick={() => fileInputRef.current?.click()}
                  type="button"
                >
                  {uploaded ? "Enviar outro PDF" : "Selecionar PDF"}
                </button>
              </div>
            )}

            <p className="upload-note">PDF · Máximo de 50 MB</p>
            {docs.uploadError && (
              <p className="upload-error" role="alert">
                {docs.uploadError}
              </p>
            )}
          </div>

          <div className="section-heading">
            <div>
              <p className="section-title">Documentos recentes</p>
              <p className="section-description">Continue de onde parou</p>
            </div>
            <button className="text-action" onClick={() => goTo("Meus documentos")} type="button">
              Ver todos
              <Icon name="chevron" size={17} />
            </button>
          </div>

          <ErrorBanner message={docs.loadError || del.error} onClose={del.clearError} />

          <div className="document-list">
            {docs.loading ? (
              <p className="empty-state">Carregando seus documentos…</p>
            ) : recent.length === 0 ? (
              <p className="empty-state">
                Você ainda não enviou nenhum documento. Envie um PDF acima para começar.
              </p>
            ) : (
              recent.map((doc) => {
                const date = parseDate(doc.uploaded_at)
                return (
                  <div className="document-row" key={doc.document_id}>
                    <DocIcon id={doc.document_id} />
                    <span className="document-info">
                      <strong>{doc.name}</strong>
                      <small>
                        {pagesLabel(doc.pages)} · {date ? relativeLabel(date) : "nesta sessão"}
                      </small>
                    </span>
                    <button
                      aria-label={`Excluir ${doc.name}`}
                      className="row-delete"
                      disabled={del.busyId === doc.document_id}
                      onClick={() => void del.ask(doc)}
                      title="Excluir documento"
                      type="button"
                    >
                      <Icon name="trash" size={19} />
                    </button>
                  </div>
                )
              })
            )}
          </div>
        </div>

        <div className="side-column">
          <div className="assistant-card">
            <div className="assistant-glow" />
            <div className="assistant-heading">
              <div className="ai-mark">
                <Icon name="sparkles" size={21} />
              </div>
              <div>
                <p>Assistente MontenAI</p>
                <span>
                  <i /> Online
                </span>
              </div>
            </div>

            <div className="assistant-content">
              <div className="msg-ai-row">
                <span className="ai-avatar">
                  <Icon name="sparkles" size={15} />
                </span>
                <div className="msg-ai">
                  <p>
                    Olá, {firstName ?? "visitante"}! Posso resumir, traduzir ou encontrar
                    informações em seus documentos.
                  </p>
                </div>
              </div>

              <ChatThread
                compact
                documents={docs.documents}
                error={chat.error}
                messages={chat.messages}
                sending={chat.sending}
              />

              {chat.messages.length === 0 && (
                <div className="suggestions">
                  <button
                    disabled={!hasDocs}
                    onClick={() => setQuestion("Resuma os principais pontos dos meus documentos")}
                    type="button"
                  >
                    Resumir um documento
                  </button>
                  <button
                    disabled={!hasDocs}
                    onClick={() => setQuestion("Traduza o conteúdo principal para o inglês")}
                    type="button"
                  >
                    Traduzir para inglês
                  </button>
                </div>
              )}
            </div>

            <div className="chat-input">
              <input
                aria-label="Mensagem para o assistente"
                disabled={!hasDocs}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") void ask()
                }}
                placeholder={
                  hasDocs ? "Pergunte sobre seus documentos..." : "Envie um PDF para começar"
                }
                type="text"
                value={question}
              />
              <button
                aria-label="Enviar mensagem"
                disabled={!hasDocs || chat.sending || !question.trim()}
                onClick={() => void ask()}
                type="button"
              >
                <Icon name="arrow-up" size={19} />
              </button>
            </div>
          </div>

          <div className="insights">
            <div className="stat-card">
              <div className="stat-icon purple">
                <Icon name="check" size={21} />
              </div>
              <div className="stat-copy">
                <p>{docs.documents.length}</p>
                <span>Documentos processados</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon blue">
                <Icon name="pages" size={21} />
              </div>
              <div className="stat-copy">
                <p>{docs.totalPages}</p>
                <span>Páginas analisadas</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
