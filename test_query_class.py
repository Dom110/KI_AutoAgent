#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')

from langgraph_system.query_classifier import EnhancedQueryClassifier

classifier = EnhancedQueryClassifier()

test_queries = [
    "Erstelle eine Whiteboard Web-App",
    "Erstelle eine Todo App",
    "Hallo",
    "Build a game"
]

for query in test_queries:
    result = classifier.classify_query(query, {})
    print(f"\nQuery: {query}")
    print(f"  Greeting: {result.is_greeting}")
    print(f"  Dev Query: {result.is_development_query}")
    print(f"  Action: {result.suggested_action}")
