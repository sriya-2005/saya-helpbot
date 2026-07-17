import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite reads this file to know how to run/build our app.
// The react() plugin teaches Vite how to understand .jsx files
// (JSX is the HTML-like syntax we write inside JavaScript for React).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173, // the local address our app will run on: http://localhost:5173
    proxy: {
      '/ask': 'http://localhost:8000',
      '/suggested-questions': 'http://localhost:8000',
      '/reload': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
