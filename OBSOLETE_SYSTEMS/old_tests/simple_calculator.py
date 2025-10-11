#!/usr/bin/env python3
"""
Simple Calculator App
Supports addition, subtraction, multiplication, and division
"""

class Calculator:
    """A simple calculator with basic arithmetic operations."""

    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        return a + b

    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        return a - b

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b

    def divide(self, a: float, b: float) -> float:
        """Divide a by b."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b


def main():
    """Interactive calculator interface."""
    calculator = Calculator()
    print("🧮 Simple Calculator")
    print("Operations: +, -, *, /")
    print("Type 'quit' to exit\n")

    while True:
        try:
            # Get user input
            expression = input("Enter calculation (e.g., 5 + 3): ").strip()

            if expression.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break

            # Parse the expression
            parts = expression.split()
            if len(parts) != 3:
                print("❌ Invalid format. Use: number operator number")
                continue

            # Extract operands and operator
            try:
                a = float(parts[0])
                operator = parts[1]
                b = float(parts[2])
            except ValueError:
                print("❌ Invalid numbers. Please enter valid numbers.")
                continue

            # Perform calculation
            if operator == '+':
                result = calculator.add(a, b)
            elif operator == '-':
                result = calculator.subtract(a, b)
            elif operator == '*':
                result = calculator.multiply(a, b)
            elif operator == '/':
                result = calculator.divide(a, b)
            else:
                print("❌ Invalid operator. Use: +, -, *, /")
                continue

            # Display result
            print(f"✅ {a} {operator} {b} = {result}")

        except ValueError as e:
            print(f"❌ Error: {e}")
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()