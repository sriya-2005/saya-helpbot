import { useState, useRef, useEffect } from 'react'
import Sidebar from './components/Sidebar.jsx'
import SearchBar from './components/SearchBar.jsx'
import ChatMessage from './components/ChatMessage.jsx'
import LoadingDots from './components/LoadingDots.jsx'
import SuggestedQuestions from './components/SuggestedQuestions.jsx'
import { SUGGESTED_QUESTIONS } from './data/mockApi.js'
import './App.css'

const WELCOME_MESSAGE = {
  id: 'welcome',
  role: 'bot',
  text: "Hi, I'm SAYA HelpBot. Ask me anything about the SAYA platform — or tap a suggestion below to get started.",
}

const API_BASE = import.meta.env.VITE_API_BASE || ''

export default function App() {
  // --- STATE ---
  // messages: the full conversation, top to bottom, as an array of objects.
  // isLoading: true while we're "waiting" for an answer (drives the typing animation).
  // history: every question the user has actually asked, for the sidebar's History tab.
  const [messages, setMessages] = useState([WELCOME_MESSAGE])
  const [isLoading, setIsLoading] = useState(false)
  const [history, setHistory] = useState([])
  const [faqList, setFaqList] = useState(SUGGESTED_QUESTIONS)

  // A ref gives us a direct handle to a real DOM element (the bottom of the chat)
  // so we can scroll to it whenever a new message arrives.
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  useEffect(() => {
    async function loadSuggestedQuestions() {
      try {
        const response = await fetch(`${API_BASE}/suggested-questions`)
        if (!response.ok) {
          throw new Error(`API returned ${response.status}`)
        }
        const data = await response.json()
        if (Array.isArray(data.questions) && data.questions.length > 0) {
          setFaqList(data.questions)
        }
      } catch (error) {
        console.warn('Could not load suggested questions:', error)
      }
    }

    loadSuggestedQuestions()
  }, [])

  // This is the core function: it runs every time the user asks a question,
  // whether they typed it, clicked a suggestion, FAQ item, or "related question" chip.
  async function handleAsk(question) {
    if (!question.trim() || isLoading) return

    // 1. Immediately show the user's own message (optimistic update — don't wait for the server)
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'user', text: question }])
    setHistory((prev) => [question, ...prev].slice(0, 20))
    setIsLoading(true)

    try {
      const response = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question }),
      })

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`)
      }

      const result = await response.json()

      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'bot',
          text: result.answer || 'Sorry, I could not find an answer.',
          confidence: result.confidence,
          ticketId: result.source,
          related: result.related_questions,
          notFound: result.source === 'NONE',
        },
      ])
    } catch (error) {
      console.error('Ask failed:', error)
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'bot',
          text: 'Sorry, I could not reach the help server. Please try again later.',
          notFound: true,
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  function handleClearChat() {
    setMessages([WELCOME_MESSAGE])
    setHistory([])
  }

  return (
    <div className="app">
      <Sidebar
        faqList={faqList}
        history={history}
        onSelectQuestion={handleAsk}
        onClearChat={handleClearChat}
      />

      <main className="chat-panel">
        <header className="chat-panel__header">
          <div className="status-dot" />
          <span>SAYA HelpBot is online</span>
        </header>

        <div className="chat-panel__messages">
          {messages.map((m) => (
            <ChatMessage
              key={m.id}
              role={m.role}
              text={m.text}
              confidence={m.confidence}
              ticketId={m.ticketId}
              related={m.related}
              notFound={m.notFound}
              onAskRelated={handleAsk}
            />
          ))}

          {isLoading && (
            <div className="message-row message-row--bot">
              <div className="message-bubble message-bubble--bot">
                <LoadingDots />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {messages.length <= 1 && (
          <SuggestedQuestions
            title="Suggested questions"
            questions={faqList}
            onSelect={handleAsk}
          />
        )}

        <SearchBar onSend={handleAsk} disabled={isLoading} />
      </main>
    </div>
  )
}
