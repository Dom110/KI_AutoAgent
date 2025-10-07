#!/usr/bin/env python3
"""
Comprehensive Codebase Analysis Script
Uses ArchitectAgent's specialized analyzers for dead code detection and cleanup
"""

import asyncio
import sys
import json
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from core.analysis.vulture_analyzer import VultureAnalyzer
from core.analysis.call_graph_analyzer import CallGraphAnalyzer
from core.indexing.code_indexer import CodeIndexer

async def progress_callback(message: str):
    """Print progress messages"""
    print(f"  {message}")

async def analyze_dead_code(root_path: str):
    """Run Vulture dead code analysis"""
    print("\n" + "="*80)
    print("🧹 DEAD CODE ANALYSIS (Vulture)")
    print("="*80)

    analyzer = VultureAnalyzer()

    if not analyzer.vulture_available:
        print("⚠️  Vulture not installed - installing now...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "vulture"], check=False)
        analyzer = VultureAnalyzer()

    result = await analyzer.find_dead_code(
        root_path=root_path,
        progress_callback=progress_callback,
        min_confidence=60  # Only report 60%+ confidence
    )

    return result

async def analyze_call_graph(root_path: str):
    """Run call graph analysis to find unused functions"""
    print("\n" + "="*80)
    print("📊 CALL GRAPH ANALYSIS")
    print("="*80)

    # First build code index
    print("  Building code index...")
    indexer = CodeIndexer()
    code_index = await indexer.build_full_index(
        root_path=root_path,
        progress_callback=progress_callback
    )

    # Then analyze call graph
    print("  Analyzing call graph...")
    analyzer = CallGraphAnalyzer()
    result = await analyzer.build_call_graph(code_index)

    return result

def scan_obsolete_code(root_path: str):
    """Find all OBSOLETE marked code sections"""
    print("\n" + "="*80)
    print("🏷️  OBSOLETE CODE SECTIONS")
    print("="*80)

    obsolete_sections = []
    root = Path(root_path)

    for py_file in root.rglob('*.py'):
        # Skip test files, pycache, backups
        if any(skip in str(py_file) for skip in ['test_', '__pycache__', 'backup', '.pyc']):
            continue

        try:
            content = py_file.read_text(encoding='utf-8')
            lines = content.split('\n')

            in_obsolete = False
            start_line = 0
            obsolete_lines = []

            for i, line in enumerate(lines, 1):
                # Check for OBSOLETE marker
                if 'OBSOLETE' in line and ('v5.' in line or 'deprecated' in line.lower()):
                    if not in_obsolete:
                        in_obsolete = True
                        start_line = i
                        obsolete_lines = [line]
                    else:
                        obsolete_lines.append(line)
                elif in_obsolete:
                    if 'END OBSOLETE' in line or '# ====' in line:
                        obsolete_sections.append({
                            'file': str(py_file.relative_to(root)),
                            'start_line': start_line,
                            'end_line': i,
                            'lines': len(obsolete_lines),
                            'preview': obsolete_lines[0][:100]
                        })
                        in_obsolete = False
                        obsolete_lines = []
                    else:
                        obsolete_lines.append(line)
        except Exception as e:
            print(f"  ⚠️  Error reading {py_file.name}: {e}")

    return obsolete_sections

def scan_cleanup_candidates(root_path: str):
    """Find temporary files, logs, caches that can be cleaned"""
    print("\n" + "="*80)
    print("🗑️  CLEANUP CANDIDATES (Temp/Cache/Logs)")
    print("="*80)

    root = Path(root_path)
    cleanup_candidates = {
        'pycache': [],
        'logs': [],
        'cache': [],
        'temp': [],
        'old_backups': [],
        'pyc_files': []
    }

    # Find __pycache__ directories
    for pycache in root.rglob('__pycache__'):
        cleanup_candidates['pycache'].append(str(pycache.relative_to(root)))

    # Find .pyc files
    for pyc in root.rglob('*.pyc'):
        cleanup_candidates['pyc_files'].append(str(pyc.relative_to(root)))

    # Find log files
    for log in root.rglob('*.log'):
        if log.stat().st_size > 0:
            cleanup_candidates['logs'].append({
                'path': str(log.relative_to(root)),
                'size_mb': log.stat().st_size / (1024 * 1024)
            })

    # Find cache directories
    for cache_dir in ['cache', '.cache', '__cache__']:
        for cache in root.rglob(cache_dir):
            if cache.is_dir():
                cleanup_candidates['cache'].append(str(cache.relative_to(root)))

    # Find temp files
    for pattern in ['*.tmp', '*.temp', '*~', '.DS_Store']:
        for temp in root.rglob(pattern):
            cleanup_candidates['temp'].append(str(temp.relative_to(root)))

    # Find old backup files
    for pattern in ['*.bak', '*.backup', '*.old']:
        for backup in root.rglob(pattern):
            cleanup_candidates['old_backups'].append(str(backup.relative_to(root)))

    return cleanup_candidates

def generate_report(dead_code, call_graph, obsolete, cleanup):
    """Generate comprehensive analysis report"""
    print("\n" + "="*80)
    print("📋 COMPREHENSIVE ANALYSIS REPORT")
    print("="*80)

    report = {
        'dead_code_analysis': dead_code,
        'call_graph_analysis': call_graph,
        'obsolete_sections': obsolete,
        'cleanup_candidates': cleanup
    }

    # Save to JSON
    report_file = Path(__file__).parent / 'CODE_ANALYSIS_REPORT.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ Full report saved to: {report_file}")

    # Print summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)

    # Dead Code Summary
    if dead_code and 'summary' in dead_code:
        summary = dead_code['summary']
        print(f"\n🧹 Dead Code (Vulture):")
        print(f"   Total Dead Code Items: {summary.get('total_dead_code', 0)}")
        print(f"   Unused Functions: {summary.get('unused_functions', 0)}")
        print(f"   Unused Classes: {summary.get('unused_classes', 0)}")
        print(f"   Unused Variables: {summary.get('unused_variables', 0)}")
        print(f"   Unused Imports: {summary.get('unused_imports', 0)}")

    # Call Graph Summary
    if call_graph and 'metrics' in call_graph:
        metrics = call_graph['metrics']
        print(f"\n📊 Call Graph:")
        print(f"   Total Functions: {metrics.get('total_functions', 0)}")
        print(f"   Unused Functions: {len(call_graph.get('unused_functions', []))}")
        print(f"   Entry Points: {len(call_graph.get('entry_points', []))}")

    # OBSOLETE Code
    print(f"\n🏷️  OBSOLETE Code Sections: {len(obsolete)}")
    if obsolete:
        print("   Files with OBSOLETE code:")
        for section in obsolete[:10]:  # Show first 10
            print(f"     - {section['file']} (lines {section['start_line']}-{section['end_line']})")
        if len(obsolete) > 10:
            print(f"     ... and {len(obsolete) - 10} more")

    # Cleanup Candidates
    print(f"\n🗑️  Cleanup Candidates:")
    print(f"   __pycache__ directories: {len(cleanup['pycache'])}")
    print(f"   .pyc files: {len(cleanup['pyc_files'])}")
    print(f"   Log files: {len(cleanup['logs'])}")
    if cleanup['logs']:
        total_log_size = sum(log['size_mb'] for log in cleanup['logs'])
        print(f"     Total log size: {total_log_size:.2f} MB")
    print(f"   Cache directories: {len(cleanup['cache'])}")
    print(f"   Temp files: {len(cleanup['temp'])}")
    print(f"   Old backups: {len(cleanup['old_backups'])}")

    print("\n" + "="*80)
    print("✅ Analysis complete! Review CODE_ANALYSIS_REPORT.json for details.")
    print("="*80)

async def main():
    """Main analysis function"""
    # Analyze backend directory only (no tests, backups, etc.)
    root_path = Path(__file__).parent / 'backend'

    if not root_path.exists():
        print(f"❌ Backend directory not found: {root_path}")
        return

    print("="*80)
    print("🔍 CODEBASE ANALYSIS - Using ArchitectAgent's Tools")
    print("="*80)
    print(f"Analyzing: {root_path}")
    print(f"Backup created: backup-before-cleanup-20251007-095817")
    print("="*80)

    try:
        # 1. Dead Code Analysis
        dead_code = await analyze_dead_code(str(root_path))

        # 2. Call Graph Analysis
        call_graph = await analyze_call_graph(str(root_path))

        # 3. OBSOLETE Code Sections
        obsolete = scan_obsolete_code(str(root_path))

        # 4. Cleanup Candidates
        cleanup = scan_cleanup_candidates(str(root_path))

        # 5. Generate Report
        generate_report(dead_code, call_graph, obsolete, cleanup)

    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
