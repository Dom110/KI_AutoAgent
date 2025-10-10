/**
 * StateManager - Application state management utility
 * Manages calculator state, history, and persistence
 * Implements Observer pattern for state change notifications
 */

export class StateManager {
    constructor() {
        this.state = this.getInitialState();
        this.history = [];
        this.maxHistorySize = 50;
        this.observers = new Set();
        this.storageKey = 'calculator-state';
        this.autoSave = true;

        // Load persisted state if available
        this.loadPersistedState();

        // Setup auto-save on page unload
        if (typeof window !== 'undefined') {
            window.addEventListener('beforeunload', () => {
                this.saveState();
            });

            // Save state periodically
            this.saveInterval = setInterval(() => {
                if (this.autoSave) {
                    this.saveState();
                }
            }, 30000); // Save every 30 seconds
        }
    }

    /**
     * Get initial state configuration
     * @returns {Object} Initial state object
     */
    getInitialState() {
        return {
            displayValue: '0',
            previousValue: null,
            operation: null,
            waitingForOperand: false,
            isError: false,
            lastAction: null,
            timestamp: Date.now(),
            memory: 0,
            hasMemory: false,
            precision: 10,
            settings: {
                soundEnabled: false,
                theme: 'light',
                decimalPlaces: 'auto'
            }
        };
    }

    /**
     * Update state with new values
     * @param {Object} updates - State updates to apply
     * @param {boolean} addToHistory - Whether to add to history
     * @returns {Object} New state
     */
    updateState(updates, addToHistory = true) {
        try {
            // Validate updates
            this.validateStateUpdate(updates);

            // Save current state to history before updating
            if (addToHistory && this.shouldAddToHistory(updates)) {
                this.addToHistory(this.state);
            }

            // Create new state
            const newState = {
                ...this.state,
                ...updates,
                timestamp: Date.now()
            };

            // Validate new state
            this.validateState(newState);

            // Update state
            this.state = newState;

            // Notify observers
            this.notifyObservers(newState, updates);

            // Auto-save if enabled
            if (this.autoSave) {
                this.scheduleStateSave();
            }

            return newState;
        } catch (error) {
            console.error('State update failed:', error);
            throw new Error(`Failed to update state: ${error.message}`);
        }
    }

    /**
     * Validate state update object
     * @param {Object} updates - Updates to validate
     */
    validateStateUpdate(updates) {
        if (typeof updates !== 'object' || updates === null) {
            throw new Error('Updates must be an object');
        }

        // Validate specific fields
        if ('displayValue' in updates && typeof updates.displayValue !== 'string') {
            throw new Error('displayValue must be a string');
        }

        if ('previousValue' in updates &&
            updates.previousValue !== null &&
            typeof updates.previousValue !== 'number') {
            throw new Error('previousValue must be a number or null');
        }

        if ('operation' in updates &&
            updates.operation !== null &&
            !['+', '-', '*', '/'].includes(updates.operation)) {
            throw new Error('operation must be a valid operator or null');
        }

        if ('waitingForOperand' in updates && typeof updates.waitingForOperand !== 'boolean') {
            throw new Error('waitingForOperand must be a boolean');
        }

        if ('isError' in updates && typeof updates.isError !== 'boolean') {
            throw new Error('isError must be a boolean');
        }
    }

    /**
     * Validate complete state object
     * @param {Object} state - State to validate
     */
    validateState(state) {
        const requiredFields = [
            'displayValue', 'previousValue', 'operation',
            'waitingForOperand', 'isError', 'timestamp'
        ];

        for (const field of requiredFields) {
            if (!(field in state)) {
                throw new Error(`Missing required state field: ${field}`);
            }
        }

        // Additional validation
        if (state.displayValue.length > 50) {
            throw new Error('Display value too long');
        }
    }

    /**
     * Determine if state change should be added to history
     * @param {Object} updates - State updates
     * @returns {boolean} Whether to add to history
     */
    shouldAddToHistory(updates) {
        // Don't add to history for certain actions
        const skipHistoryActions = ['cursor_move', 'display_update', 'timestamp_update'];

        if ('lastAction' in updates && skipHistoryActions.includes(updates.lastAction)) {
            return false;
        }

        // Don't add if only timestamp changed
        const updateKeys = Object.keys(updates).filter(key => key !== 'timestamp');
        return updateKeys.length > 0;
    }

    /**
     * Add current state to history
     * @param {Object} state - State to add to history
     */
    addToHistory(state) {
        try {
            // Create snapshot without observers
            const snapshot = {
                ...state,
                historyTimestamp: Date.now()
            };

            this.history.push(snapshot);

            // Limit history size
            if (this.history.length > this.maxHistorySize) {
                this.history = this.history.slice(-this.maxHistorySize);
            }
        } catch (error) {
            console.error('Failed to add to history:', error);
        }
    }

    /**
     * Undo last state change
     * @returns {Object|null} Previous state or null if no history
     */
    undo() {
        if (this.history.length === 0) {
            return null;
        }

        try {
            const previousState = this.history.pop();

            // Remove history timestamp
            const { historyTimestamp, ...stateWithoutTimestamp } = previousState;

            // Update current state without adding to history
            this.state = {
                ...stateWithoutTimestamp,
                timestamp: Date.now()
            };

            // Notify observers
            this.notifyObservers(this.state, { action: 'undo' });

            return this.state;
        } catch (error) {
            console.error('Undo failed:', error);
            return null;
        }
    }

    /**
     * Clear all state and history
     */
    clearState() {
        this.state = this.getInitialState();
        this.history = [];
        this.notifyObservers(this.state, { action: 'clear' });

        if (this.autoSave) {
            this.clearPersistedState();
        }
    }

    /**
     * Get current state
     * @returns {Object} Current state
     */
    getState() {
        return { ...this.state };
    }

    /**
     * Get state history
     * @returns {Array} History array
     */
    getHistory() {
        return [...this.history];
    }

    /**
     * Check if undo is available
     * @returns {boolean} Whether undo is possible
     */
    canUndo() {
        return this.history.length > 0;
    }

    /**
     * Subscribe to state changes
     * @param {Function} observer - Observer function to call on state changes
     * @returns {Function} Unsubscribe function
     */
    subscribe(observer) {
        if (typeof observer !== 'function') {
            throw new Error('Observer must be a function');
        }

        this.observers.add(observer);

        // Return unsubscribe function
        return () => {
            this.observers.delete(observer);
        };
    }

    /**
     * Notify all observers of state change
     * @param {Object} newState - New state
     * @param {Object} changes - What changed
     */
    notifyObservers(newState, changes) {
        try {
            for (const observer of this.observers) {
                observer(newState, changes);
            }
        } catch (error) {
            console.error('Observer notification failed:', error);
        }
    }

    /**
     * Schedule state save (debounced)
     */
    scheduleStateSave() {
        if (this.saveTimeout) {
            clearTimeout(this.saveTimeout);
        }

        this.saveTimeout = setTimeout(() => {
            this.saveState();
        }, 1000); // Save after 1 second of inactivity
    }

    /**
     * Save state to localStorage
     */
    saveState() {
        if (typeof window === 'undefined' || !window.localStorage) {
            return; // Not in browser environment or localStorage not available
        }

        try {
            const stateToSave = {
                state: this.state,
                version: '1.0.0',
                savedAt: Date.now()
            };

            localStorage.setItem(this.storageKey, JSON.stringify(stateToSave));
        } catch (error) {
            console.error('Failed to save state:', error);
        }
    }

    /**
     * Load state from localStorage
     */
    loadPersistedState() {
        if (typeof window === 'undefined' || !window.localStorage) {
            return; // Not in browser environment
        }

        try {
            const saved = localStorage.getItem(this.storageKey);
            if (!saved) {
                return;
            }

            const parsed = JSON.parse(saved);

            // Validate saved data
            if (parsed.version !== '1.0.0') {
                console.warn('Incompatible state version, using default state');
                return;
            }

            // Check if data is recent (within 24 hours)
            const hoursSinceLastSave = (Date.now() - parsed.savedAt) / (1000 * 60 * 60);
            if (hoursSinceLastSave > 24) {
                console.info('Saved state is old, using default state');
                return;
            }

            // Validate and merge saved state
            this.validateState(parsed.state);
            this.state = {
                ...this.getInitialState(),
                ...parsed.state,
                timestamp: Date.now()
            };

        } catch (error) {
            console.error('Failed to load persisted state:', error);
            // Continue with default state
        }
    }

    /**
     * Clear persisted state
     */
    clearPersistedState() {
        if (typeof window !== 'undefined' && window.localStorage) {
            try {
                localStorage.removeItem(this.storageKey);
            } catch (error) {
                console.error('Failed to clear persisted state:', error);
            }
        }
    }

    /**
     * Export state for backup/sharing
     * @returns {string} JSON string of state
     */
    exportState() {
        try {
            const exportData = {
                state: this.state,
                history: this.history,
                version: '1.0.0',
                exportedAt: Date.now()
            };

            return JSON.stringify(exportData, null, 2);
        } catch (error) {
            throw new Error(`Failed to export state: ${error.message}`);
        }
    }

    /**
     * Import state from backup
     * @param {string} jsonString - JSON string of state
     */
    importState(jsonString) {
        try {
            const importData = JSON.parse(jsonString);

            // Validate import data
            if (importData.version !== '1.0.0') {
                throw new Error('Incompatible import version');
            }

            this.validateState(importData.state);

            // Import state and history
            this.state = {
                ...importData.state,
                timestamp: Date.now()
            };

            if (Array.isArray(importData.history)) {
                this.history = importData.history.slice(-this.maxHistorySize);
            }

            // Notify observers
            this.notifyObservers(this.state, { action: 'import' });

            return true;
        } catch (error) {
            throw new Error(`Failed to import state: ${error.message}`);
        }
    }

    /**
     * Cleanup resources
     */
    destroy() {
        // Clear save timeout
        if (this.saveTimeout) {
            clearTimeout(this.saveTimeout);
        }

        // Clear save interval
        if (this.saveInterval) {
            clearInterval(this.saveInterval);
        }

        // Clear observers
        this.observers.clear();

        // Save final state
        if (this.autoSave) {
            this.saveState();
        }
    }
}