import { useState } from "react"

// O arquivo do logo fica em public/montenai-logo.png.
// Se ele não for encontrado, aparece o nome em texto no lugar.
export function Logo({ className = "brand-logo" }: { className?: string }) {
  const [failed, setFailed] = useState(false)

  if (failed) {
    return (
      <span className="brand-fallback">
        Monten<b>AI</b>
      </span>
    )
  }

  return (
    <img
      alt="MontenAI — Intelligent Document Assistant"
      className={className}
      onError={() => setFailed(true)}
      src="/montenai-logo.png"
    />
  )
}
