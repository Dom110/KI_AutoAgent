# 🧮 Simple Calculator Apps

This directory contains three different implementations of a simple calculator app with add, subtract, multiply, and divide operations.

## Features

All calculator implementations support:
- ✅ **Addition** (+)
- ✅ **Subtraction** (-)
- ✅ **Multiplication** (×)
- ✅ **Division** (÷)
- ✅ **Decimal numbers**
- ✅ **Negative numbers**
- ✅ **Error handling** (division by zero)

## Calculator Versions

### 1. Command Line Calculator (`simple_calculator.py`)

**Features:**
- Interactive command-line interface
- Text-based input/output
- Error handling with clear messages

**Usage:**
```bash
python3 simple_calculator.py
```

**Example:**
```
🧮 Simple Calculator
Operations: +, -, *, /
Type 'quit' to exit

Enter calculation (e.g., 5 + 3): 15.5 + 2.5
✅ 15.5 + 2.5 = 18.0
```

### 2. GUI Calculator (`calculator_gui.py`)

**Features:**
- Graphical user interface using tkinter
- Button-based input like a real calculator
- Modern styling and layout

**Requirements:**
- Python with tkinter support
- Note: tkinter may not be available in all environments

**Usage:**
```bash
python3 calculator_gui.py
```

### 3. Web Calculator (`calculator_web.html`)

**Features:**
- Modern web-based interface
- Responsive design
- Keyboard and mouse support
- Beautiful gradient styling
- Works in any modern web browser

**Usage:**
1. Open `calculator_web.html` in your web browser
2. Click buttons or use keyboard shortcuts:
   - Numbers: `0-9`
   - Operations: `+`, `-`, `*`, `/`
   - Calculate: `Enter` or `=`
   - Clear: `Escape` or `C`

## Testing

The calculator functionality has been tested with:

```python
# Basic operations
5 + 3 = 8
10 - 4 = 6
6 * 7 = 42
15 / 3 = 5.0

# Edge cases
2.5 + 1.5 = 4.0
-5 + 3 = -2
10 / 0 = Error: Cannot divide by zero
```

## Implementation Details

### Command Line Version
- Uses Python classes for clean organization
- Input parsing with error handling
- Simple text-based interface

### GUI Version
- Built with tkinter for native desktop feel
- Event-driven button handling
- Professional calculator layout

### Web Version
- Pure HTML/CSS/JavaScript
- No external dependencies
- Cross-platform compatibility
- Modern responsive design

## Error Handling

All versions include proper error handling for:
- Division by zero
- Invalid input formats
- Unexpected calculation errors
- User-friendly error messages

## Choose Your Version

- **Command Line**: Best for terminal environments or scriptable automation
- **GUI**: Best for desktop applications with native OS integration
- **Web**: Best for universal compatibility and modern user experience

All three versions implement the same core Calculator class logic, ensuring consistent behavior across platforms.