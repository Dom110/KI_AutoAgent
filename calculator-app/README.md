# React Calculator

A modern, production-ready calculator application built with React, featuring a responsive design, comprehensive error handling, and accessibility support.

## 🚀 Features

### Core Functionality
- **Basic Arithmetic Operations**: Addition, subtraction, multiplication, division
- **Advanced Features**: Memory functions (MC, MR, M+, M-), undo/redo capability
- **Expression Evaluation**: Supports complex mathematical expressions with proper order of operations
- **Error Handling**: Comprehensive error management with user-friendly messages

### User Experience
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Keyboard Support**: Full keyboard navigation and input support
- **Visual Feedback**: Button press animations and state indicators
- **Accessibility**: ARIA labels, screen reader support, high contrast mode compatibility

### Technical Excellence
- **Modern React**: Built with React 18 using hooks and functional components
- **Component Architecture**: Modular, maintainable code structure following SPA and MVC patterns
- **Performance Optimized**: Webpack bundling with code splitting and optimizations
- **Error Boundaries**: Robust error handling at multiple levels

## 🏗️ Architecture

The application follows a **Component-Based Architecture** with clear separation of concerns:

### Core Components

#### **UIComponent (Calculator.js)**
- Renders the calculator interface
- Handles button layouts and visual feedback
- Manages user interaction events

#### **StateManagement (useCalculatorState.js)**
- Custom React hook managing application state
- Handles calculation logic integration
- Provides undo/redo and memory functions

#### **OperationLogic (OperationLogic.js)**
- Core calculation engine
- Supports basic arithmetic and expression evaluation
- Includes overflow protection and precision handling

#### **InputHandler (InputHandler.js)**
- Validates and processes user input
- Handles keyboard and button interactions
- Provides input sanitization

#### **ErrorHandling (ErrorHandler.js)**
- Centralized error management system
- User-friendly error messages
- Error logging and recovery suggestions

### Data Flow

```
User Input → InputHandler → StateManagement → OperationLogic → UIComponent
     ↑                                                              ↓
     └──────────────── Error Handling ←─────────────────────────────┘
```

## 🛠️ Technology Stack

- **Frontend**: React 18, JavaScript ES6+
- **Styling**: CSS3 with modern features (Grid, Flexbox, Custom Properties)
- **Build Tools**: Webpack 5, Babel
- **Development**: ESLint, Prettier
- **Browser Support**: Modern browsers (Chrome, Firefox, Safari, Edge)

## 📦 Installation

### Prerequisites
- Node.js 16+ and npm

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd calculator-app

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

## 🎮 Usage

### Mouse/Touch Input
- Click buttons to input numbers and operations
- Use the display to view current operation and results
- Memory functions available in the top row

### Keyboard Input
- **Numbers**: 0-9
- **Operations**: +, -, *, /
- **Special Keys**:
  - `Enter` or `=`: Calculate result
  - `Escape` or `C`: Clear all
  - `Backspace`: Delete last digit
  - `.` or `,`: Decimal point

### Memory Functions
- **MC**: Memory Clear
- **MR**: Memory Recall
- **M+**: Add to memory
- **M-**: Subtract from memory

## 🧪 Testing

The application includes comprehensive error handling and input validation:

### Test Scenarios
1. **Basic Operations**: Addition, subtraction, multiplication, division
2. **Edge Cases**: Division by zero, overflow, underflow
3. **Input Validation**: Invalid characters, malformed expressions
4. **Memory Functions**: Store, recall, add, subtract operations
5. **Keyboard Input**: All supported key combinations
6. **Responsive Design**: Various screen sizes and orientations

### Error Handling
- **Division by Zero**: Displays user-friendly error message
- **Overflow**: Handles very large numbers with scientific notation
- **Invalid Input**: Prevents and handles malformed expressions
- **Network Issues**: Graceful degradation (if applicable)

## 🎨 Design Features

### Visual Design
- **Modern Glass Morphism**: Backdrop blur effects and translucent elements
- **Gradient Backgrounds**: Beautiful color gradients
- **Smooth Animations**: Button hover effects and transitions
- **Responsive Grid**: Flexible button layout

### Accessibility
- **ARIA Labels**: Comprehensive screen reader support
- **Keyboard Navigation**: Full keyboard accessibility
- **High Contrast**: Support for high contrast mode
- **Focus Indicators**: Clear focus states for keyboard users
- **Error Announcements**: Screen reader notifications for errors

## 🔧 Configuration

### Build Configuration
The application uses Webpack for bundling with the following optimizations:
- **Code Splitting**: Automatic chunk splitting for better performance
- **Asset Optimization**: Image and CSS optimization
- **Development Server**: Hot module replacement for development
- **Production Build**: Minification and compression

### Browser Support
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 📱 Responsive Design

The calculator adapts to different screen sizes:

- **Desktop (1024px+)**: Full-featured layout with all buttons visible
- **Tablet (768px-1023px)**: Optimized button sizes and spacing
- **Mobile (320px-767px)**: Compact layout with touch-optimized buttons

## 🚀 Performance

### Optimizations
- **Component Memoization**: Prevents unnecessary re-renders
- **Event Handler Optimization**: Cached event handlers using useCallback
- **Bundle Splitting**: Automatic code splitting for faster loading
- **Lazy Loading**: Components loaded on demand

### Metrics
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **First Input Delay**: < 100ms

## 🔒 Security

### Input Validation
- **XSS Prevention**: All input is sanitized and validated
- **Injection Protection**: Expression evaluation uses safe parsing
- **Error Information**: Sensitive information is not exposed in error messages

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit a pull request

### Code Standards
- Use ESLint configuration provided
- Follow React best practices
- Write comprehensive tests
- Update documentation for new features

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🐛 Known Issues

- None currently reported

## 🗺️ Roadmap

### Future Enhancements
- [ ] Scientific calculator functions (sin, cos, tan, log, etc.)
- [ ] History panel showing previous calculations
- [ ] Themes and customization options
- [ ] Offline support with service worker
- [ ] Unit conversion functions
- [ ] Export/import calculation history

## 📞 Support

For bug reports and feature requests, please open an issue in the repository.

---

**Built with ❤️ using React and modern web technologies**