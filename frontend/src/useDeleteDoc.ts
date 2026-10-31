import { useCallback, useState } from "react"
import { errorMessage, type DocumentItem } from "./api"
import { useDocs } from "./docs"

// Pede confirmação e exclui o documento (do índice, do banco e do disco).
export function useDeleteDoc() {
  const { remove } = useDocs()
  const [busyId, setBusyId] = useState<string | null>(null)
  const [error, setError] = useState("")

  const ask = useCallback(
    async (doc: DocumentItem) => {
      const confirmed = window.confirm(
        `Excluir "${doc.name}"?\n\nO documento sairá da sua biblioteca e deixará de ser usado nas respostas do assistente.`,
      )
      if (!confirmed) return
      setBusyId(doc.document_id)
      setError("")
      try {
        await remove(doc.document_id)
      } catch (err) {
        setError(errorMessage(err))
      } finally {
        setBusyId(null)
      }
    },
    [remove],
  )

  return { busyId, error, ask, clearError: () => setError("") }
}
