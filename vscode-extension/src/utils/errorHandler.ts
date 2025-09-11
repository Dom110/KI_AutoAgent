/**
 * Utility functions for error handling
 */

export function getErrorMessage(error: unknown): string {
    if (error instanceof Error) {
        return (error as any).message;
    }
    if (typeof error === 'string') {
        return error;
    }
    if (error && typeof error === 'object' && 'message' in error) {
        return String((error as any).message);
    }
    return 'Unknown error occurred';
}

export function isErrorWithMessage(error: unknown): error is { message: string } {
    return (
        typeof error === 'object' &&
        error !== null &&
        'message' in error &&
        typeof (error as any).message === 'string'
    );
}

export function safeJsonParse<T>(jsonString: string): T | null {
    try {
        return JSON.parse(jsonString) as T;
    } catch {
        return null;
    }
}