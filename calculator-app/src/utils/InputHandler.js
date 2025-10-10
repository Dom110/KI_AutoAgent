/**
 * InputHandler - Manages user input validation and processing
 * Handles button clicks, keyboard input, and input validation
 */

export class InputHandler {
  /**
   * Validates if a character is a valid digit
   * @param {string} char - Character to validate
   * @returns {boolean} - True if valid digit
   */
  static isValidDigit(char) {
    return /^[0-9]$/.test(char);
  }

  /**
   * Validates if a character is a valid operator
   * @param {string} char - Character to validate
   * @returns {boolean} - True if valid operator
   */
  static isValidOperator(char) {
    return ['+', '-', '*', '/', '×', '÷'].includes(char);
  }

  /**
   * Validates if a character is a decimal point
   * @param {string} char - Character to validate
   * @returns {boolean} - True if decimal point
   */
  static isDecimalPoint(char) {
    return char === '.';
  }

  /**
   * Validates if the current display can accept a decimal point
   * @param {string} display - Current display value
   * @returns {boolean} - True if decimal point can be added
   */
  static canAddDecimal(display) {
    // Can't add decimal if display is empty or shows error
    if (!display || display === 'Error' || display === '0') {
      return true;
    }

    // Get the last number in the display
    const lastNumber = this.getLastNumber(display);

    // Can't add decimal if last number already has one
    return !lastNumber.includes('.');
  }

  /**
   * Gets the last number from a display string
   * @param {string} display - Display string
   * @returns {string} - Last number in the display
   */
  static getLastNumber(display) {
    // Split by operators and get the last element
    const parts = display.split(/[+\-*/×÷]/);
    return parts[parts.length - 1];
  }

  /**
   * Validates if a number input is valid
   * @param {string} currentDisplay - Current display value
   * @param {string} digit - Digit to add
   * @returns {object} - Validation result with isValid and reason
   */
  static validateNumberInput(currentDisplay, digit) {
    // Check if digit is valid
    if (!this.isValidDigit(digit)) {
      return {
        isValid: false,
        reason: 'Invalid digit'
      };
    }

    // Check display length to prevent overflow
    if (currentDisplay.length >= 15) {
      return {
        isValid: false,
        reason: 'Maximum display length reached'
      };
    }

    // Don't allow leading zeros unless it's a decimal
    if (currentDisplay === '0' && digit === '0') {
      return {
        isValid: false,
        reason: 'Cannot add leading zeros'
      };
    }

    return {
      isValid: true,
      reason: 'Valid input'
    };
  }

  /**
   * Validates if an operator input is valid
   * @param {string} currentDisplay - Current display value
   * @param {string} operator - Operator to add
   * @returns {object} - Validation result with isValid and reason
   */
  static validateOperatorInput(currentDisplay, operator) {
    // Check if operator is valid
    if (!this.isValidOperator(operator)) {
      return {
        isValid: false,
        reason: 'Invalid operator'
      };
    }

    // Can't add operator to empty display
    if (!currentDisplay || currentDisplay === 'Error') {
      return {
        isValid: false,
        reason: 'Cannot add operator to empty display'
      };
    }

    // Can't add operator if display ends with an operator
    const lastChar = currentDisplay[currentDisplay.length - 1];
    if (this.isValidOperator(lastChar)) {
      return {
        isValid: false,
        reason: 'Cannot add consecutive operators'
      };
    }

    // Can't add operator if display ends with decimal point
    if (lastChar === '.') {
      return {
        isValid: false,
        reason: 'Cannot add operator after decimal point'
      };
    }

    return {
      isValid: true,
      reason: 'Valid operator input'
    };
  }

  /**
   * Validates if a decimal point can be added
   * @param {string} currentDisplay - Current display value
   * @returns {object} - Validation result with isValid and reason
   */
  static validateDecimalInput(currentDisplay) {
    // Can add decimal to empty display or display showing zero
    if (!currentDisplay || currentDisplay === '0' || currentDisplay === 'Error') {
      return {
        isValid: true,
        reason: 'Valid decimal input'
      };
    }

    // Check if current number already has decimal
    if (!this.canAddDecimal(currentDisplay)) {
      return {
        isValid: false,
        reason: 'Current number already has decimal point'
      };
    }

    // Can't add decimal after operator without a number
    const lastChar = currentDisplay[currentDisplay.length - 1];
    if (this.isValidOperator(lastChar)) {
      return {
        isValid: false,
        reason: 'Cannot add decimal point after operator'
      };
    }

    return {
      isValid: true,
      reason: 'Valid decimal input'
    };
  }

  /**
   * Processes number button input
   * @param {string} currentDisplay - Current display value
   * @param {string} digit - Digit pressed
   * @returns {string} - New display value
   */
  static processNumberInput(currentDisplay, digit) {
    const validation = this.validateNumberInput(currentDisplay, digit);

    if (!validation.isValid) {
      return currentDisplay; // Return unchanged if invalid
    }

    // Handle empty display or error state
    if (!currentDisplay || currentDisplay === 'Error') {
      return digit;
    }

    // Handle display showing zero
    if (currentDisplay === '0') {
      return digit;
    }

    // Append digit to display
    return currentDisplay + digit;
  }

  /**
   * Processes operator button input
   * @param {string} currentDisplay - Current display value
   * @param {string} operator - Operator pressed
   * @returns {string} - New display value
   */
  static processOperatorInput(currentDisplay, operator) {
    const validation = this.validateOperatorInput(currentDisplay, operator);

    if (!validation.isValid) {
      return currentDisplay; // Return unchanged if invalid
    }

    // Convert display operators to standard symbols
    const standardOperator = this.standardizeOperator(operator);
    return currentDisplay + standardOperator;
  }

  /**
   * Processes decimal point input
   * @param {string} currentDisplay - Current display value
   * @returns {string} - New display value
   */
  static processDecimalInput(currentDisplay) {
    const validation = this.validateDecimalInput(currentDisplay);

    if (!validation.isValid) {
      return currentDisplay; // Return unchanged if invalid
    }

    // Handle empty display or error state
    if (!currentDisplay || currentDisplay === 'Error') {
      return '0.';
    }

    // Handle display showing zero
    if (currentDisplay === '0') {
      return '0.';
    }

    // Append decimal point
    return currentDisplay + '.';
  }

  /**
   * Processes clear/reset input
   * @returns {string} - Reset display value
   */
  static processClearInput() {
    return '0';
  }

  /**
   * Processes backspace/delete input
   * @param {string} currentDisplay - Current display value
   * @returns {string} - New display value after deletion
   */
  static processBackspaceInput(currentDisplay) {
    // Handle empty display or error state
    if (!currentDisplay || currentDisplay === 'Error' || currentDisplay.length <= 1) {
      return '0';
    }

    // Remove last character
    const newDisplay = currentDisplay.slice(0, -1);

    // If result is empty, return '0'
    return newDisplay || '0';
  }

  /**
   * Standardizes operator symbols for consistent internal representation
   * @param {string} operator - Operator to standardize
   * @returns {string} - Standardized operator
   */
  static standardizeOperator(operator) {
    switch (operator) {
      case '×':
        return '*';
      case '÷':
        return '/';
      default:
        return operator;
    }
  }

  /**
   * Formats operator for display (converts internal symbols to display symbols)
   * @param {string} operator - Internal operator
   * @returns {string} - Display operator
   */
  static formatOperatorForDisplay(operator) {
    switch (operator) {
      case '*':
        return '×';
      case '/':
        return '÷';
      default:
        return operator;
    }
  }

  /**
   * Handles keyboard input events
   * @param {KeyboardEvent} event - Keyboard event
   * @returns {object} - Processed input with type and value
   */
  static handleKeyboardInput(event) {
    const key = event.key;

    // Number keys
    if (this.isValidDigit(key)) {
      return {
        type: 'number',
        value: key
      };
    }

    // Operator keys
    if (this.isValidOperator(key)) {
      return {
        type: 'operator',
        value: key
      };
    }

    // Decimal point
    if (key === '.' || key === ',') {
      return {
        type: 'decimal',
        value: '.'
      };
    }

    // Enter or equals
    if (key === 'Enter' || key === '=') {
      return {
        type: 'equals',
        value: '='
      };
    }

    // Clear
    if (key === 'Escape' || key.toLowerCase() === 'c') {
      return {
        type: 'clear',
        value: 'C'
      };
    }

    // Backspace
    if (key === 'Backspace') {
      return {
        type: 'backspace',
        value: '⌫'
      };
    }

    // Unrecognized key
    return {
      type: 'unknown',
      value: key
    };
  }

  /**
   * Sanitizes display value to prevent injection or invalid states
   * @param {string} display - Display value to sanitize
   * @returns {string} - Sanitized display value
   */
  static sanitizeDisplay(display) {
    if (typeof display !== 'string') {
      return '0';
    }

    // Remove any characters that aren't numbers, operators, or decimal points
    const sanitized = display.replace(/[^0-9+\-*/.×÷]/g, '');

    // If empty after sanitization, return '0'
    if (!sanitized) {
      return '0';
    }

    // Ensure the display doesn't start with an operator (except minus for negative numbers)
    if (this.isValidOperator(sanitized[0]) && sanitized[0] !== '-') {
      return '0';
    }

    return sanitized;
  }

  /**
   * Checks if the display represents a complete expression ready for evaluation
   * @param {string} display - Display value to check
   * @returns {boolean} - True if ready for evaluation
   */
  static isReadyForEvaluation(display) {
    if (!display || display === 'Error' || display === '0') {
      return false;
    }

    // Must not end with an operator or decimal point
    const lastChar = display[display.length - 1];
    if (this.isValidOperator(lastChar) || lastChar === '.') {
      return false;
    }

    // Must contain at least one operator
    return /[+\-*/×÷]/.test(display);
  }
}

export default InputHandler;