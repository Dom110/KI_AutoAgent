/**
 * Automated Fix Patterns for Common Integration Issues
 * These patterns would have automatically fixed the problems we manually resolved
 */

export interface AutoFixPattern {
    name: string;
    description: string;
    detect: RegExp | ((code: string) => boolean);
    fix: (code: string) => string;
    testFix?: (originalCode: string, fixedCode: string) => boolean;
}

export class AutomatedFixPatterns {

    /**
     * Pattern 1: Fix streaming implementation
     */
    static readonly STREAMING_IMPLEMENTATION: AutoFixPattern = {
        name: 'Fix Streaming Implementation',
        description: 'Replace chat() with streamChat() when onPartialResponse is present',
        detect: /onPartialResponse.*?\.chat\s*\(/gs,
        fix: (code: string) => {
            // Step 1: Replace .chat( with .streamChat(
            let fixed = code.replace(
                /(\w+Service)\.chat\s*\(\s*([^,)]+)\s*\)/g,
                (match, service, params) => {
                    // Check if this function has onPartialResponse parameter
                    const functionStart = code.lastIndexOf('async', code.indexOf(match));
                    const functionDecl = code.substring(functionStart, code.indexOf(match));

                    if (functionDecl.includes('onPartialResponse')) {
                        return `${service}.streamChat(${params}, onPartialResponse)`;
                    }
                    return match;
                }
            );

            // Step 2: Add accumulator outside callback if missing
            fixed = fixed.replace(
                /(streamChat\([^)]+\)\s*{)/g,
                (match) => {
                    if (!code.includes('let accumulatedContent')) {
                        return `let accumulatedContent = '';\n${match}`;
                    }
                    return match;
                }
            );

            return fixed;
        },
        testFix: (original, fixed) => {
            return fixed.includes('streamChat') &&
                   !fixed.includes('.chat(') &&
                   fixed.includes('onPartialResponse');
        }
    };

    /**
     * Pattern 2: Fix accumulator scope
     */
    static readonly ACCUMULATOR_SCOPE: AutoFixPattern = {
        name: 'Fix Accumulator Variable Scope',
        description: 'Move accumulator variables outside of streaming callbacks',
        detect: /streamChat[^}]*?\([^}]*?\)\s*=>\s*{[^}]*?let\s+(\w*[Aa]ccumulated\w*)\s*=/g,
        fix: (code: string) => {
            const regex = /(streamChat[^{]*{)([^}]*?let\s+(\w*[Aa]ccumulated\w*)\s*=\s*['"`]['"`];?)/g;

            return code.replace(regex, (match, before, accumulatorDecl, varName) => {
                // Move accumulator before the streamChat call
                const streamChatIndex = code.indexOf(match);
                const functionStart = code.lastIndexOf('async', streamChatIndex);
                const indent = code.substring(functionStart, streamChatIndex).match(/\n(\s*)/)?.[1] || '    ';

                // Remove from inside callback
                const cleanedInside = match.replace(accumulatorDecl, '');

                // Add before streamChat
                return `let ${varName} = '';\n${indent}${before}${cleanedInside.substring(before.length)}`;
            });
        }
    };

    /**
     * Pattern 3: Add missing message handlers
     */
    static readonly MESSAGE_HANDLERS: AutoFixPattern = {
        name: 'Add Missing Message Handlers',
        description: 'Add handlers for all required message types',
        detect: (code: string) => {
            return code.includes('switch') &&
                   code.includes('message.type') &&
                   !code.includes("case 'tool_result'");
        },
        fix: (code: string) => {
            const requiredHandlers = [
                { type: 'tool_result', handler: 'this._addToolResult(message);' },
                { type: 'content_block_stop', handler: 'this._handleContentBlockStop(message);' },
                { type: 'error', handler: 'this._handleError(message);' }
            ];

            let fixed = code;

            requiredHandlers.forEach(({ type, handler }) => {
                if (!fixed.includes(`case '${type}'`)) {
                    // Find the switch statement
                    const switchRegex = /(switch\s*\([^)]*message[^)]*type[^)]*\)\s*{)/g;
                    fixed = fixed.replace(switchRegex, (match) => {
                        return `${match}\n            case '${type}':\n                ${handler}\n                break;`;
                    });
                }
            });

            return fixed;
        }
    };

    /**
     * Pattern 4: Add timeout handling
     */
    static readonly TIMEOUT_HANDLING: AutoFixPattern = {
        name: 'Add Timeout Handling',
        description: 'Add AbortController and timeout to streaming operations',
        detect: /streamChat\([^)]+\)(?![^{]*AbortController)/g,
        fix: (code: string) => {
            return code.replace(
                /(async\s+\w+[^{]*{)([^}]*)(await\s+\w+\.streamChat\([^)]+\))/g,
                (match, funcStart, beforeStream, streamCall) => {
                    if (!beforeStream.includes('AbortController')) {
                        const enhanced = `${funcStart}
        const controller = new AbortController();
        const timeout = setTimeout(() => {
            controller.abort();
        }, 30000); // 30 second timeout

        try {${beforeStream}
            ${streamCall};
        } finally {
            clearTimeout(timeout);
        }`;
                        return enhanced;
                    }
                    return match;
                }
            );
        }
    };

    /**
     * Pattern 5: Fix error recovery
     */
    static readonly ERROR_RECOVERY: AutoFixPattern = {
        name: 'Fix Error Recovery',
        description: 'Preserve partial data in error handlers',
        detect: /catch[^{]*{[^}]*return\s+(null|undefined|{})\s*;?\s*}/g,
        fix: (code: string) => {
            return code.replace(
                /catch\s*\((\w+)\)\s*{[^}]*return\s+(null|undefined|{})\s*;?\s*}/g,
                (match, errorVar) => {
                    // Check if there's an accumulator variable nearby
                    const hasAccumulator = code.includes('accumulatedContent');
                    const hasPartialData = code.includes('partialData');

                    if (hasAccumulator) {
                        return `catch (${errorVar}) {
                console.error('Stream error:', ${errorVar});
                return {
                    content: accumulatedContent || '',
                    error: true,
                    errorMessage: ${errorVar}.message
                };
            }`;
                    } else if (hasPartialData) {
                        return `catch (${errorVar}) {
                console.error('Processing error:', ${errorVar});
                return {
                    data: partialData || null,
                    error: true,
                    errorMessage: ${errorVar}.message
                };
            }`;
                    } else {
                        return `catch (${errorVar}) {
                console.error('Operation failed:', ${errorVar});
                return {
                    success: false,
                    error: true,
                    errorMessage: ${errorVar}.message
                };
            }`;
                    }
                }
            );
        }
    };

    /**
     * Pattern 6: Add type guards
     */
    static readonly TYPE_GUARDS: AutoFixPattern = {
        name: 'Add Type Guards',
        description: 'Add optional chaining and type checks',
        detect: /(\w+)\.(\w+)\.(\w+)(?!\?)/g,
        fix: (code: string) => {
            // Whitelist of safe property chains
            const safePatterns = [
                'console.log',
                'process.env',
                'Math.random',
                'JSON.parse',
                'JSON.stringify',
                'Date.now',
                'Array.isArray',
                'Object.keys',
                'Object.values'
            ];

            return code.replace(
                /(\w+)\.(\w+)\.(\w+)/g,
                (match, obj, prop1, prop2) => {
                    // Check if it's a safe pattern
                    if (safePatterns.some(pattern => match.startsWith(pattern))) {
                        return match;
                    }

                    // Check if it's already using optional chaining
                    if (code[code.indexOf(match) + match.length] === '?') {
                        return match;
                    }

                    // Add optional chaining
                    return `${obj}?.${prop1}?.${prop2}`;
                }
            );
        }
    };

    /**
     * Pattern 7: Synchronize state managers
     */
    static readonly STATE_SYNC: AutoFixPattern = {
        name: 'Synchronize State Managers',
        description: 'Ensure both context and history managers are updated together',
        detect: (code: string) => {
            const hasContext = code.includes('contextManager.addMessage');
            const hasHistory = code.includes('historyManager.addMessage');
            return hasContext !== hasHistory; // XOR - one but not both
        },
        fix: (code: string) => {
            // Find places where only one manager is updated
            const contextOnlyRegex = /(this\.contextManager\.addMessage\([^)]+\);?)(?![\s\S]{0,50}historyManager)/g;
            const historyOnlyRegex = /(this\.historyManager\.addMessage\([^)]+\);?)(?![\s\S]{0,50}contextManager)/g;

            let fixed = code;

            // Add history update after context update
            fixed = fixed.replace(contextOnlyRegex, (match) => {
                const messageParam = match.match(/addMessage\(([^)]+)\)/)?.[1];
                return `${match}\n        await this.historyManager.addMessage(${messageParam});`;
            });

            // Add context update after history update
            fixed = fixed.replace(historyOnlyRegex, (match) => {
                const messageParam = match.match(/addMessage\(([^)]+)\)/)?.[1];
                return `${match}\n        this.contextManager.addMessage(${messageParam});`;
            });

            return fixed;
        }
    };

    /**
     * Pattern 8: Add debug logging
     */
    static readonly DEBUG_LOGGING: AutoFixPattern = {
        name: 'Add Debug Logging',
        description: 'Add comprehensive debug logging to API calls',
        detect: /await\s+\w+\.(sendMessage|chat|streamChat|request)\(/g,
        fix: (code: string) => {
            return code.replace(
                /(await\s+(\w+)\.(sendMessage|chat|streamChat|request)\(([^)]+)\))/g,
                (match, fullCall, service, method, params) => {
                    const hasLogging = code.substring(
                        Math.max(0, code.indexOf(match) - 100),
                        code.indexOf(match)
                    ).includes('console.log');

                    if (!hasLogging) {
                        return `console.log('[DEBUG] Calling ${service}.${method} with:', ${params});
        ${fullCall}`;
                    }
                    return match;
                }
            );
        }
    };

    /**
     * Apply all applicable fixes to code
     */
    static applyAllFixes(code: string): { fixed: string; appliedPatterns: string[] } {
        const patterns = [
            this.STREAMING_IMPLEMENTATION,
            this.ACCUMULATOR_SCOPE,
            this.MESSAGE_HANDLERS,
            this.TIMEOUT_HANDLING,
            this.ERROR_RECOVERY,
            this.TYPE_GUARDS,
            this.STATE_SYNC,
            this.DEBUG_LOGGING
        ];

        let fixed = code;
        const appliedPatterns: string[] = [];

        patterns.forEach(pattern => {
            const shouldApply = typeof pattern.detect === 'function'
                ? pattern.detect(fixed)
                : pattern.detect.test(fixed);

            if (shouldApply) {
                const beforeFix = fixed;
                fixed = pattern.fix(fixed);

                // Verify fix was successful
                if (fixed !== beforeFix) {
                    appliedPatterns.push(pattern.name);

                    // Run test if available
                    if (pattern.testFix && !pattern.testFix(beforeFix, fixed)) {
                        console.warn(`Fix verification failed for: ${pattern.name}`);
                        fixed = beforeFix; // Rollback
                        appliedPatterns.pop();
                    }
                }
            }
        });

        return { fixed, appliedPatterns };
    }

    /**
     * Generate fix report
     */
    static generateFixReport(originalCode: string, fixedCode: string, appliedPatterns: string[]): string {
        const linesChanged = this.countChangedLines(originalCode, fixedCode);

        let report = '## 🔧 Automated Fix Report\n\n';
        report += `### Applied ${appliedPatterns.length} fix patterns:\n\n`;

        appliedPatterns.forEach((pattern, index) => {
            report += `${index + 1}. ✅ ${pattern}\n`;
        });

        report += `\n### 📊 Statistics:\n`;
        report += `- Lines changed: ${linesChanged}\n`;
        report += `- Original size: ${originalCode.length} characters\n`;
        report += `- Fixed size: ${fixedCode.length} characters\n`;

        report += '\n### 🎯 Next Steps:\n';
        report += '1. Review the automated fixes\n';
        report += '2. Run tests to verify functionality\n';
        report += '3. Manually review any complex logic changes\n';

        return report;
    }

    /**
     * Count changed lines between two code versions
     */
    private static countChangedLines(original: string, fixed: string): number {
        const originalLines = original.split('\n');
        const fixedLines = fixed.split('\n');

        let changes = 0;
        const maxLines = Math.max(originalLines.length, fixedLines.length);

        for (let i = 0; i < maxLines; i++) {
            if (originalLines[i] !== fixedLines[i]) {
                changes++;
            }
        }

        return changes;
    }
}