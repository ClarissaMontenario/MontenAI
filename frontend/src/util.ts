import type { DocumentItem, Source } from "./api"

// O back end manda datas sem fuso (UTC). Sem o "Z" o navegador leria como hora local.
export function parseDate(value?: string | null): Date | null {
  if (!value) return null
  const hasZone = /(Z|[+-]\d{2}:?\d{2})$/.test(value)
  const date = new Date(hasZone ? value : value + "Z")
  return Number.isNaN(date.getTime()) ? null : date
}

function startOfDay(date: Date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()
}

export function dayLabel(date: Date): string {
  const diff = Math.round((startOfDay(new Date()) - startOfDay(date)) / 86_400_000)
  if (diff === 0) return "Hoje"
  if (diff === 1) return "Ontem"
  return date.toLocaleDateString("pt-BR", { day: "numeric", month: "long" })
}

export function timeLabel(date: Date): string {
  return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
}

export function relativeLabel(date: Date): string {
  const minutes = Math.floor((Date.now() - date.getTime()) / 60_000)
  if (minutes < 1) return "agora"
  if (minutes < 60) return `há ${minutes} min`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `há ${hours} ${hours === 1 ? "hora" : "horas"}`
  const label = dayLabel(date)
  return label === "Ontem" ? "ontem" : label
}

export function dateTimeLabel(date: Date): string {
  return `${dayLabel(date)}, ${timeLabel(date)}`
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return "?"
  const first = parts[0][0]
  const last = parts.length > 1 ? parts[parts.length - 1][0] : ""
  return (first + last).toUpperCase()
}

export function pagesLabel(pages: number | null): string {
  if (pages == null) return "—"
  return `${pages} ${pages === 1 ? "página" : "páginas"}`
}

// O índice guarda o nome com prefixos técnicos (ids). Tira tudo até o UUID.
export function cleanDocName(stored: string): string {
  return stored.replace(/^.*?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_/i, "")
}

export interface SourceGroup {
  documentId: string
  name: string
  pages: number[]
}

// Junta as fontes de uma resposta por documento: "Relatório · páginas 2, 5, 8".
export function groupSources(sources: Source[], documents: DocumentItem[]): SourceGroup[] {
  const groups = new Map<string, SourceGroup>()
  for (const source of sources) {
    const known = documents.find((doc) => doc.document_id === source.document_id)
    const name = known?.name ?? cleanDocName(source.document)
    const group = groups.get(source.document_id) ?? {
      documentId: source.document_id,
      name,
      pages: [],
    }
    if (source.page != null && !group.pages.includes(source.page)) group.pages.push(source.page)
    groups.set(source.document_id, group)
  }
  return [...groups.values()].map((group) => ({
    ...group,
    pages: [...group.pages].sort((a, b) => a - b),
  }))
}

export function pagesRange(pages: number[]): string {
  if (pages.length === 0) return "Documento inteiro"
  return `${pages.length === 1 ? "Página" : "Páginas"} ${pages.join(", ")}`
}
