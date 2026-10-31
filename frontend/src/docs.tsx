// Lista de documentos compartilhada entre as telas (upload, exclusão e contagens).

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import { api, errorMessage, type DocumentItem } from "./api"

const MAX_BYTES = 50 * 1024 * 1024

interface DocsContextValue {
  documents: DocumentItem[]
  loading: boolean
  loadError: string
  uploading: string // nome do arquivo sendo processado ("" quando parado)
  uploadError: string
  lastUploaded: DocumentItem | null // último PDF enviado e ainda existente (tela inicial)
  totalPages: number
  refresh: () => Promise<void>
  upload: (file: File) => Promise<void>
  remove: (id: string) => Promise<void>
  clearUploadError: () => void
}

const DocsContext = createContext<DocsContextValue | null>(null)

export function DocsProvider({ children }: { children: ReactNode }) {
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState("")
  const [uploading, setUploading] = useState("")
  const [uploadError, setUploadError] = useState("")
  const [lastUploadedId, setLastUploadedId] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      const data = await api.documents()
      setDocuments(data.documents)
      setLoadError("")
    } catch (error) {
      setLoadError(errorMessage(error))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const upload = useCallback(
    async (file: File) => {
      setUploadError("")
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setUploadError("Envie um arquivo PDF.")
        return
      }
      if (file.size > MAX_BYTES) {
        setUploadError("O PDF ultrapassa o limite de 50 MB.")
        return
      }
      setUploading(file.name)
      try {
        const result = await api.uploadDocument(file)
        setLastUploadedId(result.document.document_id)
        await refresh()
      } catch (error) {
        setUploadError(errorMessage(error))
      } finally {
        setUploading("")
      }
    },
    [refresh],
  )

  const remove = useCallback(async (id: string) => {
    await api.deleteDocument(id)
    setDocuments((current) => current.filter((doc) => doc.document_id !== id))
    setLastUploadedId((current) => (current === id ? null : current))
  }, [])

  const value = useMemo<DocsContextValue>(
    () => ({
      documents,
      loading,
      loadError,
      uploading,
      uploadError,
      lastUploaded: documents.find((doc) => doc.document_id === lastUploadedId) ?? null,
      totalPages: documents.reduce((sum, doc) => sum + (doc.pages ?? 0), 0),
      refresh,
      upload,
      remove,
      clearUploadError: () => setUploadError(""),
    }),
    [documents, loading, loadError, uploading, uploadError, lastUploadedId, refresh, upload, remove],
  )

  return <DocsContext.Provider value={value}>{children}</DocsContext.Provider>
}

export function useDocs(): DocsContextValue {
  const context = useContext(DocsContext)
  if (!context) throw new Error("useDocs precisa estar dentro de <DocsProvider>")
  return context
}
