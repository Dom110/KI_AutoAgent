/**
 * ErrorHandler - Centralized error handling and user feedback system
 * Manages error states, logging, and user-friendly error messages
 */

export class ErrorHandler {
  static errorLog = [];
  static maxLogSize = 100;

  /**
   * Error types and their user-friendly messages
   */
  static errorMessages = {
    DIVISION_BY_ZERO: 'Cannot divide by zero',
    INVALID_OPERATION: 'Invalid operation',
    OVERFLOW: 'Number too large',
    UNDERFLOW: 'Number too small',
    INVALID_INPUT: 'Invalid input',
    SYNTAX_ERROR: 'Syntax error',
    UNKNOWN_ERROR: 'An error occurred',
    NETWORK_ERROR: 'Network error',
    MEMORY_ERROR: 'Memory error',
    CALCULATION_ERROR: 'Calculation error'
  };

  /**
   * Error severity levels
   */
  static errorSeverity = {
    LOW: 'low',
    MEDIUM: 'medium',
    HIGH: 'high',
    CRITICAL: 'critical'
  };

  /**
   * Maps specific errors to their types and severity
   */
  static errorMapping = {
    'Division by zero': { type: 'DIVISION_BY_ZERO', severity: 'MEDIUM' },
    'division by zero': { type: 'DIVISION_BY_ZERO', severity: 'MEDIUM' },
    'Overflow': { type: 'OVERFLOW', severity: 'HIGH' },
    'overflow': { type: 'OVERFLOW', severity: 'HIGH' },
    'Underflow': { type: 'UNDERFLOW', severity: 'HIGH' },
    'underflow': { type: 'UNDERFLOW', severity: 'HIGH' },
    'Invalid': { type: 'INVALID_INPUT', severity: 'LOW' },
    'invalid': { type: 'INVALID_INPUT', severity: 'LOW' },
    'Syntax': { type: 'SYNTAX_ERROR', severity: 'MEDIUM' },
    'syntax': { type: 'SYNTAX_ERROR', severity: 'MEDIUM' },
    'NaN': { type: 'CALCULATION_ERROR', severity: 'MEDIUM' },
    'Infinity': { type: 'OVERFLOW', severity: 'HIGH' }
  };

  /**
   * Handles and processes errors from calculator operations
   * @param {Error|string} error - Error object or error message
   * @param {object} context - Additional context about the error
   * @returns {object} - Processed error information
   */
  static handleError(error, context = {}) {
    const errorInfo = this.processError(error, context);

    // Log the error
    this.logError(errorInfo);

    // Return processed error for UI handling
    return {
      message: errorInfo.userMessage,
      type: errorInfo.type,
      severity: errorInfo.severity,
      canRecover: errorInfo.canRecover,
      suggestions: errorInfo.suggestions,
      timestamp: errorInfo.timestamp
    };
  }

  /**
   * Processes raw error into structured error information
   * @param {Error|string} error - Raw error
   * @param {object} context - Error context
   * @returns {object} - Structured error information
   */
  static processError(error, context) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    const errorType = this.determineErrorType(errorMessage);
    const severity = this.determineErrorSeverity(errorType, context);

    return {
      originalError: error,
      message: errorMessage,
      type: errorType,
      severity: severity,
      userMessage: this.getUserFriendlyMessage(errorType, context),
      canRecover: this.canRecoverFromError(errorType),
      suggestions: this.getErrorSuggestions(errorType),
      context: context,
      timestamp: new Date().toISOString(),
      stack: error instanceof Error ? error.stack : null
    };
  }

  /**
   * Determines the error type from error message
   * @param {string} errorMessage - Error message
   * @returns {string} - Error type
   */
  static determineErrorType(errorMessage) {
    for (const [keyword, mapping] of Object.entries(this.errorMapping)) {
      if (errorMessage.toLowerCase().includes(keyword.toLowerCase())) {
        return mapping.type;
      }
    }
    return 'UNKNOWN_ERROR';
  }

  /**
   * Determines error severity
   * @param {string} errorType - Error type
   * @param {object} context - Error context
   * @returns {string} - Error severity
   */
  static determineErrorSeverity(errorType, context) {
    // Check context for severity overrides
    if (context.severity) {
      return context.severity;
    }

    // Use mapping
    for (const mapping of Object.values(this.errorMapping)) {
      if (mapping.type === errorType) {
        return mapping.severity;
      }
    }

    return this.errorSeverity.MEDIUM;
  }

  /**
   * Gets user-friendly error message
   * @param {string} errorType - Error type
   * @param {object} context - Error context
   * @returns {string} - User-friendly message
   */
  static getUserFriendlyMessage(errorType, context) {
    // Check for custom message in context
    if (context.userMessage) {
      return context.userMessage;
    }

    // Return standard message
    return this.errorMessages[errorType] || this.errorMessages.UNKNOWN_ERROR;
  }

  /**
   * Determines if the error is recoverable
   * @param {string} errorType - Error type
   * @returns {boolean} - True if recoverable
   */
  static canRecoverFromError(errorType) {
    const nonRecoverableErrors = ['OVERFLOW', 'MEMORY_ERROR', 'NETWORK_ERROR'];
    return !nonRecoverableErrors.includes(errorType);
  }

  /**
   * Gets suggestions for fixing the error
   * @param {string} errorType - Error type
   * @returns {Array<string>} - Array of suggestions
   */
  static getErrorSuggestions(errorType) {
    const suggestions = {
      DIVISION_BY_ZERO: [
        'Try dividing by a non-zero number',
        'Check your calculation for zeros in denominators'
      ],
      INVALID_OPERATION: [
        'Check your input format',
        'Make sure all operations are valid'
      ],
      OVERFLOW: [
        'Try using smaller numbers',
        'Break down large calculations into smaller steps'
      ],
      UNDERFLOW: [
        'The result is too small to display',
        'Try working with larger numbers'
      ],
      INVALID_INPUT: [
        'Check for typos in your input',
        'Make sure all characters are valid'
      ],
      SYNTAX_ERROR: [
        'Check parentheses balance',
        'Verify operator placement'
      ],
      CALCULATION_ERROR: [
        'Try clearing and starting over',
        'Check your input for errors'
      ]
    };

    return suggestions[errorType] || ['Try clearing and starting over'];
  }

  /**
   * Logs error to internal log
   * @param {object} errorInfo - Processed error information
   */
  static logError(errorInfo) {
    // Add to error log
    this.errorLog.push({
      timestamp: errorInfo.timestamp,
      type: errorInfo.type,
      message: errorInfo.message,
      severity: errorInfo.severity,
      context: errorInfo.context
    });

    // Maintain log size
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog.shift();
    }

    // Console logging for development
    if (process.env.NODE_ENV === 'development') {
      console.group(`Calculator Error [${errorInfo.severity}]`);
      console.error('Type:', errorInfo.type);
      console.error('Message:', errorInfo.message);
      console.error('User Message:', errorInfo.userMessage);
      console.error('Context:', errorInfo.context);
      if (errorInfo.stack) {
        console.error('Stack:', errorInfo.stack);
      }
      console.groupEnd();
    }
  }

  /**
   * Validates calculator input before processing
   * @param {string} input - Input to validate
   * @returns {object} - Validation result
   */
  static validateInput(input) {
    if (typeof input !== 'string') {
      return {
        isValid: false,
        error: this.handleError('Input must be a string', { input })
      };
    }

    // Check for empty input
    if (!input.trim()) {
      return {
        isValid: false,
        error: this.handleError('Input cannot be empty', { input })
      };
    }

    // Check for maximum length
    if (input.length > 1000) {
      return {
        isValid: false,
        error: this.handleError('Input too long', {
          input: input.substring(0, 50) + '...',
          length: input.length
        })
      };
    }

    // Check for valid characters
    const validChars = /^[0-9+\-*/().×÷\s]+$/;
    if (!validChars.test(input)) {
      return {
        isValid: false,
        error: this.handleError('Invalid characters in input', { input })
      };
    }

    return {
      isValid: true,
      error: null
    };
  }

  /**
   * Safely executes a calculation with error handling
   * @param {Function} calculation - Calculation function to execute
   * @param {object} context - Execution context
   * @returns {object} - Result or error
   */
  static safeExecute(calculation, context = {}) {
    try {
      const result = calculation();

      // Validate result
      if (typeof result === 'number') {
        if (isNaN(result)) {
          throw new Error('Calculation resulted in NaN');
        }
        if (!isFinite(result)) {
          throw new Error('Calculation resulted in Infinity');
        }
      }

      return {
        success: true,
        result: result,
        error: null
      };
    } catch (error) {
      const handledError = this.handleError(error, {
        ...context,
        operation: 'calculation'
      });

      return {
        success: false,
        result: null,
        error: handledError
      };
    }
  }

  /**
   * Gets error statistics
   * @returns {object} - Error statistics
   */
  static getErrorStats() {
    const totalErrors = this.errorLog.length;
    const errorsByType = {};
    const errorsBySeverity = {};

    this.errorLog.forEach(error => {
      errorsByType[error.type] = (errorsByType[error.type] || 0) + 1;
      errorsBySeverity[error.severity] = (errorsBySeverity[error.severity] || 0) + 1;
    });

    return {
      totalErrors,
      errorsByType,
      errorsBySeverity,
      recentErrors: this.errorLog.slice(-10)
    };
  }

  /**
   * Clears error log
   */
  static clearErrorLog() {
    this.errorLog = [];
  }

  /**
   * Gets recent errors
   * @param {number} count - Number of recent errors to get
   * @returns {Array} - Recent errors
   */
  static getRecentErrors(count = 10) {
    return this.errorLog.slice(-count);
  }

  /**
   * Checks if error recovery is recommended
   * @param {object} errorInfo - Error information
   * @returns {boolean} - True if recovery is recommended
   */
  static shouldRecommendRecovery(errorInfo) {
    // Don't recommend recovery for critical errors
    if (errorInfo.severity === this.errorSeverity.CRITICAL) {
      return false;
    }

    // Don't recommend recovery if same error occurred recently
    const recentErrors = this.getRecentErrors(5);
    const sameErrorCount = recentErrors.filter(e => e.type === errorInfo.type).length;

    return sameErrorCount < 3;
  }
}

export default ErrorHandler;