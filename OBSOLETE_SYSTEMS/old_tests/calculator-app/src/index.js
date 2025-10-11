/**
 * Entry point for the React Calculator application
 * Sets up React rendering and global styles
 */

import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles/index.css';

// Ensure the DOM is loaded
const initializeApp = () => {
  const container = document.getElementById('root');

  if (!container) {
    console.error('Failed to find root element');
    return;
  }

  // Create React root
  const root = createRoot(container);

  // Render the app
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}