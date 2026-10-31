import type { ReactNode } from "react"
import { Icon } from "./Icon"

export function PageHeading({
  title,
  description,
  action,
}: {
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <section className="page-heading">
      <div>
        <p className="page-title">{title}</p>
        <p className="page-subtitle">{description}</p>
      </div>
      {action}
    </section>
  )
}

export function ErrorBanner({ message, onClose }: { message: string; onClose?: () => void }) {
  if (!message) return null
  return (
    <div className="banner error" role="alert">
      <Icon name="alert" size={20} />
      <span>{message}</span>
      {onClose && (
        <button aria-label="Fechar aviso" onClick={onClose} type="button">
          <Icon name="x" size={16} />
        </button>
      )}
    </div>
  )
}

const TONES = ["violet", "blue", "lavender"] as const

// Cor do ícone de cada PDF: estável (sempre a mesma para o mesmo documento).
export function toneFor(id: string): (typeof TONES)[number] {
  let sum = 0
  for (const char of id) sum += char.charCodeAt(0)
  return TONES[sum % TONES.length]
}

export function DocIcon({ id, size = 22 }: { id: string; size?: number }) {
  return (
    <span className={`document-icon ${toneFor(id)}`}>
      <Icon name="pdf" size={size} />
      <small>PDF</small>
    </span>
  )
}
