import Link from 'next/link'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'AISilicons — AI Co-pilot for Product Managers',
}

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-gray-950 text-white">
      {/* Hero */}
      <section className="flex flex-col items-center justify-center min-h-[80vh] px-6 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 mb-6 text-sm bg-gray-800 rounded-full border border-gray-700">
          <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          v1.0 Foundation — Now available
        </div>

        <img src="/logo.png" alt="AISilicons" className="w-24 h-24 mb-6 rounded-2xl object-cover" />
        <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
          AISilicons
        </h1>

        <p className="text-xl md:text-2xl text-gray-400 max-w-2xl mb-4">
          Your AI co-pilot for Product Management
        </p>

        <p className="text-gray-500 max-w-xl mb-10">
          Score features, write PRDs, manage Epics, detect conflicts, track stakeholders.
          Plain language. Files you own.
        </p>

        <div className="flex flex-col sm:flex-row gap-4">
          <Link
            href="/chat"
            className="px-8 py-3 bg-white text-gray-900 font-semibold rounded-lg hover:bg-gray-100 transition"
          >
            Open Chat →
          </Link>
          <Link
            href="/projects"
            className="px-8 py-3 bg-gray-800 text-white font-semibold rounded-lg border border-gray-700 hover:bg-gray-700 transition"
          >
            View Projects
          </Link>
        </div>
      </section>

      {/* Strengths */}
      <section className="py-20 px-6 border-t border-gray-800">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Why it works</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {STRENGTHS.map((s) => (
              <div key={s.title} className="p-6 bg-gray-900 rounded-xl border border-gray-800">
                <div className="text-2xl mb-3">{s.icon}</div>
                <h3 className="text-lg font-semibold mb-2">{s.title}</h3>
                <p className="text-gray-400 text-sm">{s.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Quick commands */}
      <section className="py-20 px-6 border-t border-gray-800">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">Just type what you need</h2>
          <p className="text-gray-400 mb-10">The AI does the PM work</p>
          <div className="space-y-3 text-left">
            {COMMANDS.map((c) => (
              <div key={c.cmd} className="flex gap-4 p-4 bg-gray-900 rounded-lg border border-gray-800">
                <code className="text-green-400 text-sm flex-1">{c.cmd}</code>
                <span className="text-gray-400 text-sm">{c.result}</span>
              </div>
            ))}
          </div>
          <Link href="/chat" className="inline-block mt-8 px-8 py-3 bg-white text-gray-900 font-semibold rounded-lg hover:bg-gray-100 transition">
            Start now →
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-gray-800 text-center text-gray-500 text-sm">
        AISilicons · MIT License ·{' '}
        <a href="https://github.com/taman-spirit/product-skill-jev" className="hover:text-white transition">
          GitHub
        </a>
      </footer>
    </main>
  )
}

const STRENGTHS = [
  {
    icon: '🔗',
    title: 'Document coherence',
    description: 'Every FR, PRD, Epic, CR links to each other. When something changes, the AI knows what else to update.',
  },
  {
    icon: '📋',
    title: 'Stakeholder profiles',
    description: 'The AI remembers each stakeholder\'s style. Add feedback and it scans all documents, suggests updates, and asks before changing anything.',
  },
  {
    icon: '🔒',
    title: 'Immutable history',
    description: 'Approved documents are locked forever. Changes create new versions. Every decision is logged. Nothing is lost.',
  },
  {
    icon: '⚡',
    title: 'Conflict detection',
    description: 'Before any CR or PRD update, optionally scan for tag collisions and milestone risks across the full project.',
  },
  {
    icon: '📱',
    title: 'Works everywhere',
    description: 'Web UI on desktop and mobile. Telegram bot for on-the-go. Same workspace, always in sync.',
  },
  {
    icon: '🤖',
    title: 'Your AI, your keys',
    description: 'Use Anthropic Claude (recommended), Groq (free), Gemini, OpenAI, or local Ollama. You control the provider.',
  },
]

const COMMANDS = [
  { cmd: '"Create a new project for checkout redesign"', result: 'Full project structure created' },
  { cmd: '"Create a feature request for dark mode"', result: 'AI interviews you, writes FR' },
  { cmd: '"Score FR-001 with RICE"', result: '4 questions → priority score + formula' },
  { cmd: '"Create PRD for FR-001"', result: 'Full PRD written automatically' },
  { cmd: '"Add feedback from Sarah - concerned about timeline"', result: 'Saves feedback, scans docs, suggests updates' },
]
