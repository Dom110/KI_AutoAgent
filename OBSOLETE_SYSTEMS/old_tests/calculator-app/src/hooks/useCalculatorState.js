/**
 * useCalculatorState - Custom React hook for managing calculator state
 * Implements the StateManagement component using React hooks
 */

import { useState, useCallback, useEffect } from 'react';
import { OperationLogic } from '../utils/OperationLogic';
import { InputHandler } from '../utils/InputHandler';

export const useCalculatorState = () => {
  // Core state
  const [display, setDisplay] = useState('0');
  const [operation, setOperation] = useState('');
  const [previousResult, setPreviousResult] = useState(null);
  const [isError, setIsError] = useState(false);
  const [lastButtonPressed, setLastButtonPressed] = useState(null);
  const [isWaitingForOperand, setIsWaitingForOperand] = useState(false);

  // History state for undo functionality
  const [history, setHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // Save state to history
  const saveToHistory = useCallback((state) => {
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push({
      display: state.display,
      operation: state.operation,
      timestamp: Date.now()
    });

    // Limit history to last 50 operations
    if (newHistory.length > 50) {
      newHistory.shift();
    }

    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  }, [history, historyIndex]);

  // Handle number input
  const handleNumber = useCallback((digit) => {
    setLastButtonPressed(digit);

    if (isError) {
      // Reset on new input after error
      setDisplay(digit);
      setOperation('');
      setIsError(false);
      setIsWaitingForOperand(false);
      return;
    }

    if (isWaitingForOperand) {
      // Start new number after operator
      setDisplay(digit);
      setIsWaitingForOperand(false);
    } else {
      // Process number input through InputHandler
      const newDisplay = InputHandler.processNumberInput(display, digit);
      setDisplay(newDisplay);
    }
  }, [display, isError, isWaitingForOperand]);

  // Handle operator input
  const handleOperator = useCallback((operator) => {
    setLastButtonPressed(operator);

    if (isError) {
      return; // Don't allow operators when in error state
    }

    // If there's already an operation and we're not waiting for operand, calculate first
    if (operation && !isWaitingForOperand) {
      try {
        const result = OperationLogic.evaluateExpression(operation + display);
        const formattedResult = OperationLogic.formatNumber(result);

        // Save to history
        saveToHistory({
          display: operation + display + ' = ' + formattedResult,
          operation: operation + display
        });

        setDisplay(formattedResult);
        setOperation(formattedResult + operator);
        setPreviousResult(result);
        setIsWaitingForOperand(true);
      } catch (error) {
        setDisplay('Error');
        setOperation('');
        setIsError(true);
        setIsWaitingForOperand(false);
        return;
      }
    } else {
      // Start new operation or replace current operator
      const currentValue = isWaitingForOperand ? display : display;
      setOperation(currentValue + operator);
      setIsWaitingForOperand(true);
    }
  }, [display, operation, isError, isWaitingForOperand, saveToHistory]);

  // Handle equals/calculation
  const handleEquals = useCallback(() => {
    setLastButtonPressed('=');

    if (isError || !operation) {
      return;
    }

    try {
      const fullExpression = operation + (isWaitingForOperand ? '' : display);

      if (!InputHandler.isReadyForEvaluation(fullExpression)) {
        return; // Don't calculate incomplete expressions
      }

      const result = OperationLogic.evaluateExpression(fullExpression);
      const formattedResult = OperationLogic.formatNumber(result);

      // Save to history
      saveToHistory({
        display: fullExpression + ' = ' + formattedResult,
        operation: fullExpression
      });

      setDisplay(formattedResult);
      setOperation('');
      setPreviousResult(result);
      setIsWaitingForOperand(true);
      setIsError(false);
    } catch (error) {
      setDisplay('Error');
      setOperation('');
      setIsError(true);
      setIsWaitingForOperand(false);
    }
  }, [display, operation, isError, isWaitingForOperand, saveToHistory]);

  // Handle decimal point
  const handleDecimal = useCallback(() => {
    setLastButtonPressed('.');

    if (isError) {
      // Reset on new input after error
      setDisplay('0.');
      setOperation('');
      setIsError(false);
      setIsWaitingForOperand(false);
      return;
    }

    if (isWaitingForOperand) {
      // Start new decimal number
      setDisplay('0.');
      setIsWaitingForOperand(false);
    } else {
      // Process decimal input through InputHandler
      const newDisplay = InputHandler.processDecimalInput(display);
      setDisplay(newDisplay);
    }
  }, [display, isError, isWaitingForOperand]);

  // Handle clear
  const handleClear = useCallback(() => {
    setLastButtonPressed('C');
    setDisplay('0');
    setOperation('');
    setIsError(false);
    setIsWaitingForOperand(false);
    setPreviousResult(null);
  }, []);

  // Handle clear entry (CE)
  const handleClearEntry = useCallback(() => {
    setLastButtonPressed('CE');

    if (isWaitingForOperand) {
      // Clear the operation
      setOperation('');
      setIsWaitingForOperand(false);
    } else {
      // Clear just the display
      setDisplay('0');
    }

    setIsError(false);
  }, [isWaitingForOperand]);

  // Handle backspace
  const handleBackspace = useCallback(() => {
    setLastButtonPressed('⌫');

    if (isError || isWaitingForOperand) {
      return;
    }

    const newDisplay = InputHandler.processBackspaceInput(display);
    setDisplay(newDisplay);
  }, [display, isError, isWaitingForOperand]);

  // Handle keyboard input
  const handleKeyboard = useCallback((event) => {
    event.preventDefault();

    const input = InputHandler.handleKeyboardInput(event);

    switch (input.type) {
      case 'number':
        handleNumber(input.value);
        break;
      case 'operator':
        handleOperator(input.value);
        break;
      case 'decimal':
        handleDecimal();
        break;
      case 'equals':
        handleEquals();
        break;
      case 'clear':
        handleClear();
        break;
      case 'backspace':
        handleBackspace();
        break;
      default:
        // Ignore unknown keys
        break;
    }
  }, [handleNumber, handleOperator, handleDecimal, handleEquals, handleClear, handleBackspace]);

  // Undo functionality
  const handleUndo = useCallback(() => {
    if (historyIndex > 0) {
      const previousState = history[historyIndex - 1];
      setDisplay(previousState.display);
      setOperation(previousState.operation);
      setHistoryIndex(historyIndex - 1);
      setIsError(false);
      setIsWaitingForOperand(false);
    }
  }, [history, historyIndex]);

  // Redo functionality
  const handleRedo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      const nextState = history[historyIndex + 1];
      setDisplay(nextState.display);
      setOperation(nextState.operation);
      setHistoryIndex(historyIndex + 1);
      setIsError(false);
      setIsWaitingForOperand(false);
    }
  }, [history, historyIndex]);

  // Memory functions
  const [memory, setMemory] = useState(0);

  const handleMemoryStore = useCallback(() => {
    if (!isError && display !== 'Error') {
      const value = parseFloat(display) || 0;
      setMemory(value);
    }
  }, [display, isError]);

  const handleMemoryRecall = useCallback(() => {
    if (!isError) {
      setDisplay(OperationLogic.formatNumber(memory));
      setIsWaitingForOperand(false);
    }
  }, [memory, isError]);

  const handleMemoryAdd = useCallback(() => {
    if (!isError && display !== 'Error') {
      const value = parseFloat(display) || 0;
      setMemory(prevMemory => prevMemory + value);
    }
  }, [display, isError]);

  const handleMemorySubtract = useCallback(() => {
    if (!isError && display !== 'Error') {
      const value = parseFloat(display) || 0;
      setMemory(prevMemory => prevMemory - value);
    }
  }, [display, isError]);

  const handleMemoryClear = useCallback(() => {
    setMemory(0);
  }, []);

  // Add keyboard event listeners
  useEffect(() => {
    const handleKeyPress = (event) => {
      // Prevent default for calculator keys
      if (/[0-9+\-*/.=cC]/.test(event.key) ||
          event.key === 'Enter' ||
          event.key === 'Escape' ||
          event.key === 'Backspace') {
        handleKeyboard(event);
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [handleKeyboard]);

  // Computed values
  const currentOperation = operation + (isWaitingForOperand ? '' : display);
  const canUndo = historyIndex > 0;
  const canRedo = historyIndex < history.length - 1;
  const hasMemory = memory !== 0;

  return {
    // State
    display,
    operation: currentOperation,
    isError,
    lastButtonPressed,
    isWaitingForOperand,
    previousResult,
    memory,
    history,

    // Computed state
    canUndo,
    canRedo,
    hasMemory,

    // Actions
    handleNumber,
    handleOperator,
    handleEquals,
    handleDecimal,
    handleClear,
    handleClearEntry,
    handleBackspace,
    handleKeyboard,
    handleUndo,
    handleRedo,
    handleMemoryStore,
    handleMemoryRecall,
    handleMemoryAdd,
    handleMemorySubtract,
    handleMemoryClear
  };
};

export default useCalculatorState;