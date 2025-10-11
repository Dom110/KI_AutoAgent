#!/usr/bin/env python3
"""
GUI Calculator App using tkinter
Supports addition, subtraction, multiplication, and division
"""

import tkinter as tk
from tkinter import messagebox
import math


class CalculatorGUI:
    """A graphical calculator with basic arithmetic operations."""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("🧮 Simple Calculator")
        self.window.geometry("300x400")
        self.window.resizable(False, False)

        # Display variables
        self.current = "0"
        self.previous = "0"
        self.operator = None
        self.waiting_for_operand = False

        # Create the GUI
        self.create_display()
        self.create_buttons()

    def create_display(self):
        """Create the calculator display."""
        self.display_var = tk.StringVar(value="0")
        self.display = tk.Entry(
            self.window,
            textvariable=self.display_var,
            font=("Arial", 16),
            state="readonly",
            justify="right",
            bg="white",
            relief="sunken",
            bd=2
        )
        self.display.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky="ew")

    def create_buttons(self):
        """Create calculator buttons."""
        # Button styling
        button_style = {
            "font": ("Arial", 12),
            "width": 5,
            "height": 2
        }

        number_style = {**button_style, "bg": "#f0f0f0"}
        operator_style = {**button_style, "bg": "#e0e0e0"}
        special_style = {**button_style, "bg": "#d0d0d0"}

        # Button layout
        buttons = [
            ("C", 1, 0, special_style, self.clear),
            ("±", 1, 1, special_style, self.toggle_sign),
            ("%", 1, 2, special_style, self.percentage),
            ("÷", 1, 3, operator_style, lambda: self.operator_click("/")),

            ("7", 2, 0, number_style, lambda: self.number_click("7")),
            ("8", 2, 1, number_style, lambda: self.number_click("8")),
            ("9", 2, 2, number_style, lambda: self.number_click("9")),
            ("×", 2, 3, operator_style, lambda: self.operator_click("*")),

            ("4", 3, 0, number_style, lambda: self.number_click("4")),
            ("5", 3, 1, number_style, lambda: self.number_click("5")),
            ("6", 3, 2, number_style, lambda: self.number_click("6")),
            ("-", 3, 3, operator_style, lambda: self.operator_click("-")),

            ("1", 4, 0, number_style, lambda: self.number_click("1")),
            ("2", 4, 1, number_style, lambda: self.number_click("2")),
            ("3", 4, 2, number_style, lambda: self.number_click("3")),
            ("+", 4, 3, operator_style, lambda: self.operator_click("+")),

            ("0", 5, 0, number_style, lambda: self.number_click("0")),
            (".", 5, 1, number_style, self.decimal_click),
            ("=", 5, 2, {**button_style, "bg": "#4CAF50", "columnspan": 2}, self.equals_click),
        ]

        # Create buttons
        for text, row, col, style, command in buttons:
            if "columnspan" in style:
                colspan = style.pop("columnspan")
                btn = tk.Button(self.window, text=text, command=command, **style)
                btn.grid(row=row, column=col, columnspan=colspan, padx=2, pady=2, sticky="ew")
            else:
                btn = tk.Button(self.window, text=text, command=command, **style)
                btn.grid(row=row, column=col, padx=2, pady=2, sticky="ew")

        # Configure grid weights
        for i in range(4):
            self.window.grid_columnconfigure(i, weight=1)

    def number_click(self, number):
        """Handle number button clicks."""
        if self.waiting_for_operand:
            self.current = number
            self.waiting_for_operand = False
        else:
            if self.current == "0":
                self.current = number
            else:
                self.current += number

        self.update_display()

    def decimal_click(self):
        """Handle decimal point button click."""
        if self.waiting_for_operand:
            self.current = "0."
            self.waiting_for_operand = False
        elif "." not in self.current:
            self.current += "."

        self.update_display()

    def operator_click(self, op):
        """Handle operator button clicks."""
        if self.operator and not self.waiting_for_operand:
            self.equals_click()

        self.previous = self.current
        self.operator = op
        self.waiting_for_operand = True

    def equals_click(self):
        """Handle equals button click."""
        if self.operator and not self.waiting_for_operand:
            try:
                prev_val = float(self.previous)
                curr_val = float(self.current)

                if self.operator == "+":
                    result = prev_val + curr_val
                elif self.operator == "-":
                    result = prev_val - curr_val
                elif self.operator == "*":
                    result = prev_val * curr_val
                elif self.operator == "/":
                    if curr_val == 0:
                        messagebox.showerror("Error", "Cannot divide by zero!")
                        return
                    result = prev_val / curr_val

                # Format result
                if result.is_integer():
                    self.current = str(int(result))
                else:
                    self.current = str(round(result, 10))

                self.operator = None
                self.waiting_for_operand = True
                self.update_display()

            except ValueError:
                messagebox.showerror("Error", "Invalid calculation!")
            except Exception as e:
                messagebox.showerror("Error", f"Calculation error: {str(e)}")

    def clear(self):
        """Clear the calculator."""
        self.current = "0"
        self.previous = "0"
        self.operator = None
        self.waiting_for_operand = False
        self.update_display()

    def toggle_sign(self):
        """Toggle the sign of the current number."""
        if self.current != "0":
            if self.current.startswith("-"):
                self.current = self.current[1:]
            else:
                self.current = "-" + self.current
            self.update_display()

    def percentage(self):
        """Convert current number to percentage."""
        try:
            value = float(self.current) / 100
            if value.is_integer():
                self.current = str(int(value))
            else:
                self.current = str(value)
            self.update_display()
        except ValueError:
            messagebox.showerror("Error", "Invalid number for percentage!")

    def update_display(self):
        """Update the calculator display."""
        # Limit display length
        if len(self.current) > 15:
            self.current = self.current[:15]

        self.display_var.set(self.current)

    def run(self):
        """Start the calculator application."""
        self.window.mainloop()


def main():
    """Run the GUI calculator."""
    calculator = CalculatorGUI()
    calculator.run()


if __name__ == "__main__":
    main()