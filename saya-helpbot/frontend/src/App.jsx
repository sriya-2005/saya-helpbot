import { useState, useRef, useEffect } from 'react'
import Sidebar from './components/Sidebar.jsx'
import SearchBar from './components/SearchBar.jsx'
import ChatMessage from './components/ChatMessage.jsx'
import LoadingDots from './components/LoadingDots.jsx'
import SuggestedQuestions from './components/SuggestedQuestions.jsx'
import { mockAsk, SUGGESTED_QUESTIONS } from './data/mockApi.js'
import './App.css'

const WELCOME_MESSAGE = {
  id: 'welcome',
  role: 'bot',
  text: "Hi, I'm SAYA HelpBot. Ask me anything about the SAYA platform — or tap a suggestion below to get started.",
}

export default function App() {
  // --- STATE ---
  // messages: the full conversation, top to bottom, as an array of objects.
  // isLoading: true while we're "waiting" for an answer (drives the typing animation).
  // history: every question the user has actually asked, for the sidebar's History tab.
  const [messages, setMessages] = useState([WELCOME_MESSAGE])
  const [isLoading, setIsLoading] = useState(false)
  const [history, setHistory] = useState([])

  // A ref gives us a direct handle to a real DOM element (the bottom of the chat)
  // so we can scroll to it whenever a new message arrives.
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // This is the core function: it runs every time the user asks a question,
  // whether they typed it, clicked a suggestion, FAQ item, or "related question" chip.
  async function handleAsk(question) {
    if (!question.trim() || isLoading) return

    // 1. Immediately show the user's own message (optimistic update — don't wait for the server)
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'user', text: question }])
    setHistory((prev) => [question, ...prev].slice(0, 20))
    setIsLoading(true)

    // 2. Ask the "backend" (mock for now — a real fetch() call replaces this later)
    const result = await mockAsk(question)

    // 3. Turn the backend's response into a bot message and add it to the list
    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: 'bot',
        text: result.found
          ? result.answer
          : "I couldn't find a confident answer to that yet. Here are some questions I do know:",
        confidence: result.found ? result.confidence : undefined,
        ticketId: result.found ? result.id : undefined,
        related: result.related,
        notFound: !result.found,
      },
    ])
    setIsLoading(false)
  }

  function handleClearChat() {
    setMessages([WELCOME_MESSAGE])
    setHistory([])
  }

  return (
    <div className="app">
      <Sidebar
        faqList={SUGGESTED_QUESTIONS}
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
            questions={SUGGESTED_QUESTIONS}
            onSelect={handleAsk}
          />
        )}

        <SearchBar onSend={handleAsk} disabled={isLoading} />
      </main>
    </div>
  )
}
