/**
 * OperationLogic - Core calculation engine for the calculator
 * Handles all arithmetic operations with proper error handling and edge cases
 */

export class OperationLogic {
  /**
   * Performs arithmetic operations based on the operator
   * @param {number} a - First operand
   * @param {number} b - Second operand
   * @param {string} operator - Operation to perform (+, -, *, /)
   * @returns {number} - Result of the operation
   * @throws {Error} - For invalid operations or division by zero
   */
  static calculate(a, b, operator) {
    // Validate inputs
    if (typeof a !== 'number' || typeof b !== 'number') {
      throw new Error('Invalid operands: both values must be numbers');
    }

    if (isNaN(a) || isNaN(b)) {
      throw new Error('Invalid operands: NaN values not allowed');
    }

    if (!isFinite(a) || !isFinite(b)) {
      throw new Error('Invalid operands: Infinity values not allowed');
    }

    // Perform calculation based on operator
    switch (operator) {
      case '+':
        return this.add(a, b);

      case '-':
        return this.subtract(a, b);

      case '*':
      case '×':
        return this.multiply(a, b);

      case '/':
      case '÷':
        return this.divide(a, b);

      default:
        throw new Error(`Unsupported operator: ${operator}`);
    }
  }

  /**
   * Addition operation
   * @param {number} a - First number
   * @param {number} b - Second number
   * @returns {number} - Sum
   */
  static add(a, b) {
    const result = a + b;

    // Check for overflow
    if (!isFinite(result)) {
      throw new Error('Overflow: Result is too large');
    }

    return this.roundToSafeDecimals(result);
  }

  /**
   * Subtraction operation
   * @param {number} a - First number
   * @param {number} b - Second number
   * @returns {number} - Difference
   */
  static subtract(a, b) {
    const result = a - b;

    // Check for overflow
    if (!isFinite(result)) {
      throw new Error('Overflow: Result is too large');
    }

    return this.roundToSafeDecimals(result);
  }

  /**
   * Multiplication operation
   * @param {number} a - First number
   * @param {number} b - Second number
   * @returns {number} - Product
   */
  static multiply(a, b) {
    const result = a * b;

    // Check for overflow
    if (!isFinite(result)) {
      throw new Error('Overflow: Result is too large');
    }

    return this.roundToSafeDecimals(result);
  }

  /**
   * Division operation with zero-division check
   * @param {number} a - Dividend
   * @param {number} b - Divisor
   * @returns {number} - Quotient
   * @throws {Error} - For division by zero
   */
  static divide(a, b) {
    // Check for division by zero
    if (b === 0) {
      throw new Error('Division by zero is not allowed');
    }

    // Check for division by very small number (could cause overflow)
    if (Math.abs(b) < Number.EPSILON) {
      throw new Error('Division by extremely small number not allowed');
    }

    const result = a / b;

    // Check for overflow or underflow
    if (!isFinite(result)) {
      throw new Error('Division result is too large or too small');
    }

    return this.roundToSafeDecimals(result);
  }

  /**
   * Rounds number to avoid floating point precision issues
   * @param {number} num - Number to round
   * @returns {number} - Rounded number
   */
  static roundToSafeDecimals(num) {
    // For very large or very small numbers, return as-is
    if (Math.abs(num) > 1e15 || Math.abs(num) < 1e-15) {
      return num;
    }

    // Round to 10 decimal places to avoid floating point issues
    return Math.round(num * 1e10) / 1e10;
  }

  /**
   * Evaluates a complete mathematical expression
   * @param {string} expression - Mathematical expression (e.g., "2 + 3 * 4")
   * @returns {number} - Result of the expression
   * @throws {Error} - For invalid expressions
   */
  static evaluateExpression(expression) {
    // Remove whitespace
    expression = expression.replace(/\s+/g, '');

    // Validate expression format
    if (!this.isValidExpression(expression)) {
      throw new Error('Invalid expression format');
    }

    try {
      // Parse and evaluate the expression safely
      return this.parseExpression(expression);
    } catch (error) {
      throw new Error(`Expression evaluation failed: ${error.message}`);
    }
  }

  /**
   * Validates if an expression has proper format
   * @param {string} expression - Expression to validate
   * @returns {boolean} - True if valid
   */
  static isValidExpression(expression) {
    // Allow only numbers, operators, parentheses, and decimal points
    const validPattern = /^[0-9+\-*/().×÷\s]+$/;

    if (!validPattern.test(expression)) {
      return false;
    }

    // Check for balanced parentheses
    let parenthesesCount = 0;
    for (const char of expression) {
      if (char === '(') parenthesesCount++;
      if (char === ')') parenthesesCount--;
      if (parenthesesCount < 0) return false;
    }

    return parenthesesCount === 0;
  }

  /**
   * Parses and evaluates a mathematical expression using proper order of operations
   * @param {string} expression - Expression to parse
   * @returns {number} - Result
   */
  static parseExpression(expression) {
    // Replace × and ÷ with * and /
    expression = expression.replace(/×/g, '*').replace(/÷/g, '/');

    // This is a simplified parser - in production, you'd use a proper expression parser
    // For now, we'll handle basic operations with proper precedence

    // Remove outer parentheses if they wrap the entire expression
    expression = this.removeOuterParentheses(expression);

    // Handle parentheses first
    while (expression.includes('(')) {
      const innerExpression = this.extractInnerParentheses(expression);
      const result = this.parseExpression(innerExpression.content);
      expression = expression.replace(innerExpression.full, result.toString());
    }

    // Handle multiplication and division (left to right)
    expression = this.handleMultiplicationAndDivision(expression);

    // Handle addition and subtraction (left to right)
    expression = this.handleAdditionAndSubtraction(expression);

    const result = parseFloat(expression);

    if (isNaN(result)) {
      throw new Error('Invalid calculation result');
    }

    return result;
  }

  /**
   * Removes outer parentheses if they wrap the entire expression
   * @param {string} expression - Expression to process
   * @returns {string} - Expression without outer parentheses
   */
  static removeOuterParentheses(expression) {
    if (expression.startsWith('(') && expression.endsWith(')')) {
      let depth = 0;
      for (let i = 0; i < expression.length - 1; i++) {
        if (expression[i] === '(') depth++;
        if (expression[i] === ')') depth--;
        if (depth === 0) return expression; // Not fully wrapped
      }
      return expression.slice(1, -1);
    }
    return expression;
  }

  /**
   * Extracts the first innermost parentheses expression
   * @param {string} expression - Expression containing parentheses
   * @returns {object} - Object with full expression and content
   */
  static extractInnerParentheses(expression) {
    const start = expression.indexOf('(');
    let depth = 0;
    let end = start;

    for (let i = start; i < expression.length; i++) {
      if (expression[i] === '(') depth++;
      if (expression[i] === ')') {
        depth--;
        if (depth === 0) {
          end = i;
          break;
        }
      }
    }

    return {
      full: expression.slice(start, end + 1),
      content: expression.slice(start + 1, end)
    };
  }

  /**
   * Handles multiplication and division operations in order
   * @param {string} expression - Expression to process
   * @returns {string} - Expression with multiplication and division resolved
   */
  static handleMultiplicationAndDivision(expression) {
    const operators = ['*', '/'];

    for (const operator of operators) {
      while (expression.includes(operator)) {
        const operatorIndex = expression.indexOf(operator);
        const { left, right } = this.extractOperands(expression, operatorIndex);

        const leftNum = parseFloat(left);
        const rightNum = parseFloat(right);

        const result = this.calculate(leftNum, rightNum, operator);

        const fullExpression = left + operator + right;
        expression = expression.replace(fullExpression, result.toString());
      }
    }

    return expression;
  }

  /**
   * Handles addition and subtraction operations in order
   * @param {string} expression - Expression to process
   * @returns {string} - Expression with addition and subtraction resolved
   */
  static handleAdditionAndSubtraction(expression) {
    const operators = ['+', '-'];

    for (const operator of operators) {
      while (expression.includes(operator)) {
        // Find the first occurrence, but skip if it's a negative sign
        let operatorIndex = expression.indexOf(operator);

        // Skip if this is a negative sign at the beginning or after another operator
        if (operator === '-' && (operatorIndex === 0 || '+-*/'.includes(expression[operatorIndex - 1]))) {
          operatorIndex = expression.indexOf(operator, operatorIndex + 1);
          if (operatorIndex === -1) break;
        }

        const { left, right } = this.extractOperands(expression, operatorIndex);

        const leftNum = parseFloat(left);
        const rightNum = parseFloat(right);

        const result = this.calculate(leftNum, rightNum, operator);

        const fullExpression = left + operator + right;
        expression = expression.replace(fullExpression, result.toString());
      }
    }

    return expression;
  }

  /**
   * Extracts left and right operands from an expression at a given operator position
   * @param {string} expression - Full expression
   * @param {number} operatorIndex - Index of the operator
   * @returns {object} - Object with left and right operands
   */
  static extractOperands(expression, operatorIndex) {
    // Extract left operand
    let leftStart = operatorIndex - 1;
    while (leftStart >= 0 && /[0-9.]/.test(expression[leftStart])) {
      leftStart--;
    }
    // Handle negative numbers
    if (leftStart >= 0 && expression[leftStart] === '-' &&
        (leftStart === 0 || '+-*/('.includes(expression[leftStart - 1]))) {
      leftStart--;
    }
    leftStart++;

    // Extract right operand
    let rightEnd = operatorIndex + 1;
    // Handle negative numbers after operator
    if (expression[rightEnd] === '-') {
      rightEnd++;
    }
    while (rightEnd < expression.length && /[0-9.]/.test(expression[rightEnd])) {
      rightEnd++;
    }

    return {
      left: expression.slice(leftStart, operatorIndex),
      right: expression.slice(operatorIndex + 1, rightEnd)
    };
  }

  /**
   * Formats a number for display, handling very large/small numbers
   * @param {number} num - Number to format
   * @returns {string} - Formatted number string
   */
  static formatNumber(num) {
    if (isNaN(num)) return 'Error';
    if (!isFinite(num)) return 'Error';

    // Handle very large numbers with scientific notation
    if (Math.abs(num) >= 1e12) {
      return num.toExponential(6);
    }

    // Handle very small numbers with scientific notation
    if (Math.abs(num) > 0 && Math.abs(num) < 1e-6) {
      return num.toExponential(6);
    }

    // Regular formatting for normal numbers
    if (num % 1 === 0) {
      // Integer
      return num.toString();
    } else {
      // Decimal - limit to reasonable precision
      return parseFloat(num.toPrecision(12)).toString();
    }
  }
}

export default OperationLogic;