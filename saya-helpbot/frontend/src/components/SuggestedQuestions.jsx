// This component just displays a list of strings as clickable buttons.
// `questions` is an array we loop over with .map() — the standard way
// React turns a list of data into a list of UI elements.
export default function SuggestedQuestions({ questions, onSelect, title }) {
  if (!questions || questions.length === 0) return null

  return (
    <div className="suggested">
      <span className="suggested__title">{title}</span>
      <div className="suggested__list">
        {questions.map((q) => (
          <button key={q} className="chip" onClick={() => onSelect(q)}>
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}
