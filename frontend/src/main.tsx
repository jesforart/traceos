/**
 * Main entry point for TraceOS frontend
 *
 * Week 2 - Option C: Production-ready dual renderer system
 * All 15 improvements implemented
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import { App } from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)