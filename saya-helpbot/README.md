# SAYA HelpBot (v1)

A chatbot that answers predefined questions about the SAYA platform from an
internal knowledge base, using fuzzy matching (not AI/LLM generation).

## Status: Step 1 of 10 — Frontend only (using mock data)

The backend does not exist yet. Right now, the frontend uses fake data in
`frontend/src/data/mockApi.js` so we can build and test the UI in isolation.

## How to run the frontend

```bash
cd frontend
npm install
npm run dev
```

Then open the URL it prints (usually http://localhost:5173).

## What to check before we move on

- [ ] Does the layout look right (sidebar on the left, chat on the right)?
- [ ] Do the suggested question chips work when clicked?
- [ ] Does typing a question and hitting "Send" show a loading animation, then an answer?
- [ ] Try typing something *not* in the knowledge base (e.g. "asdf") — do you see the
      "no answer found" message with related question suggestions?
- [ ] Does "Clear chat" reset the conversation?
- [ ] Try resizing your browser narrow (or open on your phone) — does it still look OK?

## Project structure so far

```
saya-helpbot/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatMessage.jsx      # one chat bubble
│   │   │   ├── LoadingDots.jsx      # typing animation
│   │   │   ├── SearchBar.jsx        # question input
│   │   │   ├── Sidebar.jsx          # FAQ + history panel
│   │   │   └── SuggestedQuestions.jsx
│   │   ├── data/
│   │   │   └── mockApi.js           # TEMPORARY fake backend, deleted later
│   │   ├── App.jsx                  # main app, holds all state
│   │   ├── App.css                  # component styling
│   │   ├── index.css                # design tokens (colors, fonts, spacing)
│   │   └── main.jsx                 # entry point
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── backend/                          # empty — built in the next step
├── requirements.txt                  # empty — filled in with the backend
└── README.md
```

## Next steps (once you confirm the frontend looks/works right)

5. Build the FastAPI backend (`backend/main.py`, `backend/search.py`)
6. Wait for confirmation
7. Connect frontend to the real backend (delete `mockApi.js`, add a real `fetch()`)
8. Create the 100-question `knowledge.json`
9. Implement fuzzy search properly (using `rapidfuzz`)
10. Polish the UI further based on what we learn from real data
