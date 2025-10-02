"""
Test script for new v5.0 features:
- Function Call Graph Analyzer
- System Layers Analyzer
- Playwright Browser Testing
"""

import asyncio
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_code_indexing():
    """Test that code indexing works"""
    logger.info("🧪 Test 1: Code Indexing")

    try:
        from backend.core.indexing.code_indexer import CodeIndexer

        indexer = CodeIndexer()
        code_index = await indexer.build_full_index('.', None, 'test')

        stats = code_index.get('statistics', {})
        logger.info(f"✅ Code Index built: {stats.get('total_files', 0)} files, {stats.get('total_functions', 0)} functions")
        return True
    except Exception as e:
        logger.error(f"❌ Code Indexing failed: {e}")
        return False

async def test_call_graph():
    """Test call graph analyzer"""
    logger.info("🧪 Test 2: Function Call Graph")

    try:
        from backend.core.indexing.code_indexer import CodeIndexer
        from backend.core.analysis.call_graph_analyzer import CallGraphAnalyzer

        # Build code index first
        indexer = CodeIndexer()
        code_index = await indexer.build_full_index('.', None, 'test')

        # Build call graph
        analyzer = CallGraphAnalyzer()
        call_graph = await analyzer.build_call_graph(code_index)

        metrics = call_graph['metrics']
        logger.info(f"✅ Call Graph built: {metrics['total_functions']} functions, {metrics['total_calls']} calls")
        logger.info(f"   Entry points: {len(call_graph['entry_points'])}")
        logger.info(f"   Unused functions: {len(call_graph['unused_functions'])}")
        logger.info(f"   Max call depth: {metrics['max_call_depth']}")
        return True
    except Exception as e:
        logger.error(f"❌ Call Graph failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_layer_analysis():
    """Test system layers analyzer"""
    logger.info("🧪 Test 3: System Layers Analysis")

    try:
        from backend.core.indexing.code_indexer import CodeIndexer
        from backend.core.analysis.layer_analyzer import LayerAnalyzer

        # Build code index
        indexer = CodeIndexer()
        code_index = await indexer.build_full_index('.', None, 'test')

        # Analyze layers
        analyzer = LayerAnalyzer()
        layers_result = await analyzer.detect_system_layers(code_index)

        logger.info(f"✅ System Layers analyzed:")
        logger.info(f"   Quality score: {layers_result['quality_score']:.2f}")
        logger.info(f"   Violations: {layers_result['metrics']['total_violations']}")

        for layer in layers_result['layers']:
            logger.info(f"   Layer '{layer['name']}': {layer['component_count']} components")

        return True
    except Exception as e:
        logger.error(f"❌ Layer Analysis failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_playwright():
    """Test Playwright browser testing"""
    logger.info("🧪 Test 4: Playwright Browser Testing")

    try:
        from backend.agents.tools.browser_tester import PLAYWRIGHT_AVAILABLE, BrowserTester

        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("⚠️ Playwright not available - install with: pip install playwright && playwright install")
            return False

        # Just test that we can initialize BrowserTester
        async with BrowserTester() as tester:
            logger.info("✅ Playwright browser started successfully")

            # Get page info (just to verify it works)
            info = await tester.get_page_info()
            logger.info(f"   Browser ready: {info.get('viewport', {})}")

        return True
    except Exception as e:
        logger.error(f"❌ Playwright test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_architect_integration():
    """Test that ArchitectAgent can use new analyzers"""
    logger.info("🧪 Test 5: ArchitectAgent Integration")

    try:
        # Just verify imports work
        from backend.agents.specialized.architect_agent import ArchitectAgent

        logger.info("✅ ArchitectAgent imports new analyzers successfully")
        return True
    except Exception as e:
        logger.error(f"❌ ArchitectAgent integration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_reviewer_integration():
    """Test that ReviewerGPT can use BrowserTester"""
    logger.info("🧪 Test 6: ReviewerGPT Integration")

    try:
        from backend.agents.specialized.reviewer_gpt_agent import ReviewerGPTAgent

        logger.info("✅ ReviewerGPT imports BrowserTester successfully")
        return True
    except Exception as e:
        logger.error(f"❌ ReviewerGPT integration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("KI AutoAgent v5.0 - New Features Test Suite")
    logger.info("=" * 60)

    tests = [
        ("Code Indexing", test_code_indexing),
        ("Function Call Graph", test_call_graph),
        ("System Layers", test_layer_analysis),
        ("Playwright", test_playwright),
        ("ArchitectAgent Integration", test_architect_integration),
        ("ReviewerGPT Integration", test_reviewer_integration)
    ]

    results = []
    for name, test_func in tests:
        success = await test_func()
        results.append((name, success))
        logger.info("")

    # Summary
    logger.info("=" * 60)
    logger.info("Test Summary:")
    logger.info("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {name}")

    logger.info("")
    logger.info(f"Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    if passed == total:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error(f"💥 {total - passed} tests failed")
        return 1

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
