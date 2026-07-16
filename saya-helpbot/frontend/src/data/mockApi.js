// ============================================
// TEMPORARY MOCK API
// This file pretends to be our backend so we can build and test
// the frontend before the real Python/FastAPI server exists.
// In a later step, we delete this file and replace it with a real
// fetch() call to our FastAPI server.
// ============================================

const MOCK_QA = [
  {
    id: 'SAYA-0147',
    question: 'How do I create a reconciliation?',
    answer:
      '1. Open ReconX.\n2. Click New Reconciliation.\n3. Upload the files.\n4. Configure matching rules.\n5. Run reconciliation.\n6. Review the results.',
  },
  {
    id: 'SAYA-0032',
    question: 'What is ReconX?',
    answer:
      'ReconX is used for reconciling data between multiple systems, matching records automatically based on rules you configure.',
  },
  {
    id: 'SAYA-0088',
    question: 'How do I reset my SAYA password?',
    answer:
      '1. Go to the login screen.\n2. Click "Forgot password".\n3. Enter your work email.\n4. Follow the reset link sent to your inbox.',
  },
  {
    id: 'SAYA-0211',
    question: 'How do I export reconciliation results?',
    answer:
      '1. Open the completed reconciliation.\n2. Click Export in the top-right corner.\n3. Choose CSV or PDF.\n4. The file downloads automatically.',
  },
  {
    id: 'SAYA-0059',
    question: 'Who can approve a reconciliation?',
    answer:
      'Only users with the "Reviewer" or "Admin" role can approve a completed reconciliation.',
  },
]

// Suggested questions shown as quick-tap chips before the user has typed anything
export const SUGGESTED_QUESTIONS = MOCK_QA.slice(0, 4).map((q) => q.question)

// Very simple substring "fuzzy-ish" matching just for frontend testing.
// The REAL fuzzy matching logic will live in the Python backend later.
export function mockAsk(userQuestion) {
  const normalized = userQuestion.trim().toLowerCase()

  let bestMatch = null
  let bestScore = 0

  for (const item of MOCK_QA) {
    const q = item.question.toLowerCase()
    let score = 0
    if (q === normalized) score = 1
    else if (q.includes(normalized) || normalized.includes(q)) score = 0.75
    else {
      const wordsA = new Set(normalized.split(/\s+/))
      const wordsB = new Set(q.split(/\s+/))
      const overlap = [...wordsA].filter((w) => wordsB.has(w)).length
      score = overlap / Math.max(wordsA.size, wordsB.size)
    }
    if (score > bestScore) {
      bestScore = score
      bestMatch = item
    }
  }

  // Simulate network latency so our loading animation has something to show
  return new Promise((resolve) => {
    setTimeout(() => {
      if (bestMatch && bestScore > 0.3) {
        resolve({
          found: true,
          id: bestMatch.id,
          answer: bestMatch.answer,
          confidence: Math.round(bestScore * 100),
          related: MOCK_QA.filter((q) => q.id !== bestMatch.id)
            .slice(0, 2)
            .map((q) => q.question),
        })
      } else {
        resolve({
          found: false,
          confidence: 0,
          related: MOCK_QA.slice(0, 3).map((q) => q.question),
        })
      }
    }, 700)
  })
}
