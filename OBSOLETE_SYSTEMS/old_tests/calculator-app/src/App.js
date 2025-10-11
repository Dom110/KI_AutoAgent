/**
 * App - Main Application Component
 * Root component that provides application context and renders the calculator
 */

import React, { useEffect, useState } from 'react';
import Calculator from './components/Calculator';
import { ErrorHandler } from './utils/ErrorHandler';

const App = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [appError, setAppError] = useState(null);

  // Initialize app
  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Simulate app initialization
        await new Promise(resolve => setTimeout(resolve, 500));

        // Check for browser compatibility
        if (!window.addEventListener || !window.JSON) {
          throw new Error('Browser not supported');
        }

        // Initialize error handler
        ErrorHandler.clearErrorLog();

        setIsLoading(false);
      } catch (error) {
        const handledError = ErrorHandler.handleError(error, {
          operation: 'app_initialization',
          userAgent: navigator.userAgent
        });

        setAppError(handledError);
        setIsLoading(false);
      }
    };

    initializeApp();
  }, []);

  // Global error boundary
  const handleGlobalError = (error, errorInfo) => {
    const handledError = ErrorHandler.handleError(error, {
      operation: 'global_error',
      errorInfo: errorInfo
    });

    setAppError(handledError);
  };

  // Handle unhandled promise rejections
  useEffect(() => {
    const handleUnhandledRejection = (event) => {
      const handledError = ErrorHandler.handleError(event.reason, {
        operation: 'unhandled_promise_rejection',
        type: 'promise_rejection'
      });

      console.error('Unhandled Promise Rejection:', handledError);
    };

    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    return () => window.removeEventListener('unhandledrejection', handleUnhandledRejection);
  }, []);

  // Loading state
  if (isLoading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner" aria-label="Loading calculator"></div>
        <p>Initializing Calculator...</p>
      </div>
    );
  }

  // Error state
  if (appError) {
    return (
      <div className="app-error" role="alert">
        <div className="error-container">
          <h1>Calculator Error</h1>
          <p>{appError.message}</p>
          {appError.suggestions && (
            <div className="error-suggestions">
              <h3>Suggestions:</h3>
              <ul>
                {appError.suggestions.map((suggestion, index) => (
                  <li key={index}>{suggestion}</li>
                ))}
              </ul>
            </div>
          )}
          <button
            onClick={() => window.location.reload()}
            className="retry-button"
          >
            Reload Calculator
          </button>
        </div>
      </div>
    );
  }

  // Main app
  return (
    <div className="app">
      <header className="app-header">
        <h1 className="sr-only">React Calculator</h1>
      </header>

      <main className="app-main">
        <ErrorBoundary onError={handleGlobalError}>
          <Calculator />
        </ErrorBoundary>
      </main>

      <footer className="app-footer">
        <p className="sr-only">
          Use keyboard or click buttons to operate the calculator.
          Press Escape to clear, Enter for equals.
        </p>
      </footer>
    </div>
  );
};

// Error Boundary Component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary" role="alert">
          <h2>Something went wrong</h2>
          <p>The calculator encountered an unexpected error.</p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="retry-button"
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default App;