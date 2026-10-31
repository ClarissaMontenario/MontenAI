import { useEffect, useMemo, useRef, useState } from "react"
import { api } from "../api"
import { DocIcon, ErrorBanner, PageHeading } from "../components/Common"
import { Icon } from "../components/Icon"
import { useDocs } from "../docs"
import { useDeleteDoc } from "../useDeleteDoc"
import { dateTimeLabel, pagesLabel, parseDate } from "../util"

export function DocumentsPage() {
  const docs = useDocs()
  const del = useDeleteDoc()
  const uploadRef = useRef<HTMLInputElement>(null)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("Todos")
  const [conversationCount, setConversationCount] = useState<number | null>(null)

  useEffect(() => {
    api
      .history()
      .then((data) => setConversationCount(data.conversations.length))
      .catch(() => setConversationCount(null))
  }, [])

  const statuses = useMemo(
    () => ["Todos", ...new Set(docs.documents.map((doc) => doc.status))],
    [docs.documents],
  )

  const visible = docs.documents.filter(
    (doc) =>
      doc.name.toLowerCase().includes(search.toLowerCase()) &&
      (statusFilter === "Todos" || doc.status === statusFilter),
  )

  const busy = docs.uploading !== ""

  return (
    <div className="content">
      <PageHeading
        action={
          <button
            className="new-document"
            disabled={busy}
            onClick={() => uploadRef.current?.click()}
            type="button"
          >
            <Icon name="upload" size={20} />
            {busy ? "Processando…" : "Enviar documento"}
          </button>
        }
        description="Organize, consulte e acompanhe todos os seus arquivos."
        title="Meus documentos"
      />
      <input
        accept="application/pdf"
        className="hidden-input"
        onChange={(event) => {
          const file = event.target.files?.[0]
          if (file) void docs.upload(file)
          event.target.value = ""
        }}
        ref={uploadRef}
        type="file"
      />

      <ErrorBanner
        message={docs.uploadError || docs.loadError || del.error}
        onClose={() => {
          docs.clearUploadError()
          del.clearError()
        }}
      />
      {busy && (
        <div className="banner info">
          <span className="spinner small" />
          Processando {docs.uploading}… isso pode levar alguns instantes.
        </div>
      )}

      <section className="library-summary">
        <div>
          <span className="summary-icon purple">
            <Icon name="files" size={22} />
          </span>
          <p>
            <strong>{docs.documents.length}</strong>
            <small>Documentos</small>
          </p>
        </div>
        <div>
          <span className="summary-icon blue">
            <Icon name="pages" size={22} />
          </span>
          <p>
            <strong>{docs.totalPages}</strong>
            <small>Páginas</small>
          </p>
        </div>
        <div>
          <span className="summary-icon green">
            <Icon name="message" size={22} />
          </span>
          <p>
            <strong>{conversationCount ?? "—"}</strong>
            <small>Conversas</small>
          </p>
        </div>
      </section>

      <section className="library-card">
        <div className="library-toolbar">
          <div className="library-search">
            <Icon name="search" size={20} />
            <input
              aria-label="Buscar documentos"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Buscar por nome do documento..."
              value={search}
            />
          </div>
          {statuses.length > 2 && (
            <div className="filter-group">
              {statuses.map((filter) => (
                <button
                  className={statusFilter === filter ? "active" : ""}
                  key={filter}
                  onClick={() => setStatusFilter(filter)}
                  type="button"
                >
                  {filter}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="documents-table">
          <div className="table-header">
            <span>Documento</span>
            <span>Data de envio</span>
            <span>Páginas</span>
            <span>Status</span>
            <span />
          </div>

          {docs.loading ? (
            <p className="empty-state">Carregando seus documentos…</p>
          ) : visible.length === 0 ? (
            <p className="empty-state">
              {docs.documents.length === 0
                ? "Nenhum documento ainda. Use o botão “Enviar documento” para começar."
                : "Nenhum documento encontrado com esses filtros."}
            </p>
          ) : (
            visible.map((doc) => {
              const date = parseDate(doc.uploaded_at)
              return (
                <div className="table-row" key={doc.document_id}>
                  <span className="table-document">
                    <DocIcon id={doc.document_id} size={24} />
                    <span>
                      <strong>{doc.name}</strong>
                      <small>PDF</small>
                    </span>
                  </span>
                  <span>{date ? dateTimeLabel(date) : "Nesta sessão"}</span>
                  <span>{pagesLabel(doc.pages)}</span>
                  <span>
                    <i className={`status-pill ${doc.status === "Temporário" ? "processing" : ""}`}>
                      <b />
                      {doc.status}
                    </i>
                  </span>
                  <button
                    aria-label={`Excluir ${doc.name}`}
                    className="row-delete"
                    disabled={del.busyId === doc.document_id}
                    onClick={() => void del.ask(doc)}
                    title="Excluir documento"
                    type="button"
                  >
                    <Icon name="trash" size={20} />
                  </button>
                </div>
              )
            })
          )}
        </div>
      </section>
    </div>
  )
}
