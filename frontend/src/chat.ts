// Estado de uma conversa com o assistente. Usado no cartão da tela inicial e na tela Assistente.

import { useCallback, useState } from "react"
import { api, errorMessage, type ChatMessage, type Conversation } from "./api"

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState("")

  // Devolve o id da conversa quando deu certo (para atualizar listas), ou null se falhou.
  const send = useCallback(
    async (question: string, documentIds?: string[]): Promise<string | null> => {
      setMessages((current) => [...current, { role: "user", content: question }])
      setSending(true)
      setError("")
      try {
        const result = await api.chat({
          question,
          document_ids: documentIds && documentIds.length > 0 ? documentIds : undefined,
          conversation_id: conversationId ?? undefined,
        })
        setConversationId(result.conversation_id)
        setMessages((current) => [
          ...current,
          { role: "assistant", content: result.answer, sources: result.sources },
        ])
        return result.conversation_id
      } catch (err) {
        setError(errorMessage(err))
        return null
      } finally {
        setSending(false)
      }
    },
    [conversationId],
  )

  const reset = useCallback(() => {
    setMessages([])
    setConversationId(null)
    setError("")
  }, [])

  const load = useCallback((conversation: Conversation) => {
    setMessages(conversation.messages)
    setConversationId(conversation.conversation_id)
    setError("")
  }, [])

  return { messages, conversationId, sending, error, send, reset, load }
}
