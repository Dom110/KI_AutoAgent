"""
SIMULATION: StreamReader-basiertes stdin ohne Timeout
======================================================

Testet das neue Pattern für MCP Server stdin-Handling.
Kernel: asyncio.StreamReader statt asyncio.wait_for()

Best Practice Research:
- https://docs.python.org/3/library/asyncio-stream.html
- StreamReader.readline() wartet auf EOF ohne Timeout
- EOF Erkennung: reader.at_eof() oder empty bytes "" von readline()
- Kein Timeout = Cleanere Architektur
"""

import asyncio
import sys
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger("streamreader_test")


async def create_stdin_reader() -> asyncio.StreamReader:
    """
    🔧 Erstellt einen StreamReader für stdin
    
    Best Practice:
    - Nutzt die Event Loop um stdin zu registrieren
    - Erlaubt async readline() ohne Blocking
    - Supportet EOF-Detection nativ
    """
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    
    def read_stdin():
        """Blocking read helper für stdin"""
        try:
            # sys.stdin.read(1) liest 1 Byte blocking
            # Das ist OK weil es in Executor läuft
            data = sys.stdin.read(1)
            logger.debug(f"[stdin] Raw read: {repr(data)}")
            return data
        except Exception as e:
            logger.error(f"[stdin] Error reading: {type(e).__name__}: {e}")
            return ""
    
    # Starte Background Task die stdin liest und in StreamReader schreibt
    async def fill_reader():
        """Liest kontinuierlich von stdin in den StreamReader"""
        logger.info("[reader] Starting stdin fill task")
        while True:
            try:
                # Non-blocking lese-operation via executor
                data = await loop.run_in_executor(None, read_stdin)
                
                if not data:
                    logger.info("[reader] EOF detected (empty read)")
                    reader.feed_eof()
                    break
                
                logger.debug(f"[reader] Feed {len(data)} bytes")
                reader.feed_data(data.encode() if isinstance(data, str) else data)
                
            except Exception as e:
                logger.error(f"[reader] Error in fill_reader: {type(e).__name__}: {e}")
                reader.feed_eof()
                break
    
    # Starte den Fill Task im Background (fire and forget)
    asyncio.create_task(fill_reader())
    
    return reader


async def async_stdin_readline_v2() -> str:
    """
    ✅ NEU: StreamReader-basiertes stdin.readline() OHNE Timeout
    
    Advantages:
    1. Kein Timeout → Keine False Positives
    2. Native EOF-Unterstützung
    3. Clean asyncio Pattern
    4. Skaliert für lange-laufende Tasks
    """
    try:
        loop = asyncio.get_running_loop()
        
        logger.debug("[v2] Waiting for stdin line...")
        
        # Hier der Trick: Nutze loop.run_in_executor um blocking readline() 
        # aber OHNE Timeout
        line = await loop.run_in_executor(None, sys.stdin.readline)
        
        if line:
            logger.debug(f"[v2] Got line: {repr(line[:60])}")
        else:
            logger.debug("[v2] EOF (empty line)")
        
        return line
        
    except Exception as e:
        logger.error(f"[v2] Unexpected error: {type(e).__name__}: {e}")
        return ""


async def async_stdin_readline_v3() -> str:
    """
    ✅ BESSER: Mit StreamReader für True Non-Blocking
    
    Dieser Ansatz funktioniert aber braucht stdin als StreamReader
    Deshalb: Simulation mit Mock-Reader
    """
    try:
        logger.debug("[v3] Using StreamReader pattern")
        
        # In echter Implementation würde das sein:
        # reader = await create_stdin_reader()
        # line = await reader.readline()
        # if not line:
        #     logger.info("[v3] EOF detected")
        # return line.decode()
        
        # Für Simulation: Nutze echo oder Test-Input
        # In Production: Würde stdin zu StreamReader sein
        logger.debug("[v3] (Simulation) Would use StreamReader.readline()")
        return "test\n"
        
    except Exception as e:
        logger.error(f"[v3] Unexpected error: {type(e).__name__}: {e}")
        return ""


async def test_v2_pattern():
    """Test des verbesserten Patterns ohne Timeout"""
    logger.info("=" * 80)
    logger.info("TEST V2: run_in_executor WITHOUT timeout")
    logger.info("=" * 80)
    
    # Test 1: Normal input
    logger.info("\n✅ TEST 1: Reading normal input")
    logger.info("Please type something and press Enter (test input):")
    
    # Für Automated Testing: Simuliere Input
    # In echter Verwendung würde User input liefern
    
    logger.info("(Skipped - würde auf User Input warten)")
    
    logger.info("\n" + "=" * 80)


async def test_metrics():
    """Vergleich der Patterns"""
    logger.info("\n📊 PATTERN COMPARISON:")
    logger.info("""
    ┌─────────────────────────────────────────────────────┐
    │ V1: wait_for(executor, timeout=300)                 │
    ├─────────────────────────────────────────────────────┤
    │ ✅ Verhindert Infinite Block                         │
    │ ❌ 300s Timeout ist willkürlich                       │
    │ ❌ Unterbricht lange-laufende Operations            │
    │ ⚠️  False Timeouts bei langsamen Systemen            │
    └─────────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────────┐
    │ V2: run_in_executor OHNE timeout (EMPFOHLEN)        │
    ├─────────────────────────────────────────────────────┤
    │ ✅ Keine Timeouts                                    │
    │ ✅ Saubere asyncio Integration                       │
    │ ✅ Wartet auf echtes EOF vom Parent Process          │
    │ ✅ Skaliert für long-running Tasks                   │
    │ ❌ Braucht Graceful Shutdown Handling                │
    └─────────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────────┐
    │ V3: StreamReader (IDEAL aber komplexer)            │
    ├─────────────────────────────────────────────────────┤
    │ ✅ True Non-Blocking                                │
    │ ✅ Native EOF-Detection                             │
    │ ✅ Keine Executor-Overhead                          │
    │ ❌ Braucht stdin als StreamReader (komplexer)       │
    │ ❌ Plattform-spezifische Implementierung            │
    └─────────────────────────────────────────────────────┘
    """)


async def main():
    """Main test runner"""
    logger.info("🧪 SIMULATION: Async Stdin Patterns ohne Timeout")
    logger.info(f"Start: {datetime.now()}")
    
    await test_metrics()
    
    logger.info("\n✅ Recommendation für MCP Servers:")
    logger.info("""
    1. V2 Pattern verwenden: run_in_executor OHNE timeout
    2. Graceful Shutdown implementieren:
       - Signal Handler für SIGTERM/SIGINT
       - Cleanup bei EOF
    3. Logging:
       - [stdin] prefix für alle stdin ops
       - Debug logs für EOF detection
    4. Keine Timeouts = Saubere Architektur
    """)
    
    logger.info(f"End: {datetime.now()}")


if __name__ == "__main__":
    asyncio.run(main())
