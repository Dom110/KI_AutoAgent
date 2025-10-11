/**
 * CalculatorLogic - Core arithmetic operations and computation logic
 * Implements the Model component of the MVC architecture
 * Provides pure functions for mathematical operations with error handling
 */

export class CalculatorLogic {
    // Precision for floating point operations (15 decimal places)
    static PRECISION = 15;
    static MAX_DISPLAY_DIGITS = 12;
    static MAX_SAFE_INTEGER = Number.MAX_SAFE_INTEGER;
    static MIN_SAFE_INTEGER = Number.MIN_SAFE_INTEGER;

    /**
     * Perform arithmetic calculation between two operands
     * @param {number} firstOperand - The first number
     * @param {number} secondOperand - The second number
     * @param {string} operator - The arithmetic operator (+, -, *, /)
     * @returns {number} The calculation result
     * @throws {Error} For invalid operations or division by zero
     */
    static calculate(firstOperand, secondOperand, operator) {
        // Input validation
        if (typeof firstOperand !== 'number' || typeof secondOperand !== 'number') {
            throw new Error('Invalid operands: Both values must be numbers');
        }

        if (isNaN(firstOperand) || isNaN(secondOperand)) {
            throw new Error('Invalid operands: NaN values not allowed');
        }

        if (!isFinite(firstOperand) || !isFinite(secondOperand)) {
            throw new Error('Invalid operands: Infinite values not allowed');
        }

        // Check for safe integer range to prevent overflow
        if (Math.abs(firstOperand) > this.MAX_SAFE_INTEGER ||
            Math.abs(secondOperand) > this.MAX_SAFE_INTEGER) {
            throw new Error('Number too large for calculation');
        }

        let result;

        switch (operator) {
            case '+':
                result = this.add(firstOperand, secondOperand);
                break;
            case '-':
                result = this.subtract(firstOperand, secondOperand);
                break;
            case '*':
                result = this.multiply(firstOperand, secondOperand);
                break;
            case '/':
                result = this.divide(firstOperand, secondOperand);
                break;
            default:
                throw new Error(`Unsupported operator: ${operator}`);
        }

        // Validate result
        if (!isFinite(result)) {
            throw new Error('Calculation resulted in invalid number');
        }

        return this.roundToPrecision(result);
    }

    /**
     * Addition operation
     * @param {number} a - First operand
     * @param {number} b - Second operand
     * @returns {number} Sum of a and b
     */
    static add(a, b) {
        const result = a + b;

        // Check for overflow
        if (!isFinite(result)) {
            throw new Error('Addition overflow: Result is too large');
        }

        return result;
    }

    /**
     * Subtraction operation
     * @param {number} a - First operand
     * @param {number} b - Second operand
     * @returns {number} Difference of a and b
     */
    static subtract(a, b) {
        const result = a - b;

        // Check for overflow
        if (!isFinite(result)) {
            throw new Error('Subtraction overflow: Result is too large');
        }

        return result;
    }

    /**
     * Multiplication operation
     * @param {number} a - First operand
     * @param {number} b - Second operand
     * @returns {number} Product of a and b
     */
    static multiply(a, b) {
        const result = a * b;

        // Check for overflow
        if (!isFinite(result)) {
            throw new Error('Multiplication overflow: Result is too large');
        }

        return result;
    }

    /**
     * Division operation
     * @param {number} a - Dividend
     * @param {number} b - Divisor
     * @returns {number} Quotient of a divided by b
     * @throws {Error} When dividing by zero
     */
    static divide(a, b) {
        // Division by zero check
        if (b === 0) {
            throw new Error('Cannot divide by zero');
        }

        // Division by very small numbers (near zero)
        if (Math.abs(b) < Number.EPSILON) {
            throw new Error('Cannot divide by number too close to zero');
        }

        const result = a / b;

        // Check for overflow
        if (!isFinite(result)) {
            throw new Error('Division overflow: Result is too large');
        }

        return result;
    }

    /**
     * Round number to precision to avoid floating point errors
     * @param {number} num - Number to round
     * @returns {number} Rounded number
     */
    static roundToPrecision(num) {
        if (!isFinite(num)) {
            return num;
        }

        // Use parseFloat to remove unnecessary decimal places
        const rounded = parseFloat(num.toPrecision(this.PRECISION));

        // Handle very small numbers that should be zero
        if (Math.abs(rounded) < Number.EPSILON) {
            return 0;
        }

        return rounded;
    }

    /**
     * Format result for display with appropriate precision and notation
     * @param {number} result - The calculation result
     * @returns {string} Formatted display string
     */
    static formatResult(result) {
        if (!isFinite(result)) {
            return 'Error';
        }

        if (result === 0) {
            return '0';
        }

        const absResult = Math.abs(result);

        // Use scientific notation for very large or very small numbers
        if (absResult >= 1e12 || (absResult < 1e-6 && absResult !== 0)) {
            return result.toExponential(6);
        }

        // Convert to string and remove trailing zeros
        let formatted = result.toString();

        // Limit display length
        if (formatted.length > this.MAX_DISPLAY_DIGITS) {
            // Try to use toPrecision to fit in display
            const precision = Math.max(1, this.MAX_DISPLAY_DIGITS - 2);
            formatted = result.toPrecision(precision);

            // If still too long, use scientific notation
            if (formatted.length > this.MAX_DISPLAY_DIGITS) {
                formatted = result.toExponential(6);
            }
        }

        return formatted;
    }

    /**
     * Validate input string and convert to number
     * @param {string} input - Input string to validate
     * @returns {number} Parsed number
     * @throws {Error} For invalid input
     */
    static validateAndParseInput(input) {
        if (typeof input !== 'string') {
            throw new Error('Input must be a string');
        }

        if (input.trim() === '') {
            throw new Error('Empty input not allowed');
        }

        // Remove whitespace
        const cleanInput = input.trim();

        // Check for valid number format
        const numberRegex = /^-?(\d+\.?\d*|\.\d+)$/;
        if (!numberRegex.test(cleanInput)) {
            throw new Error('Invalid number format');
        }

        const parsed = parseFloat(cleanInput);

        if (isNaN(parsed)) {
            throw new Error('Could not parse number');
        }

        if (!isFinite(parsed)) {
            throw new Error('Number is infinite');
        }

        return parsed;
    }

    /**
     * Check if a string represents a valid operator
     * @param {string} operator - Operator to validate
     * @returns {boolean} True if valid operator
     */
    static isValidOperator(operator) {
        return ['+', '-', '*', '/'].includes(operator);
    }

    /**
     * Get operator precedence for order of operations
     * @param {string} operator - The operator
     * @returns {number} Precedence level (higher = more precedent)
     */
    static getOperatorPrecedence(operator) {
        switch (operator) {
            case '+':
            case '-':
                return 1;
            case '*':
            case '/':
                return 2;
            default:
                return 0;
        }
    }

    /**
     * Calculate percentage of a number
     * @param {number} value - The base value
     * @param {number} percentage - The percentage to calculate
     * @returns {number} The percentage of the value
     */
    static calculatePercentage(value, percentage) {
        if (typeof value !== 'number' || typeof percentage !== 'number') {
            throw new Error('Both value and percentage must be numbers');
        }

        if (!isFinite(value) || !isFinite(percentage)) {
            throw new Error('Infinite values not allowed');
        }

        const result = (value * percentage) / 100;
        return this.roundToPrecision(result);
    }

    /**
     * Calculate the square root of a number
     * @param {number} value - The number to calculate square root for
     * @returns {number} The square root
     * @throws {Error} For negative numbers
     */
    static calculateSquareRoot(value) {
        if (typeof value !== 'number') {
            throw new Error('Value must be a number');
        }

        if (value < 0) {
            throw new Error('Cannot calculate square root of negative number');
        }

        if (!isFinite(value)) {
            throw new Error('Cannot calculate square root of infinite number');
        }

        const result = Math.sqrt(value);
        return this.roundToPrecision(result);
    }

    /**
     * Calculate power (exponentiation)
     * @param {number} base - The base number
     * @param {number} exponent - The exponent
     * @returns {number} base raised to the power of exponent
     */
    static calculatePower(base, exponent) {
        if (typeof base !== 'number' || typeof exponent !== 'number') {
            throw new Error('Both base and exponent must be numbers');
        }

        if (!isFinite(base) || !isFinite(exponent)) {
            throw new Error('Infinite values not allowed');
        }

        const result = Math.pow(base, exponent);

        if (!isFinite(result)) {
            throw new Error('Power calculation resulted in overflow');
        }

        return this.roundToPrecision(result);
    }
}