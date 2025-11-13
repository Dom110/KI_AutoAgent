# Shared Multi-Agent Collaboration Protocols v2.0

## Overview
This document defines the shared protocols that all agents must follow for effective collaboration, memory sharing, and conflict resolution in the KI_AutoAgent system.

## Core Principles

1. **Shared Context First**: Always check shared context before starting any task
2. **Memory Before Action**: Search memory for similar tasks before executing
3. **Collaborate Don't Compete**: Work together, share knowledge freely
4. **Learn Continuously**: Extract patterns and store learnings from every task
5. **Fail Gracefully**: Handle errors collaboratively and learn from failures

## Communication Protocol

### Message Types and When to Use Them

#### REQUEST
Use when you need another agent to perform a task:
```javascript
await communicationBus.send({
  from: 'your-agent-id',
  to: 'target-agent-id',
  type: MessageType.REQUEST,
  content: {
    task: 'Validate this architecture',
    data: architectureSpec
  },
  metadata: {
    priority: 'high',
    requiresResponse: true,
    timeout: 30000
  }
});
```

#### HELP_REQUEST
Use when stuck or need expertise:
```javascript
await communicationBus.requestHelp(
  'your-agent-id',
  {
    problem: 'Cannot resolve dependency conflict',
    context: currentContext,
    attemptedSolutions: [...],
    preferredAgents: ['fixer', 'architect']
  }
);
```

#### KNOWLEDGE_SHARE
Broadcast important discoveries:
```javascript
await communicationBus.shareKnowledge(
  'your-agent-id',
  {
    discovery: 'New optimization pattern found',
    pattern: optimizationCode,
    metrics: performanceGains,
    applicability: ['api', 'database']
  },
  relevantAgents // optional, broadcasts to all if not specified
);
```

#### VALIDATION_REQUEST
Request validation from specific agent:
```javascript
await communicationBus.requestValidation(
  'your-agent-id',
  'reviewer',
  {
    type: 'security',
    code: implementation,
    context: securityRequirements
  }
);
```

#### CONFLICT
Report conflicts requiring arbitration:
```javascript
await communicationBus.reportConflict(
  'your-agent-id',
  ['agent1', 'agent2'],
  {
    issue: 'Disagreement on architecture pattern',
    positions: {
      agent1: 'Microservices needed',
      agent2: 'Monolith sufficient'
    },
    impact: 'Blocks implementation'
  }
);
```

## Shared Context Management

### What to Share
All agents MUST update shared context with:

#### Critical Information (Always Share)
- Major decisions that affect other agents
- Errors that might impact others
- Resource constraints discovered
- Security issues found
- Performance bottlenecks identified

#### Project State (Update Regularly)
- Current task progress
- Completed milestones
- Blocking issues
- Test results
- Performance metrics

### How to Share

#### Update Context
```javascript
// For important updates that others need to know
await sharedContext.updateContext(
  'your-agent-id',
  'architectureDecisions',
  {
    decision: 'Use event-driven architecture',
    reasoning: 'Need real-time updates',
    impact: 'All services must implement event handlers',
    timestamp: Date.now()
  },
  {
    confidence: 0.9,
    dependencies: ['message-bus-setup']
  }
);
```

#### Read Context
```javascript
// Always check context before starting work
const context = sharedContext.getContext();
const architecture = context.architectureDecisions;
const currentTasks = context.activeTasks;
const knownIssues = context.blockers;
```

#### Subscribe to Updates
```javascript
// Listen for relevant updates
sharedContext.subscribe(
  'your-agent-id',
  (update) => {
    if (update.key === 'architectureDecisions') {
      // Adjust your approach based on new architecture
      adaptToArchitecture(update.value);
    }
  },
  // Optional filter
  (update) => update.key.includes('architecture') || update.key.includes('your-domain')
);
```

## Memory Management Protocol

### What to Remember

#### Always Store
1. **Successful Patterns**: Code, architectures, workflows that worked
2. **Failures and Solutions**: Problems encountered and how they were solved
3. **Performance Metrics**: Execution times, resource usage, bottlenecks
4. **User Preferences**: Specific requirements, communication styles
5. **Collaboration Patterns**: Which agents work well together

#### Memory Types and Usage

```javascript
// Episodic Memory - Specific events
await memoryManager.store(
  'your-agent-id',
  {
    task: 'API implementation',
    approach: 'REST with JWT',
    result: 'Success',
    duration: 5000
  },
  MemoryType.EPISODIC,
  { importance: 0.7 }
);

// Procedural Memory - How to do things
await memoryManager.store(
  'your-agent-id',
  {
    procedure: 'Database optimization',
    steps: [...],
    prerequisites: [...],
    outcomes: [...]
  },
  MemoryType.PROCEDURAL,
  { importance: 0.9 }
);

// Semantic Memory - General knowledge
await memoryManager.store(
  'your-agent-id',
  {
    concept: 'Microservices pros/cons',
    knowledge: {...},
    sources: [...]
  },
  MemoryType.SEMANTIC,
  { importance: 0.8 }
);
```

### Memory Search Before Action

```javascript
// Always search memory before starting new tasks
const similar = await memoryManager.search(currentTask, {
  k: 10,
  type: MemoryType.EPISODIC,
  minSimilarity: 0.7
});

if (similar.length > 0 && similar[0].similarity > 0.85) {
  // Reuse previous solution with adaptations
  const previousSolution = similar[0].entry.content;
  return adaptSolution(previousSolution, currentTask);
}
```

## Collaboration Workflow

### Starting a Collaboration Session

When multiple agents need to work together:

```javascript
// 1. Orchestrator initiates collaboration
const session = await communicationBus.startCollaboration(
  {
    task: 'Build trading system',
    requirements: [...],
    deadline: Date.now() + 3600000
  },
  ['architect', 'codesmith', 'tradestrat', 'reviewer'],
  'orchestrator' // leader
);

// 2. Each agent prepares
async function prepareForCollaboration(task) {
  // Gather relevant knowledge
  const relevantMemories = await searchMemory(task);
  const capabilities = getMyCapabilities();

  // Update collaboration context
  await updateCollaborationContext(session.id, 'ready', {
    agent: 'your-agent-id',
    capabilities,
    relevantKnowledge: relevantMemories
  });

  return { ready: true };
}

// 3. During collaboration
async function collaborationWork(session) {
  // Share progress
  await collaborationMessage(
    session.id,
    'your-agent-id',
    { progress: 'Completed component design' },
    MessageType.STATUS_UPDATE
  );

  // Request help if needed
  if (needHelp) {
    await collaborationMessage(
      session.id,
      'your-agent-id',
      { need: 'Performance optimization expertise' },
      MessageType.HELP_REQUEST
    );
  }
}
```

## Conflict Resolution Protocol

### Detecting Conflicts

Conflicts occur when:
- Two agents propose incompatible solutions
- Resource constraints prevent both approaches
- Requirements interpretation differs
- Technical approaches fundamentally disagree

### Resolution Process

```javascript
// 1. Try to resolve locally
async function resolveLocally(conflict) {
  // Check if one solution clearly better
  const metrics = compareSolutions(conflict.solutions);
  if (metrics.clearWinner) {
    return metrics.best;
  }

  // Try to merge approaches
  const merged = attemptMerge(conflict.solutions);
  if (merged.viable) {
    return merged.solution;
  }

  return null;
}

// 2. Escalate to OpusArbitrator if needed
async function escalateConflict(conflict) {
  await communicationBus.reportConflict(
    'your-agent-id',
    conflict.parties,
    {
      issue: conflict.description,
      attempts: conflict.resolutionAttempts,
      impact: conflict.businessImpact,
      urgency: conflict.deadline
    }
  );
}

// 3. Accept arbitration decision
async function acceptArbitration(decision) {
  // Store decision for future reference
  await memoryManager.store(
    'your-agent-id',
    {
      conflict: conflict.description,
      decision: decision.ruling,
      reasoning: decision.explanation
    },
    MemoryType.EPISODIC,
    { importance: 1.0 }
  );

  // Implement decision
  await implementDecision(decision);
}
```

## Error Handling Protocol

### When Errors Occur

```javascript
async function handleError(error, context) {
  // 1. Log and store
  await memoryManager.store(
    'your-agent-id',
    {
      error: error.message,
      stack: error.stack,
      context,
      timestamp: Date.now()
    },
    MemoryType.EPISODIC,
    { importance: 0.9, type: 'error' }
  );

  // 2. Update shared context
  await sharedContext.updateContext(
    'your-agent-id',
    'current_error',
    {
      error: error.message,
      agent: 'your-agent-id',
      impact: assessImpact(error),
      needsHelp: true
    }
  );

  // 3. Request help if cannot resolve
  if (!canHandleError(error)) {
    const help = await communicationBus.requestHelp(
      'your-agent-id',
      {
        error: error.message,
        tried: attemptedSolutions,
        context
      }
    );

    if (help && help.length > 0) {
      return applySolution(help[0]);
    }
  }

  // 4. Graceful degradation
  return fallbackSolution(context);
}
```

## Learning Protocol

### After Each Task

```javascript
async function postTaskLearning(task, result) {
  // 1. Evaluate success
  const metrics = {
    success: result.status === 'success',
    duration: result.duration,
    quality: assessQuality(result),
    resourceUsage: measureResources(result)
  };

  // 2. Extract patterns
  if (metrics.success && metrics.quality > 0.8) {
    const pattern = extractPattern(task, result);
    await storePattern(pattern);
  }

  // 3. Record learnings
  const learnings = identifyLearnings(task, result, metrics);
  for (const learning of learnings) {
    await recordLearning(
      learning.type,
      learning.description,
      learning.context
    );
  }

  // 4. Share insights
  if (learnings.some(l => l.importance === 'high')) {
    await communicationBus.shareKnowledge(
      'your-agent-id',
      {
        learnings,
        applicableToAgents: identifyRelevantAgents(learnings)
      }
    );
  }
}
```

## Performance Optimization Protocol

### Monitoring and Optimization

```javascript
// Track performance metrics
const performanceMonitor = {
  async trackExecution(task, execution) {
    const startTime = Date.now();
    const startMemory = process.memoryUsage();

    const result = await execution();

    const metrics = {
      duration: Date.now() - startTime,
      memory: process.memoryUsage().heapUsed - startMemory.heapUsed,
      success: result.status === 'success'
    };

    // Store metrics for analysis
    await storePerformanceMetrics(task, metrics);

    // Alert if performance degraded
    if (metrics.duration > expectedDuration * 1.5) {
      await alertPerformanceIssue(task, metrics);
    }

    return result;
  }
};
```

## Quality Assurance Protocol

### Before Completing Any Task

```javascript
const qualityChecklist = {
  async validate(work, type) {
    const checks = [];

    // Universal checks
    checks.push(await checkCompleteness(work));
    checks.push(await checkErrorHandling(work));
    checks.push(await checkPerformance(work));

    // Type-specific checks
    switch(type) {
      case 'code':
        checks.push(await checkCodeQuality(work));
        checks.push(await checkTests(work));
        checks.push(await checkSecurity(work));
        break;
      case 'architecture':
        checks.push(await checkScalability(work));
        checks.push(await checkMaintainability(work));
        break;
      // ... more types
    }

    // Request validation if critical
    if (work.critical) {
      const validation = await requestValidation(
        'your-agent-id',
        'reviewer',
        work
      );
      checks.push(validation);
    }

    return {
      passed: checks.every(c => c.passed),
      issues: checks.filter(c => !c.passed)
    };
  }
};
```

## Agent Lifecycle Hooks

### Initialization
```javascript
async function onInit() {
  // Register with communication bus
  registerCommunicationHandlers();

  // Subscribe to shared context
  subscribeToContextUpdates();

  // Load relevant memories
  await loadRecentMemories();

  // Announce availability
  await announceReady();
}
```

### Task Start
```javascript
async function onTaskStart(task) {
  // Check shared context
  const context = await getSharedContext();

  // Search memory
  const relevant = await searchMemory(task);

  // Update status
  await updateStatus('working', task);

  return { context, memories: relevant };
}
```

### Task Complete
```javascript
async function onTaskComplete(task, result) {
  // Store in memory
  await storeTaskMemory(task, result);

  // Update shared context
  await updateSharedContext('completed_task', result);

  // Learn from experience
  await postTaskLearning(task, result);

  // Clean up resources
  await cleanup();
}
```

### Shutdown
```javascript
async function onShutdown() {
  // Save important memories
  await persistMemories();

  // Notify other agents
  await broadcastShutdown();

  // Unregister handlers
  unregisterAllHandlers();
}
```

## Best Practices

1. **Always Check Context First**: Never start work without checking shared context
2. **Memory Over Computation**: Reuse previous solutions when similarity > 85%
3. **Fail Fast, Recover Smart**: Don't hide errors, share them for collaborative solving
4. **Document Decisions**: Store reasoning with every major decision
5. **Continuous Learning**: Extract patterns from both successes and failures
6. **Proactive Communication**: Share discoveries before being asked
7. **Respect Arbitration**: Accept OpusArbitrator decisions as final
8. **Optimize Collaboratively**: Share performance improvements with all agents

Remember: The strength of the multi-agent system lies not in individual agent capabilities, but in how well agents work together, share knowledge, and learn collectively.