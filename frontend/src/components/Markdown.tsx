import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

// As respostas da IA vêm em Markdown (negrito, listas, tabelas).
export function Markdown({ children }: { children: string }) {
  return (
    <div className="markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  )
}
