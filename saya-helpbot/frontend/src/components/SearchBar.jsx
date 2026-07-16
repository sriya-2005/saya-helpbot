import { useState } from 'react'

// useState is a React "hook" — it gives a component memory.
// `value` is the current text in the box; `setValue` is the only way to change it.
// Every time setValue runs, React automatically redraws the component with the new value.
export default function SearchBar({ onSend, disabled }) {
  const [value, setValue] = useState('')

  function handleSubmit(e) {
    e.preventDefault() // stop the browser from doing a full page reload on submit
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed) // hand the question up to the parent component (App.jsx)
    setValue('')     // clear the box
  }

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <input
        type="text"
        className="search-bar__input"
        placeholder="Ask about SAYA… e.g. How do I create a reconciliation?"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
        aria-label="Ask SAYA HelpBot a question"
      />
      <button type="submit" className="search-bar__send" disabled={disabled || !value.trim()}>
        Send
      </button>
    </form>
  )
}
