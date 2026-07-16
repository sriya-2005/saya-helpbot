// "props" is just an object of values passed in from the parent (ChatWindow).
// Destructuring { role, text, ... } pulls specific fields out of that object,
// the same way you'd pull fields out of a JSON response.
export default function ChatMessage({ role, text, confidence, ticketId, related, notFound, onAskRelated }) {
  const isUser = role === 'user'

  return (
    <div className={`message-row ${isUser ? 'message-row--user' : 'message-row--bot'}`}>
      <div className={`message-bubble ${isUser ? 'message-bubble--user' : 'message-bubble--bot'} ${notFound ? 'message-bubble--notfound' : ''}`}>
        {/* Every bot answer gets a small reference number, like a real ledger entry */}
        {!isUser && ticketId && (
          <div className="message-meta">
            <span className="ticket-id">#{ticketId}</span>
            {typeof confidence === 'number' && (
              <span className={`confidence confidence--${confidenceLevel(confidence)}`}>
                {confidence}% match
              </span>
            )}
          </div>
        )}

        {/* whiteSpace: 'pre-line' makes \n in our answer text become real line breaks */}
        <p className="message-text" style={{ whiteSpace: 'pre-line' }}>{text}</p>

        {/* If the bot couldn't find a confident answer, offer related questions to try instead */}
        {!isUser && related && related.length > 0 && (
          <div className="related-box">
            <span className="related-label">
              {notFound ? 'Try one of these instead:' : 'Related questions:'}
            </span>
            <div className="related-chips">
              {related.map((q) => (
                <button key={q} className="chip chip--related" onClick={() => onAskRelated(q)}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// A tiny helper function (not a component) that turns a number into a label,
// so our CSS can color high/medium/low confidence differently.
function confidenceLevel(score) {
  if (score >= 70) return 'high'
  if (score >= 40) return 'medium'
  return 'low'
}
