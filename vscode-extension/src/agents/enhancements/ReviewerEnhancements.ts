/**
 * Enhanced Review Rules for VS Code Extension Integration Issues
 * These patterns would have caught the problems we manually fixed
 */

export interface SystemIntegrationIssue {
    type: string;
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    line?: number;
    code?: string;
    message: string;
    autoFixable: boolean;
    suggestedFix?: string;
}

export class EnhancedReviewerRules {

    /**
     * Check for streaming implementation issues
     */
    static checkStreamingImplementation(code: string): SystemIntegrationIssue[] {
        const issues: SystemIntegrationIssue[] = [];

        // Check 1: onPartialResponse parameter not being used
        const hasOnPartialResponse = /onPartialResponse\s*[?:]/g.test(code);
        const usesStreamChat = /streamChat\s*\(/g.test(code);
        const usesRegularChat = /\.chat\s*\(/g.test(code);

        if (hasOnPartialResponse && !usesStreamChat && usesRegularChat) {
            issues.push({
                type: 'STREAMING_NOT_IMPLEMENTED',
                severity: 'HIGH',
                message: 'Function has onPartialResponse parameter but uses chat() instead of streamChat()',
                autoFixable: true,
                suggestedFix: 'Replace .chat( with .streamChat( and pass onPartialResponse as second parameter'
            });
        }

        // Check 2: Accumulator scope issues in streaming callbacks
        const accumulatorInCallbackRegex = /streamChat[^}]*?\([^}]*?\)\s*=>\s*{[^}]*?let\s+\w*[Aa]ccumulated\w*\s*=/g;
        if (accumulatorInCallbackRegex.test(code)) {
            issues.push({
                type: 'ACCUMULATOR_SCOPE_ERROR',
                severity: 'CRITICAL',
                message: 'Accumulator variable declared inside streaming callback - will reset on each chunk',
                autoFixable: true,
                suggestedFix: 'Move accumulator variable declaration outside the callback function'
            });
        }

        // Check 3: Missing streaming in agents
        const isAgentFile = /class\s+\w*Agent\s+extends/g.test(code);
        const hasExecuteMethod = /async\s+execute\w*\(/g.test(code);

        if (isAgentFile && hasExecuteMethod && !usesStreamChat && hasOnPartialResponse) {
            issues.push({
                type: 'AGENT_STREAMING_MISSING',
                severity: 'HIGH',
                message: 'Agent class has streaming callback but doesn\'t use streaming API',
                autoFixable: true,
                suggestedFix: 'Implement streamChat in agent execute methods'
            });
        }

        return issues;
    }

    /**
     * Check for message handler completeness
     */
    static checkMessageHandlers(code: string): SystemIntegrationIssue[] {
        const issues: SystemIntegrationIssue[] = [];

        // Find switch statements handling message types
        const switchMessageTypeRegex = /switch\s*\([^)]*message[^)]*type[^)]*\)\s*{([^}]+(?:{[^}]*}[^}]*)*)}/g;
        const matches = code.match(switchMessageTypeRegex);

        if (matches) {
            const requiredHandlers = [
                'text', 'stream_event', 'tool_use', 'tool_result',
                'error', 'system', 'content_block_start', 'content_block_stop'
            ];

            matches.forEach(switchBlock => {
                const missingHandlers = requiredHandlers.filter(handler => {
                    const caseRegex = new RegExp(`case\\s+['"\`]${handler}['"\`]`, 'g');
                    return !caseRegex.test(switchBlock);
                });

                if (missingHandlers.length > 0) {
                    issues.push({
                        type: 'MISSING_MESSAGE_HANDLERS',
                        severity: 'MEDIUM',
                        message: `Missing message handlers: ${missingHandlers.join(', ')}`,
                        autoFixable: true,
                        suggestedFix: `Add case statements for: ${missingHandlers.join(', ')}`
                    });
                }
            });
        }

        return issues;
    }

    /**
     * Check for error recovery patterns
     */
    static checkErrorRecovery(code: string): SystemIntegrationIssue[] {
        const issues: SystemIntegrationIssue[] = [];

        // Check 1: Returning null/undefined in catch blocks without preserving partial data
        const catchReturnsNullRegex = /catch[^{]*{[^}]*return\s+(null|undefined|{}\s*);?\s*}/g;
        if (catchReturnsNullRegex.test(code)) {
            issues.push({
                type: 'DATA_LOSS_ON_ERROR',
                severity: 'HIGH',
                message: 'Catch block returns null/undefined - partial data will be lost',
                autoFixable: true,
                suggestedFix: 'Return partial data with error flag instead of null'
            });
        }

        // Check 2: Missing try-catch around streaming operations
        const streamingWithoutTryRegex = /(?<!try\s*{[^}]*)(streamChat|stream\()/g;
        if (streamingWithoutTryRegex.test(code)) {
            issues.push({
                type: 'UNPROTECTED_STREAMING',
                severity: 'MEDIUM',
                message: 'Streaming operation without try-catch error handling',
                autoFixable: true,
                suggestedFix: 'Wrap streaming operations in try-catch with partial content recovery'
            });
        }

        return issues;
    }

    /**
     * Check for timeout handling
     */
    static checkTimeoutHandling(code: string): SystemIntegrationIssue[] {
        const issues: SystemIntegrationIssue[] = [];

        // Check for async operations without timeout
        const asyncOpsRegex = /(streamChat|fetch|request|axios|http)/g;
        const hasAsyncOps = asyncOpsRegex.test(code);
        const hasTimeout = /setTimeout|AbortController|timeout/g.test(code);

        if (hasAsyncOps && !hasTimeout) {
            issues.push({
                type: 'MISSING_TIMEOUT',
                severity: 'MEDIUM',
                message: 'Async operations without timeout handling - requests may hang indefinitely',
                autoFixable: true,
                suggestedFix: 'Add AbortController with timeout or setTimeout wrapper'
            });
        }

        return issues;
    }

    /**
     * Check for state synchronization issues
     */
    static checkStateSynchronization(code: string): SystemIntegrationIssue[] {
        const issues: SystemIntegrationIssue[] = [];

        // Check for multiple state managers without sync
        const hasContextManager = /contextManager\./g.test(code);
        const hasHistoryManager = /historyManager\./g.test(code);
        const hasAddMessage = /\.addMessage\(/g.test(code);

        if (hasContextManager && hasHistoryManager && hasAddMessage) {
            // Check if both managers are called in same function
            const functionBlocks = code.match(/async\s+\w+\([^)]*\)[^{]*{[^}]+(?:{[^}]*}[^}]*)*/g) || [];

            functionBlocks.forEach(func => {
                const contextCalls = (func.match(/contextManager\.addMessage/g) || []).length;
                const historyCalls = (func.match(/historyManager\.addMessage/g) || []).length;

                if ((contextCalls > 0 && historyCalls === 0) ||
                    (historyCalls > 0 && contextCalls === 0)) {
                    issues.push({
                        type: 'STATE_DESYNC',
                        severity: 'HIGH',
                        message: 'State managers not synchronized - only one manager being updated',
                        autoFixable: true,
                        suggestedFix: 'Update both contextManager and historyManager together'
                    });
                }
            });
        }

        return issues;
    }

    /**
     * Check for type safety issues
     */
    static checkTypeSafety(code: string): SystemIntegrationIssue[] {
        const issues: SystemIntegrationIssue[] = [];

        // Check for unsafe property access chains
        const unsafeAccessRegex = /(\w+)\.(\w+)\.(\w+)(?!\?)/g;
        const matches = code.matchAll(unsafeAccessRegex);

        for (const match of matches) {
            // Exclude known safe patterns
            if (!match[0].includes('console.') &&
                !match[0].includes('process.') &&
                !match[0].includes('Math.')) {
                issues.push({
                    type: 'UNSAFE_PROPERTY_ACCESS',
                    severity: 'MEDIUM',
                    message: `Unsafe property access: ${match[0]} - use optional chaining`,
                    autoFixable: true,
                    suggestedFix: `Replace with: ${match[1]}?.${match[2]}?.${match[3]}`
                });
            }
        }

        // Check for missing null checks before array operations
        const arrayOpsWithoutCheckRegex = /(\w+)\.(?:map|filter|forEach|reduce)\(/g;
        const arrayMatches = code.matchAll(arrayOpsWithoutCheckRegex);

        for (const match of arrayMatches) {
            const variable = match[1];
            // Check if there's a guard before this line
            const guardRegex = new RegExp(`if\\s*\\([^)]*${variable}[^)]*\\)`, 'g');
            const hasGuard = guardRegex.test(code.substring(Math.max(0, match.index! - 200), match.index!));

            if (!hasGuard) {
                issues.push({
                    type: 'UNGUARDED_ARRAY_OPERATION',
                    severity: 'MEDIUM',
                    message: `Array operation without null check: ${match[0]}`,
                    autoFixable: true,
                    suggestedFix: `Add guard: if (${variable} && Array.isArray(${variable}))`
                });
            }
        }

        return issues;
    }

    /**
     * Run all enhanced review checks
     */
    static runAllChecks(code: string): SystemIntegrationIssue[] {
        return [
            ...this.checkStreamingImplementation(code),
            ...this.checkMessageHandlers(code),
            ...this.checkErrorRecovery(code),
            ...this.checkTimeoutHandling(code),
            ...this.checkStateSynchronization(code),
            ...this.checkTypeSafety(code)
        ];
    }

    /**
     * Generate review report
     */
    static generateReport(issues: SystemIntegrationIssue[]): string {
        if (issues.length === 0) {
            return '✅ No integration issues found!';
        }

        const criticalIssues = issues.filter(i => i.severity === 'CRITICAL');
        const highIssues = issues.filter(i => i.severity === 'HIGH');
        const mediumIssues = issues.filter(i => i.severity === 'MEDIUM');
        const lowIssues = issues.filter(i => i.severity === 'LOW');

        let report = '## 🔍 Integration Review Report\n\n';
        report += `Found **${issues.length}** integration issues\n\n`;

        if (criticalIssues.length > 0) {
            report += '### 🔴 CRITICAL Issues\n';
            criticalIssues.forEach(issue => {
                report += `- **${issue.type}**: ${issue.message}\n`;
                if (issue.suggestedFix) {
                    report += `  - Fix: ${issue.suggestedFix}\n`;
                }
            });
            report += '\n';
        }

        if (highIssues.length > 0) {
            report += '### 🟠 HIGH Priority Issues\n';
            highIssues.forEach(issue => {
                report += `- **${issue.type}**: ${issue.message}\n`;
                if (issue.suggestedFix) {
                    report += `  - Fix: ${issue.suggestedFix}\n`;
                }
            });
            report += '\n';
        }

        if (mediumIssues.length > 0) {
            report += '### 🟡 MEDIUM Priority Issues\n';
            mediumIssues.forEach(issue => {
                report += `- **${issue.type}**: ${issue.message}\n`;
                if (issue.suggestedFix) {
                    report += `  - Fix: ${issue.suggestedFix}\n`;
                }
            });
            report += '\n';
        }

        const autoFixableCount = issues.filter(i => i.autoFixable).length;
        report += `### 🔧 Auto-fixable Issues: ${autoFixableCount}/${issues.length}\n`;

        return report;
    }
}