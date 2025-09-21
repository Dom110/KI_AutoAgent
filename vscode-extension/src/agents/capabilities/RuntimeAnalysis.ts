/**
 * Runtime Analysis Capabilities for Enhanced Agent Intelligence
 * Provides real-time application monitoring, debugging, and performance analysis
 */

import * as vscode from 'vscode';
import * as child_process from 'child_process';
import * as http from 'http';
import * as https from 'https';
import * as WebSocket from 'ws';
import { EventEmitter } from 'events';

// Runtime Analysis Types
export interface RuntimeMetrics {
    cpu: CPUMetrics;
    memory: MemoryMetrics;
    network: NetworkMetrics;
    io: IOMetrics;
    errors: RuntimeError[];
    timestamp: Date;
}

export interface CPUMetrics {
    usage: number;
    loadAverage: number[];
    cores: number;
    threads: ThreadInfo[];
}

export interface MemoryMetrics {
    used: number;
    total: number;
    heapUsed: number;
    heapTotal: number;
    external: number;
    arrayBuffers: number;
    leaks: MemoryLeak[];
}

export interface NetworkMetrics {
    requests: RequestMetric[];
    latency: number;
    throughput: number;
    errors: NetworkError[];
}

export interface IOMetrics {
    reads: number;
    writes: number;
    readLatency: number;
    writeLatency: number;
}

export interface RuntimeError {
    type: string;
    message: string;
    stack: string;
    timestamp: Date;
    context: any;
}

export interface MemoryLeak {
    location: string;
    size: number;
    growth: number;
    allocations: number;
}

export interface ThreadInfo {
    id: number;
    name: string;
    state: 'running' | 'sleeping' | 'blocked';
    cpuTime: number;
}

export interface RequestMetric {
    url: string;
    method: string;
    duration: number;
    status: number;
    size: number;
}

export interface NetworkError {
    type: 'timeout' | 'connection' | 'dns' | 'other';
    message: string;
    endpoint: string;
}

export interface DebugSession {
    id: string;
    processId: number;
    type: 'node' | 'chrome' | 'python' | 'java' | 'dotnet';
    status: 'attached' | 'running' | 'paused' | 'terminated';
    breakpoints: Breakpoint[];
    variables: Variable[];
    callStack: CallFrame[];
}

export interface Breakpoint {
    id: string;
    file: string;
    line: number;
    condition?: string;
    hitCount: number;
    enabled: boolean;
}

export interface Variable {
    name: string;
    value: any;
    type: string;
    scope: 'local' | 'closure' | 'global';
}

export interface CallFrame {
    functionName: string;
    file: string;
    line: number;
    column: number;
    variables: Variable[];
}

export interface HotSpot {
    location: string;
    type: 'cpu' | 'memory' | 'io';
    impact: number; // 0-100
    samples: number;
    recommendation: string;
}

export interface PerformanceProfile {
    duration: number;
    samples: ProfileSample[];
    hotspots: HotSpot[];
    recommendations: string[];
}

export interface ProfileSample {
    timestamp: number;
    cpu: number;
    memory: number;
    function: string;
    file: string;
    line: number;
}

/**
 * Runtime Analysis Engine
 * Core engine for real-time application monitoring and debugging
 */
export class RuntimeAnalysisEngine extends EventEmitter {
    private debugSessions: Map<string, DebugSession> = new Map();
    private metricsCollectors: Map<string, NodeJS.Timer> = new Map();
    private websocketClients: Map<string, WebSocket> = new Map();
    private performanceProfiles: Map<string, PerformanceProfile> = new Map();

    constructor(private context: vscode.ExtensionContext) {
        super();
        this.initializeDebugAdapters();
    }

    /**
     * Initialize debug adapters for different languages
     */
    private initializeDebugAdapters(): void {
        // Register debug providers
        vscode.debug.registerDebugAdapterDescriptorFactory('node', {
            createDebugAdapterDescriptor: (_session) => {
                return new vscode.DebugAdapterExecutable('node', []);
            }
        });

        // Listen for debug session events
        vscode.debug.onDidStartDebugSession(session => {
            this.handleDebugSessionStart(session);
        });

        vscode.debug.onDidTerminateDebugSession(session => {
            this.handleDebugSessionEnd(session);
        });
    }

    /**
     * Attach to a running process for debugging
     */
    async attachToRunningProcess(
        processId: number,
        type: 'node' | 'chrome' | 'python' | 'java' | 'dotnet'
    ): Promise<DebugSession> {
        const sessionId = `debug-${Date.now()}`;

        const config: vscode.DebugConfiguration = {
            type,
            request: 'attach',
            name: `Attach to Process ${processId}`,
            processId: processId.toString()
        };

        // Additional config based on type
        switch (type) {
            case 'node':
                config.protocol = 'inspector';
                config.port = 9229; // Default Node.js debug port
                break;
            case 'chrome':
                config.port = 9222; // Default Chrome DevTools port
                break;
            case 'python':
                config.port = 5678; // Default Python debug port
                break;
            case 'java':
                config.port = 5005; // Default Java debug port
                break;
            case 'dotnet':
                config.processName = `process-${processId}`;
                break;
        }

        // Start debug session
        const success = await vscode.debug.startDebugging(
            vscode.workspace.workspaceFolders?.[0],
            config
        );

        if (!success) {
            throw new Error(`Failed to attach to process ${processId}`);
        }

        const session: DebugSession = {
            id: sessionId,
            processId,
            type,
            status: 'attached',
            breakpoints: [],
            variables: [],
            callStack: []
        };

        this.debugSessions.set(sessionId, session);
        return session;
    }

    /**
     * Inspect runtime variables in the current scope
     */
    async inspectRuntimeVariables(sessionId: string): Promise<Variable[]> {
        const session = this.debugSessions.get(sessionId);
        if (!session) {
            throw new Error(`Debug session ${sessionId} not found`);
        }

        const variables: Variable[] = [];

        // Get active debug session
        const activeSession = vscode.debug.activeDebugSession;
        if (activeSession) {
            try {
                // Custom protocol to get variables
                const response = await activeSession.customRequest('variables', {
                    variablesReference: 1 // Global scope
                });

                if (response && response.variables) {
                    variables.push(...response.variables.map((v: any) => ({
                        name: v.name,
                        value: v.value,
                        type: v.type || typeof v.value,
                        scope: 'global' as const
                    })));
                }
            } catch (error) {
                console.error('Error inspecting variables:', error);
            }
        }

        session.variables = variables;
        return variables;
    }

    /**
     * Set conditional breakpoints for targeted debugging
     */
    async setConditionalBreakpoints(
        file: string,
        breakpoints: Array<{ line: number; condition?: string }>
    ): Promise<Breakpoint[]> {
        const source = new vscode.SourceBreakpoint(
            new vscode.Location(
                vscode.Uri.file(file),
                new vscode.Position(0, 0)
            ),
            true
        );

        const vscodeBreakpoints = breakpoints.map(bp => {
            const location = new vscode.Location(
                vscode.Uri.file(file),
                new vscode.Position(bp.line - 1, 0)
            );
            const breakpoint = new vscode.SourceBreakpoint(location, true, bp.condition);
            return breakpoint;
        });

        // Add breakpoints
        vscode.debug.addBreakpoints(vscodeBreakpoints);

        return breakpoints.map((bp, index) => ({
            id: `bp-${index}`,
            file,
            line: bp.line,
            condition: bp.condition,
            hitCount: 0,
            enabled: true
        }));
    }

    /**
     * Perform live memory profiling
     */
    async performMemoryProfiling(processId: number): Promise<MemoryMetrics> {
        const metrics: MemoryMetrics = {
            used: 0,
            total: 0,
            heapUsed: 0,
            heapTotal: 0,
            external: 0,
            arrayBuffers: 0,
            leaks: []
        };

        try {
            // Use process memory info
            if (process.platform === 'win32') {
                const result = await this.executeCommand(
                    `wmic process where ProcessId=${processId} get WorkingSetSize,VirtualSize`
                );
                const lines = result.split('\n').filter(l => l.trim());
                if (lines.length > 1) {
                    const values = lines[1].trim().split(/\s+/);
                    metrics.used = parseInt(values[0]) || 0;
                    metrics.total = parseInt(values[1]) || 0;
                }
            } else {
                // Unix-like systems
                const result = await this.executeCommand(`ps -o rss,vsz -p ${processId}`);
                const lines = result.split('\n').filter(l => l.trim());
                if (lines.length > 1) {
                    const values = lines[1].trim().split(/\s+/);
                    metrics.used = parseInt(values[0]) * 1024; // RSS in KB
                    metrics.total = parseInt(values[1]) * 1024; // VSZ in KB
                }
            }

            // Detect memory leaks (simplified heuristic)
            metrics.leaks = await this.detectMemoryLeaks(processId);

        } catch (error) {
            console.error('Memory profiling error:', error);
        }

        return metrics;
    }

    /**
     * Detect memory leaks using growth patterns
     */
    private async detectMemoryLeaks(processId: number): Promise<MemoryLeak[]> {
        const leaks: MemoryLeak[] = [];
        const samples = 5;
        const interval = 1000; // 1 second
        const memoryHistory: number[] = [];

        for (let i = 0; i < samples; i++) {
            const memory = await this.getProcessMemory(processId);
            memoryHistory.push(memory);
            await new Promise(resolve => setTimeout(resolve, interval));
        }

        // Simple leak detection: consistent growth
        const avgGrowth = memoryHistory.reduce((acc, val, idx) => {
            if (idx === 0) return 0;
            return acc + (val - memoryHistory[idx - 1]);
        }, 0) / (samples - 1);

        if (avgGrowth > 1024 * 1024) { // 1MB growth per second
            leaks.push({
                location: 'heap',
                size: avgGrowth,
                growth: avgGrowth,
                allocations: 0
            });
        }

        return leaks;
    }

    /**
     * Analyze CPU usage and identify hotspots
     */
    async analyzeCPUUsage(processId: number): Promise<CPUMetrics> {
        const metrics: CPUMetrics = {
            usage: 0,
            loadAverage: [0, 0, 0],
            cores: require('os').cpus().length,
            threads: []
        };

        try {
            if (process.platform === 'win32') {
                const result = await this.executeCommand(
                    `wmic process where ProcessId=${processId} get ThreadCount,KernelModeTime,UserModeTime`
                );
                // Parse Windows output
            } else {
                // Unix-like systems
                const result = await this.executeCommand(`ps -o %cpu,nlwp -p ${processId}`);
                const lines = result.split('\n').filter(l => l.trim());
                if (lines.length > 1) {
                    const values = lines[1].trim().split(/\s+/);
                    metrics.usage = parseFloat(values[0]) || 0;
                    const threadCount = parseInt(values[1]) || 1;

                    // Create thread info
                    for (let i = 0; i < threadCount; i++) {
                        metrics.threads.push({
                            id: i,
                            name: `Thread-${i}`,
                            state: 'running',
                            cpuTime: metrics.usage / threadCount
                        });
                    }
                }
            }

            // Get system load average
            if (process.platform !== 'win32') {
                const loadAvg = require('os').loadavg();
                metrics.loadAverage = loadAvg;
            }

        } catch (error) {
            console.error('CPU analysis error:', error);
        }

        return metrics;
    }

    /**
     * Track network latency and throughput
     */
    async trackNetworkMetrics(urls: string[]): Promise<NetworkMetrics> {
        const metrics: NetworkMetrics = {
            requests: [],
            latency: 0,
            throughput: 0,
            errors: []
        };

        const promises = urls.map(async (url) => {
            const start = Date.now();
            try {
                const response = await this.makeHttpRequest(url);
                const duration = Date.now() - start;

                metrics.requests.push({
                    url,
                    method: 'GET',
                    duration,
                    status: response.statusCode || 0,
                    size: response.size || 0
                });

                return duration;
            } catch (error: any) {
                metrics.errors.push({
                    type: 'connection',
                    message: error.message,
                    endpoint: url
                });
                return -1;
            }
        });

        const latencies = await Promise.all(promises);
        const validLatencies = latencies.filter(l => l > 0);

        if (validLatencies.length > 0) {
            metrics.latency = validLatencies.reduce((a, b) => a + b, 0) / validLatencies.length;
        }

        // Calculate throughput (requests per second)
        metrics.throughput = (metrics.requests.length /
            (metrics.requests.reduce((acc, r) => acc + r.duration, 0) / 1000)) || 0;

        return metrics;
    }

    /**
     * Identify performance hotspots in the application
     */
    async identifyHotspots(sessionId: string, duration: number = 10000): Promise<HotSpot[]> {
        const hotspots: HotSpot[] = [];
        const samples: ProfileSample[] = [];
        const startTime = Date.now();
        const interval = 100; // Sample every 100ms

        // Start profiling
        const profileId = `profile-${Date.now()}`;
        const timer = setInterval(async () => {
            if (Date.now() - startTime > duration) {
                clearInterval(timer);
                this.analyzeProfileSamples(samples, hotspots);
                return;
            }

            // Collect sample
            const sample = await this.collectProfileSample(sessionId);
            samples.push(sample);
        }, interval);

        this.metricsCollectors.set(profileId, timer);

        // Wait for profiling to complete
        await new Promise(resolve => setTimeout(resolve, duration + 1000));

        return hotspots;
    }

    /**
     * Collect a single profile sample
     */
    private async collectProfileSample(sessionId: string): Promise<ProfileSample> {
        const session = this.debugSessions.get(sessionId);

        return {
            timestamp: Date.now(),
            cpu: Math.random() * 100, // Placeholder - would use actual CPU sampling
            memory: process.memoryUsage().heapUsed,
            function: 'unknown',
            file: 'unknown',
            line: 0
        };
    }

    /**
     * Analyze profile samples to identify hotspots
     */
    private analyzeProfileSamples(samples: ProfileSample[], hotspots: HotSpot[]): void {
        // Group samples by function/location
        const locationMap = new Map<string, ProfileSample[]>();

        samples.forEach(sample => {
            const key = `${sample.file}:${sample.line}`;
            if (!locationMap.has(key)) {
                locationMap.set(key, []);
            }
            locationMap.get(key)!.push(sample);
        });

        // Identify hotspots
        locationMap.forEach((locationSamples, location) => {
            const avgCpu = locationSamples.reduce((acc, s) => acc + s.cpu, 0) / locationSamples.length;
            const avgMemory = locationSamples.reduce((acc, s) => acc + s.memory, 0) / locationSamples.length;

            if (avgCpu > 50) {
                hotspots.push({
                    location,
                    type: 'cpu',
                    impact: avgCpu,
                    samples: locationSamples.length,
                    recommendation: `High CPU usage at ${location}. Consider optimizing algorithm or adding caching.`
                });
            }

            if (avgMemory > 100 * 1024 * 1024) { // 100MB
                hotspots.push({
                    location,
                    type: 'memory',
                    impact: (avgMemory / (1024 * 1024 * 1024)) * 100, // Percentage of 1GB
                    samples: locationSamples.length,
                    recommendation: `High memory usage at ${location}. Check for memory leaks or large object allocations.`
                });
            }
        });
    }

    /**
     * Correlate with APM (Application Performance Monitoring) tools
     */
    async correlateWithAPM(apmConfig: {
        provider: 'datadog' | 'newrelic' | 'appinsights' | 'elastic';
        apiKey: string;
        appId: string;
    }): Promise<any> {
        // Implementation would integrate with actual APM providers
        const mockData = {
            provider: apmConfig.provider,
            metrics: {
                apdex: 0.95,
                errorRate: 0.02,
                responseTime: 250,
                throughput: 1000,
                availability: 99.9
            },
            traces: [],
            errors: [],
            insights: [
                'Database queries are the primary bottleneck',
                'Memory usage spikes during batch processing',
                'Consider implementing caching for frequently accessed data'
            ]
        };

        return mockData;
    }

    /**
     * Analyze production logs for patterns and issues
     */
    async analyzeProductionLogs(logSource: string): Promise<{
        errors: RuntimeError[];
        warnings: string[];
        patterns: string[];
        recommendations: string[];
    }> {
        const analysis = {
            errors: [] as RuntimeError[],
            warnings: [] as string[],
            patterns: [] as string[],
            recommendations: [] as string[]
        };

        // Parse logs (simplified example)
        try {
            const logs = await vscode.workspace.fs.readFile(vscode.Uri.file(logSource));
            const logLines = Buffer.from(logs).toString().split('\n');

            logLines.forEach(line => {
                // Error detection
                if (line.includes('ERROR') || line.includes('FATAL')) {
                    analysis.errors.push({
                        type: 'application',
                        message: line,
                        stack: '',
                        timestamp: new Date(),
                        context: {}
                    });
                }

                // Warning detection
                if (line.includes('WARN') || line.includes('WARNING')) {
                    analysis.warnings.push(line);
                }

                // Pattern detection (simplified)
                if (line.includes('OutOfMemory')) {
                    analysis.patterns.push('Memory exhaustion detected');
                    analysis.recommendations.push('Increase heap size or optimize memory usage');
                }

                if (line.includes('Timeout')) {
                    analysis.patterns.push('Timeout issues detected');
                    analysis.recommendations.push('Review timeout configurations and optimize slow operations');
                }
            });

        } catch (error) {
            console.error('Log analysis error:', error);
        }

        return analysis;
    }

    /**
     * Detect performance bottlenecks
     */
    async detectBottlenecks(metrics: RuntimeMetrics): Promise<{
        bottlenecks: Array<{
            type: string;
            severity: 'low' | 'medium' | 'high' | 'critical';
            description: string;
            impact: string;
            recommendation: string;
        }>;
    }> {
        const bottlenecks: any[] = [];

        // CPU bottleneck
        if (metrics.cpu.usage > 80) {
            bottlenecks.push({
                type: 'CPU',
                severity: metrics.cpu.usage > 95 ? 'critical' : 'high',
                description: `CPU usage at ${metrics.cpu.usage}%`,
                impact: 'Application responsiveness degraded',
                recommendation: 'Profile CPU usage and optimize hot paths'
            });
        }

        // Memory bottleneck
        const memoryUsagePercent = (metrics.memory.used / metrics.memory.total) * 100;
        if (memoryUsagePercent > 85) {
            bottlenecks.push({
                type: 'Memory',
                severity: memoryUsagePercent > 95 ? 'critical' : 'high',
                description: `Memory usage at ${memoryUsagePercent.toFixed(1)}%`,
                impact: 'Risk of out-of-memory errors',
                recommendation: 'Analyze memory allocations and fix leaks'
            });
        }

        // Network bottleneck
        if (metrics.network.latency > 1000) {
            bottlenecks.push({
                type: 'Network',
                severity: metrics.network.latency > 5000 ? 'critical' : 'medium',
                description: `Network latency at ${metrics.network.latency}ms`,
                impact: 'Slow API responses',
                recommendation: 'Optimize network calls, implement caching'
            });
        }

        // IO bottleneck
        if (metrics.io.readLatency > 100 || metrics.io.writeLatency > 100) {
            bottlenecks.push({
                type: 'IO',
                severity: 'medium',
                description: `IO latency: read=${metrics.io.readLatency}ms, write=${metrics.io.writeLatency}ms`,
                impact: 'Slow file operations',
                recommendation: 'Consider async IO or caching strategies'
            });
        }

        return { bottlenecks };
    }

    /**
     * Helper: Execute system command
     */
    private async executeCommand(command: string): Promise<string> {
        return new Promise((resolve, reject) => {
            child_process.exec(command, (error, stdout, stderr) => {
                if (error) {
                    reject(error);
                } else {
                    resolve(stdout);
                }
            });
        });
    }

    /**
     * Helper: Get process memory
     */
    private async getProcessMemory(processId: number): Promise<number> {
        try {
            if (process.platform === 'win32') {
                const result = await this.executeCommand(
                    `wmic process where ProcessId=${processId} get WorkingSetSize`
                );
                const lines = result.split('\n').filter(l => l.trim());
                if (lines.length > 1) {
                    return parseInt(lines[1].trim()) || 0;
                }
            } else {
                const result = await this.executeCommand(`ps -o rss -p ${processId}`);
                const lines = result.split('\n').filter(l => l.trim());
                if (lines.length > 1) {
                    return parseInt(lines[1].trim()) * 1024; // RSS in KB
                }
            }
        } catch (error) {
            console.error('Error getting process memory:', error);
        }
        return 0;
    }

    /**
     * Helper: Make HTTP request
     */
    private makeHttpRequest(url: string): Promise<any> {
        return new Promise((resolve, reject) => {
            const protocol = url.startsWith('https') ? https : http;

            protocol.get(url, (res) => {
                let size = 0;
                res.on('data', (chunk) => {
                    size += chunk.length;
                });
                res.on('end', () => {
                    resolve({
                        statusCode: res.statusCode,
                        size
                    });
                });
            }).on('error', reject);
        });
    }

    /**
     * Handle debug session start
     */
    private handleDebugSessionStart(session: vscode.DebugSession): void {
        console.log('Debug session started:', session.name);
        this.emit('sessionStarted', session);
    }

    /**
     * Handle debug session end
     */
    private handleDebugSessionEnd(session: vscode.DebugSession): void {
        console.log('Debug session ended:', session.name);
        this.emit('sessionEnded', session);

        // Clean up session data
        for (const [id, debugSession] of this.debugSessions.entries()) {
            if (debugSession.processId === parseInt(session.configuration.processId || '0')) {
                this.debugSessions.delete(id);
            }
        }
    }

    /**
     * Cleanup resources
     */
    dispose(): void {
        // Clear all timers
        this.metricsCollectors.forEach(timer => clearInterval(timer as any));
        this.metricsCollectors.clear();

        // Close WebSocket connections
        this.websocketClients.forEach(ws => ws.close());
        this.websocketClients.clear();

        // Clear debug sessions
        this.debugSessions.clear();

        // Clear performance profiles
        this.performanceProfiles.clear();
    }
}

/**
 * Runtime Analysis Integration for ReviewerAgent and FixerBot
 */
export class RuntimeAnalysisIntegration {
    private engine: RuntimeAnalysisEngine;

    constructor(context: vscode.ExtensionContext) {
        this.engine = new RuntimeAnalysisEngine(context);
    }

    /**
     * Enhanced review with runtime analysis
     */
    async performRuntimeReview(processId?: number): Promise<{
        staticIssues: any[];
        runtimeIssues: any[];
        performanceIssues: any[];
        recommendations: string[];
    }> {
        const review = {
            staticIssues: [] as any[],
            runtimeIssues: [] as any[],
            performanceIssues: [] as any[],
            recommendations: [] as string[]
        };

        if (processId) {
            try {
                // Attach to process
                const session = await this.engine.attachToRunningProcess(processId, 'node');

                // Analyze runtime metrics
                const cpuMetrics = await this.engine.analyzeCPUUsage(processId);
                const memoryMetrics = await this.engine.performMemoryProfiling(processId);
                const hotspots = await this.engine.identifyHotspots(session.id);

                // Identify issues
                if (cpuMetrics.usage > 80) {
                    review.performanceIssues.push({
                        type: 'HIGH_CPU',
                        severity: 'high',
                        message: `CPU usage at ${cpuMetrics.usage}%`,
                        recommendation: 'Profile and optimize CPU-intensive operations'
                    });
                }

                if (memoryMetrics.leaks.length > 0) {
                    review.runtimeIssues.push({
                        type: 'MEMORY_LEAK',
                        severity: 'critical',
                        message: `${memoryMetrics.leaks.length} potential memory leaks detected`,
                        leaks: memoryMetrics.leaks,
                        recommendation: 'Review object lifecycle and ensure proper cleanup'
                    });
                }

                hotspots.forEach(hotspot => {
                    review.performanceIssues.push({
                        type: 'HOTSPOT',
                        severity: hotspot.impact > 70 ? 'high' : 'medium',
                        location: hotspot.location,
                        impact: hotspot.impact,
                        recommendation: hotspot.recommendation
                    });
                });

                // Generate recommendations
                review.recommendations.push(
                    ...this.generateRuntimeRecommendations(cpuMetrics, memoryMetrics, hotspots)
                );

            } catch (error) {
                console.error('Runtime analysis error:', error);
                review.runtimeIssues.push({
                    type: 'ANALYSIS_ERROR',
                    severity: 'low',
                    message: `Could not perform runtime analysis: ${(error as any).message}`
                });
            }
        }

        return review;
    }

    /**
     * Generate recommendations based on runtime analysis
     */
    private generateRuntimeRecommendations(
        cpu: CPUMetrics,
        memory: MemoryMetrics,
        hotspots: HotSpot[]
    ): string[] {
        const recommendations: string[] = [];

        // CPU recommendations
        if (cpu.usage > 80) {
            recommendations.push('Consider implementing worker threads for CPU-intensive tasks');
            recommendations.push('Review algorithmic complexity in hot paths');
            recommendations.push('Implement caching for expensive computations');
        }

        // Memory recommendations
        if (memory.leaks.length > 0) {
            recommendations.push('Implement proper cleanup in componentWillUnmount or cleanup functions');
            recommendations.push('Review event listener management');
            recommendations.push('Check for circular references');
        }

        // Hotspot recommendations
        const cpuHotspots = hotspots.filter(h => h.type === 'cpu');
        if (cpuHotspots.length > 0) {
            recommendations.push('Profile identified hotspots with Chrome DevTools');
            recommendations.push('Consider memoization for expensive functions');
        }

        const memoryHotspots = hotspots.filter(h => h.type === 'memory');
        if (memoryHotspots.length > 0) {
            recommendations.push('Review object allocation patterns in hotspots');
            recommendations.push('Consider object pooling for frequently created objects');
        }

        return recommendations;
    }

    /**
     * Get runtime analysis engine for direct access
     */
    getEngine(): RuntimeAnalysisEngine {
        return this.engine;
    }

    /**
     * Dispose resources
     */
    dispose(): void {
        this.engine.dispose();
    }
}