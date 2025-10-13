# Architecture Decision: Incremental Subgraph Build Strategy

**Date:** 2025-10-08
**Status:** Accepted
**Context:** v6.0 Migration - Phase-by-Phase Implementation

---

## Question

Should we build all subgraphs upfront (even if not connected), or only build subgraphs as they are implemented and connected?

---

## Decision

**We choose: Incremental Build (Only Build What's Used)**

Build and add nodes phase-by-phase, keeping the graph fully connected at all times.

---

## Rationale

### Constraint: LangGraph Validation

LangGraph's `.compile()` **throws ValueError** for unreachable nodes:

```python
# ❌ THIS FAILS:
graph.add_node("research", research_node)
graph.add_node("architect", architect_node)  # Added but unreachable!

graph.add_edge("supervisor", "research")
graph.add_edge("research", END)  # architect not in routing!

graph.compile()  # ValueError: Node `architect` is not reachable
```

**LangGraph requires:** Every node must be reachable from the entry point.

### Why Incremental Build is Correct

#### ✅ Advantages:

1. **No Unreachable Nodes**
   - Every node in the graph is reachable
   - Graph compiles successfully at every phase
   - LangGraph validation passes

2. **Performance**
   - Only build subgraphs that are actually used
   - Faster initialization (no wasted builds)
   - No placeholder logic executed

3. **Clear Implementation Status**
   - Commented out = not implemented yet
   - Present in code = implemented and tested
   - No confusion about what works

4. **Phase-by-Phase Testing**
   - Each phase tests only completed functionality
   - No half-baked placeholder nodes
   - Clean test boundaries

5. **Clean Architecture**
   - No dead code in the compiled graph
   - Clear separation of concerns
   - Easy to see migration progress

#### ❌ Alternative: "Build All Upfront" Problems:

1. **LangGraph Compilation Error**
   - Unreachable nodes cause ValueError
   - Must connect all nodes immediately
   - Forces incomplete implementations

2. **Wasted Resources**
   - Building placeholder subgraphs every init
   - Memory/CPU for unused components
   - Slows down development iteration

3. **Confusing Implementation State**
   - All nodes exist but some are placeholders
   - Hard to know what actually works
   - Testing includes incomplete code

---

## Implementation Pattern

### Phase-by-Phase Approach:

```python
# Phase 3: Research Only
def _build_workflow(self):
    research_subgraph = self._build_research_subgraph()
    # architect_subgraph = self._build_architect_subgraph()  # TODO Phase 4
    # codesmith_subgraph = self._build_codesmith_subgraph()  # TODO Phase 5
    # reviewfix_subgraph = self._build_reviewfix_subgraph()  # TODO Phase 6

    graph.add_node("research", research_node_wrapper)
    # Only research node exists

    graph.add_edge("supervisor", "research")
    graph.add_edge("research", END)
    # research is reachable ✅

# Phase 4: Research + Architect
def _build_workflow(self):
    research_subgraph = self._build_research_subgraph()
    architect_subgraph = self._build_architect_subgraph()  # ✅ Uncommented!
    # codesmith_subgraph = self._build_codesmith_subgraph()  # TODO Phase 5
    # reviewfix_subgraph = self._build_reviewfix_subgraph()  # TODO Phase 6

    graph.add_node("research", research_node_wrapper)
    graph.add_node("architect", architect_node_wrapper)  # ✅ Added!

    graph.add_edge("supervisor", "research")
    graph.add_edge("research", "architect")  # ✅ New edge!
    graph.add_edge("architect", END)
    # Both nodes reachable ✅

# Phase 7: Full Workflow
def _build_workflow(self):
    research_subgraph = self._build_research_subgraph()
    architect_subgraph = self._build_architect_subgraph()
    codesmith_subgraph = self._build_codesmith_subgraph()
    reviewfix_subgraph = self._build_reviewfix_subgraph()

    graph.add_node("research", research_node_wrapper)
    graph.add_node("architect", architect_node_wrapper)
    graph.add_node("codesmith", codesmith_node_wrapper)
    graph.add_node("reviewfix", reviewfix_node_wrapper)

    graph.add_edge("supervisor", "research")
    graph.add_edge("research", "architect")
    graph.add_edge("architect", "codesmith")
    graph.add_edge("codesmith", "reviewfix")
    graph.add_edge("reviewfix", END)
    # All nodes reachable ✅
```

---

## Migration Path

### Current State (Phase 4):
```
supervisor → research → architect → END
```
- ✅ Research implemented and tested
- ✅ Architect implemented and tested
- ⏳ Codesmith TODO (Phase 5)
- ⏳ ReviewFix TODO (Phase 6)

### Phase 5:
```
supervisor → research → architect → codesmith → END
```
1. Implement codesmith_subgraph_v6.py
2. Uncomment `codesmith_subgraph = self._build_codesmith_subgraph()`
3. Add codesmith_node_wrapper
4. Update routing: `architect → codesmith → END`

### Phase 6:
```
supervisor → research → architect → codesmith → reviewfix → END
```
1. Implement reviewfix_subgraph_v6.py
2. Uncomment `reviewfix_subgraph = self._build_reviewfix_subgraph()`
3. Add reviewfix_node_wrapper
4. Update routing: `codesmith → reviewfix → END`

### Phase 7: Complete
```
supervisor → research → architect → codesmith → reviewfix → END
```
All nodes implemented, connected, and reachable.

---

## Consequences

### Positive:

- ✅ No LangGraph compilation errors
- ✅ Clean phase boundaries
- ✅ Only test what's implemented
- ✅ Easy to see progress (uncommented = done)
- ✅ Better performance (no wasted builds)

### Negative:

- ⚠️ More code changes between phases (uncomment + add edges)
- ⚠️ Could look "incomplete" (commented TODOs)
- ⚠️ Each phase modifies routing logic

### Mitigation:

- Document incremental approach clearly
- Use clear TODO comments with phase numbers
- Test after each phase to ensure no regressions

---

## Alternatives Considered

### Alternative 1: Build All Upfront, Conditionally Connect

```python
research_subgraph = self._build_research_subgraph()
architect_subgraph = self._build_architect_subgraph()  # Always built
codesmith_subgraph = self._build_codesmith_subgraph()  # Always built
reviewfix_subgraph = self._build_reviewfix_subgraph()  # Always built

# Only connect implemented nodes
if PHASE >= 3:
    graph.add_node("research", research_node)
if PHASE >= 4:
    graph.add_node("architect", architect_node)
# etc.
```

**Rejected because:**
- Still builds unused subgraphs (performance)
- Adds complexity (phase flags)
- Harder to test (conditional logic)

### Alternative 2: Feature Flags

```python
if FEATURE_ARCHITECT_ENABLED:
    architect_subgraph = self._build_architect_subgraph()
    graph.add_node("architect", architect_node)
```

**Rejected because:**
- Over-engineering for migration scenario
- Not needed once migration complete
- Phase-based approach is simpler

---

## References

- LangGraph Documentation: Graph Validation
- V6_0_MIGRATION_PLAN.md: Phase-by-Phase Strategy
- PHASE_3_COMPLETE.md: Lazy Initialization Pattern

---

## Review

This decision should be reviewed:
- ✅ After each phase (4, 5, 6, 7)
- ✅ Once migration complete (Phase 8)
- ❓ If LangGraph changes validation rules
- ❓ If performance becomes an issue

**Last Reviewed:** 2025-10-08 (Phase 4 complete)
