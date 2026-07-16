import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// ReactDOM.createRoot() grabs the <div id="root"> from index.html
// and tells React "you are now in charge of everything inside this div."
// .render(<App />) then draws our top-level App component into it.
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
