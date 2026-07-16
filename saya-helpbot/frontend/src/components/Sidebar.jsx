import { useState } from 'react'

// This sidebar has two "tabs": the FAQ list, and the history of what
// you've already asked. `activeTab` is local state — it only matters
// inside this component, so it doesn't need to live in App.jsx.
export default function Sidebar({ faqList, history, onSelectQuestion, onClearChat }) {
  const [activeTab, setActiveTab] = useState('faq')

  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <div className="sidebar__logo">SAYA</div>
        <div className="sidebar__brand-text">
          <span className="sidebar__title">HelpBot</span>
          <span className="sidebar__subtitle">Internal knowledge base · v1</span>
        </div>
      </div>

      <div className="sidebar__tabs">
        <button
          className={`sidebar__tab ${activeTab === 'faq' ? 'sidebar__tab--active' : ''}`}
          onClick={() => setActiveTab('faq')}
        >
          FAQ
        </button>
        <button
          className={`sidebar__tab ${activeTab === 'history' ? 'sidebar__tab--active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          History
        </button>
      </div>

      <div className="sidebar__content">
        {activeTab === 'faq' && (
          <ul className="sidebar__list">
            {faqList.map((q) => (
              <li key={q}>
                <button className="sidebar__list-item" onClick={() => onSelectQuestion(q)}>
                  {q}
                </button>
              </li>
            ))}
          </ul>
        )}

        {activeTab === 'history' && (
          <>
            {history.length === 0 ? (
              <p className="sidebar__empty">Questions you ask will show up here.</p>
            ) : (
              <ul className="sidebar__list">
                {history.map((q, i) => (
                  <li key={`${q}-${i}`}>
                    <button className="sidebar__list-item" onClick={() => onSelectQuestion(q)}>
                      {q}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>

      <button className="sidebar__clear" onClick={onClearChat}>
        Clear chat
      </button>
    </aside>
  )
}
