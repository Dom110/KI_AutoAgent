/**
 * Calculator - Main UI Component
 * Renders the calculator interface and handles user interactions
 */

import React, { useCallback } from 'react';
import { useCalculatorState } from '../hooks/useCalculatorState';
import { ErrorHandler } from '../utils/ErrorHandler';
import '../styles/Calculator.css';

const Calculator = () => {
  const {
    display,
    operation,
    isError,
    lastButtonPressed,
    handleNumber,
    handleOperator,
    handleEquals,
    handleDecimal,
    handleClear,
    handleClearEntry,
    handleBackspace,
    handleMemoryStore,
    handleMemoryRecall,
    handleMemoryAdd,
    handleMemorySubtract,
    handleMemoryClear,
    hasMemory,
    canUndo,
    handleUndo
  } = useCalculatorState();

  // Button click handler with visual feedback
  const handleButtonClick = useCallback((callback, buttonValue) => {
    return () => {
      try {
        // Add pressed class for visual feedback
        const buttonElement = document.querySelector(`[data-button="${buttonValue}"]`);
        if (buttonElement) {
          buttonElement.classList.add('pressed');
          setTimeout(() => {
            buttonElement.classList.remove('pressed');
          }, 100);
        }

        // Execute the callback
        callback();
      } catch (error) {
        const handledError = ErrorHandler.handleError(error, {
          operation: 'button_click',
          buttonValue: buttonValue
        });
        console.error('Button click error:', handledError);
      }
    };
  }, []);

  // Button configuration
  const buttons = [
    // Row 1: Memory and Clear functions
    [
      { label: 'MC', type: 'function', action: handleMemoryClear, disabled: !hasMemory },
      { label: 'MR', type: 'function', action: handleMemoryRecall, disabled: !hasMemory },
      { label: 'M+', type: 'function', action: handleMemoryAdd },
      { label: 'M-', type: 'function', action: handleMemorySubtract }
    ],
    // Row 2: Clear and backspace
    [
      { label: 'C', type: 'clear', action: handleClear },
      { label: 'CE', type: 'function', action: handleClearEntry },
      { label: '⌫', type: 'function', action: handleBackspace },
      { label: '÷', type: 'operator', action: () => handleOperator('/') }
    ],
    // Row 3: Numbers 7-9 and multiply
    [
      { label: '7', type: 'number', action: () => handleNumber('7') },
      { label: '8', type: 'number', action: () => handleNumber('8') },
      { label: '9', type: 'number', action: () => handleNumber('9') },
      { label: '×', type: 'operator', action: () => handleOperator('*') }
    ],
    // Row 4: Numbers 4-6 and subtract
    [
      { label: '4', type: 'number', action: () => handleNumber('4') },
      { label: '5', type: 'number', action: () => handleNumber('5') },
      { label: '6', type: 'number', action: () => handleNumber('6') },
      { label: '-', type: 'operator', action: () => handleOperator('-') }
    ],
    // Row 5: Numbers 1-3 and add
    [
      { label: '1', type: 'number', action: () => handleNumber('1') },
      { label: '2', type: 'number', action: () => handleNumber('2') },
      { label: '3', type: 'number', action: () => handleNumber('3') },
      { label: '+', type: 'operator', action: () => handleOperator('+') }
    ],
    // Row 6: Zero, decimal, and equals
    [
      { label: '0', type: 'number', action: () => handleNumber('0'), className: 'zero' },
      { label: '.', type: 'number', action: handleDecimal },
      { label: '=', type: 'operator', action: handleEquals, className: 'equals' }
    ]
  ];

  // Render button
  const renderButton = (button, index) => {
    const {
      label,
      type,
      action,
      disabled = false,
      className = ''
    } = button;

    const buttonClasses = [
      'button',
      type,
      className,
      disabled ? 'disabled' : '',
      lastButtonPressed === label ? 'active' : ''
    ].filter(Boolean).join(' ');

    return (
      <button
        key={`${label}-${index}`}
        className={buttonClasses}
        onClick={handleButtonClick(action, label)}
        disabled={disabled}
        data-button={label}
        aria-label={`${label} button`}
        tabIndex={disabled ? -1 : 0}
      >
        {label}
      </button>
    );
  };

  // Format display value
  const formatDisplay = (value) => {
    if (value === 'Error') return value;
    if (value === '0') return '0';

    // Handle very long numbers
    if (value.length > 12) {
      const num = parseFloat(value);
      if (!isNaN(num)) {
        if (Math.abs(num) >= 1e12 || (Math.abs(num) < 1e-6 && num !== 0)) {
          return num.toExponential(6);
        }
        return num.toPrecision(12);
      }
    }

    return value;
  };

  return (
    <div className="calculator" role="application" aria-label="Calculator">
      {/* Display Section */}
      <div className="display" aria-live="polite">
        <div className="display-operation" aria-label="Current operation">
          {operation || '\u00A0'}
        </div>
        <div
          className={`display-result ${isError ? 'error' : ''}`}
          aria-label="Result display"
        >
          {formatDisplay(display)}
        </div>
      </div>

      {/* Button Grid */}
      <div className="button-grid">
        {buttons.flat().map((button, index) => renderButton(button, index))}
      </div>

      {/* Additional Controls (Hidden but accessible via keyboard) */}
      <div style={{ position: 'absolute', left: '-9999px' }}>
        <button
          onClick={handleUndo}
          disabled={!canUndo}
          aria-label="Undo last operation"
          tabIndex={-1}
        >
          Undo
        </button>
        <button
          onClick={handleMemoryStore}
          aria-label="Store current value in memory"
          tabIndex={-1}
        >
          Memory Store
        </button>
      </div>

      {/* Screen reader announcements */}
      <div aria-live="assertive" className="sr-only">
        {isError && 'Calculation error occurred'}
        {hasMemory && 'Value stored in memory'}
      </div>
    </div>
  );
};

export default Calculator;