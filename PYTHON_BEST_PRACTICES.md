# 🐍 Python Best Practices für KI AutoAgent

**Version:** 1.0.0
**Python Target:** 3.13+
**Letzte Aktualisierung:** 2025-10-07

Dieses Dokument definiert verbindliche Standards für alle Python-Entwicklung im KI AutoAgent Projekt, basierend auf modernen Best Practices aus der Python Community 2024/2025.

---

## 📑 Inhaltsverzeichnis

1. [Python 3.13 Features](#python-313-features)
2. [Error Handling](#error-handling)
3. [Type Hints & Type Safety](#type-hints--type-safety)
4. [Context Managers & Resource Management](#context-managers--resource-management)
5. [Async/Await Patterns](#asyncawait-patterns)
6. [Clean Code Principles](#clean-code-principles)
7. [Anti-Patterns zu vermeiden](#anti-patterns-zu-vermeiden)
8. [Code Review Checklist](#code-review-checklist)

---

## 🚀 Python 3.13 Features

### Verfügbare Features (nutzen!)

#### 1. Native Union Types (`|`)
```python
# ✅ RICHTIG (Python 3.10+)
def process(data: str | int | None) -> dict | None:
    pass

# ❌ FALSCH (veraltet)
from typing import Union, Optional
def process(data: Union[str, int, None]) -> Optional[dict]:
    pass
```

#### 2. Native Generic Types
```python
# ✅ RICHTIG (Python 3.9+)
def process_items(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}

# ❌ FALSCH (veraltet)
from typing import List, Dict
def process_items(items: List[str]) -> Dict[str, int]:
    pass
```

#### 3. Enhanced Error Messages
```python
# Python 3.13 hat verbesserte Fehlerausgaben mit Farben im REPL
# Nutze dies beim Debugging!
```

#### 4. JIT Compiler & Free-Threading
```python
# Python 3.13 unterstützt:
# - JIT compilation für Performance
# - Free-threaded execution (--disable-gil)
#
# Für Multi-Threading intensive Tasks relevant
```

---

## 🛡️ Error Handling

### Grundprinzipien

**1. Be Specific with Exceptions**

```python
# ❌ FALSCH - Zu breit
try:
    result = dangerous_operation()
except Exception as e:
    logger.error(f"Error: {e}")

# ✅ RICHTIG - Spezifisch
try:
    result = dangerous_operation()
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
except PermissionError as e:
    logger.error(f"Permission denied: {e}")
except ValueError as e:
    logger.error(f"Invalid value: {e}")
```

**2. Minimize Try Block Scope**

```python
# ❌ FALSCH - Zu viel im try Block
try:
    data = load_config()
    validated = validate_data(data)
    processed = process_data(validated)
    result = save_result(processed)
    logger.info("All done!")
except Exception as e:
    # Welche Zeile hat gefailed? Unklar!
    logger.error(f"Something failed: {e}")

# ✅ RICHTIG - Kleine, fokussierte try Blöcke
try:
    data = load_config()
except ConfigError as e:
    logger.error(f"Config loading failed: {e}")
    raise

try:
    validated = validate_data(data)
except ValidationError as e:
    logger.error(f"Data validation failed: {e}")
    raise

# ... etc
```

**3. Use the `else` Clause**

```python
# ✅ RICHTIG - else für Success Path
try:
    file = open("data.json")
except FileNotFoundError:
    logger.error("File not found")
    use_default_data()
else:
    # Nur wenn kein Error aufgetreten ist
    data = json.load(file)
    process_data(data)
finally:
    # Cleanup - immer ausgeführt
    if 'file' in locals():
        file.close()
```

**4. Context Managers > try-finally**

```python
# ❌ FALSCH - Manuelles Resource Management
file = None
try:
    file = open("data.txt")
    data = file.read()
    process(data)
except IOError as e:
    logger.error(f"IO Error: {e}")
finally:
    if file:
        file.close()

# ✅ RICHTIG - Context Manager
try:
    with open("data.txt") as file:
        data = file.read()
        process(data)
except IOError as e:
    logger.error(f"IO Error: {e}")
```

**5. Initialize Variables Before try Block**

```python
# ❌ FALSCH - UnboundLocalError Risk
try:
    result = agent.execute(task)
    content = result.content
    data = parse_content(content)
except ExecutionError as e:
    logger.error(f"Failed: {e}")
    fallback = content[:100]  # ❌ content existiert nicht wenn parse_content failed!

# ✅ RICHTIG - Initialize First
result: AgentResult | None = None
content: str | None = None
data: dict | None = None

try:
    result = agent.execute(task)
    content = result.content
    data = parse_content(content)
except ExecutionError as e:
    logger.error(f"Failed: {e}")
    fallback = content[:100] if content else "No content available"  # ✅ Safe!
```

**6. EAFP - Easier to Ask Forgiveness than Permission**

```python
# ❌ FALSCH - LBYL (Look Before You Leap)
if os.path.exists(file_path):
    if os.access(file_path, os.R_OK):
        with open(file_path) as f:
            data = f.read()

# ✅ RICHTIG - EAFP
try:
    with open(file_path) as f:
        data = f.read()
except FileNotFoundError:
    logger.error("File not found")
except PermissionError:
    logger.error("Permission denied")
```

**7. Avoid Exception Silencing**

```python
# ❌ FALSCH - Silent Failure
try:
    result = risky_operation()
except Exception:
    pass  # ❌ Bugs werden verschluckt!

# ✅ RICHTIG - Explicit Handling
try:
    result = risky_operation()
except ExpectedException as e:
    logger.warning(f"Expected error occurred: {e}")
    result = default_value
except UnexpectedException as e:
    logger.error(f"Unexpected error: {e}")
    raise  # Re-raise für debugging
```

**8. Custom Exceptions für Domain Logic**

```python
# ✅ RICHTIG - Custom Exceptions
class ArchitectError(Exception):
    """Base exception for Architect Agent"""
    pass

class ArchitectValidationError(ArchitectError):
    """Raised when architecture validation fails"""
    pass

class ArchitectResearchError(ArchitectError):
    """Raised when research step fails"""
    pass

# Usage
try:
    architecture = architect.design(requirements)
except ArchitectValidationError as e:
    logger.error(f"Validation failed: {e}")
    # Spezifische Behandlung für Validation Errors
except ArchitectResearchError as e:
    logger.warning(f"Research failed, using defaults: {e}")
    # Fallback zu Defaults
```

---

## 🔤 Type Hints & Type Safety

### Grundregeln

**1. Alle Public Functions haben Type Hints**

```python
# ❌ FALSCH - Keine Type Hints
def process_data(data, config):
    result = transform(data, config)
    return result

# ✅ RICHTIG - Vollständige Type Hints
def process_data(
    data: dict[str, Any],
    config: Config
) -> ProcessResult:
    result = transform(data, config)
    return result
```

**2. Use Native Types (Python 3.9+)**

```python
# ❌ FALSCH - typing.* imports
from typing import List, Dict, Set, Tuple

def process(items: List[str]) -> Dict[str, int]:
    pass

# ✅ RICHTIG - Native types
def process(items: list[str]) -> dict[str, int]:
    pass
```

**3. Union Types mit `|` (Python 3.10+)**

```python
# ❌ FALSCH - typing.Union
from typing import Union, Optional

def get_user(id: Union[str, int]) -> Optional[User]:
    pass

# ✅ RICHTIG - | operator
def get_user(id: str | int) -> User | None:
    pass
```

**4. Type Aliases für Komplexität**

```python
# ✅ RICHTIG - Type Aliases für Readability
from typing import TypeAlias

UserId: TypeAlias = str | int
UserData: TypeAlias = dict[str, str | int | bool]
TaskResult: TypeAlias = tuple[bool, str, dict[str, Any]]

def process_user(
    user_id: UserId,
    data: UserData
) -> TaskResult:
    pass
```

**5. Optional vs `| None`**

```python
# ⚠️ OK aber veraltet
from typing import Optional

def get_value() -> Optional[str]:
    pass

# ✅ BESSER - Modern
def get_value() -> str | None:
    pass
```

**6. Generic Types**

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        return self.value

# Usage
container: Container[str] = Container("hello")
value: str = container.get()  # Type checker weiß: value ist str
```

**7. Protocol für Duck Typing**

```python
from typing import Protocol

class Executable(Protocol):
    """Alles was .execute() hat ist Executable"""
    def execute(self, task: str) -> str:
        ...

def run_agent(agent: Executable) -> str:
    return agent.execute("task")

# Funktioniert mit jedem Object das .execute() hat
```

**8. Type Guards für Runtime Checks**

```python
from typing import TypeGuard

def is_string_list(val: list[Any]) -> TypeGuard[list[str]]:
    """Runtime check mit Type Guard"""
    return all(isinstance(x, str) for x in val)

# Usage
items: list[Any] = get_items()
if is_string_list(items):
    # Type checker weiß jetzt: items ist list[str]
    result = " ".join(items)  # ✅ OK
```

---

## 🔒 Context Managers & Resource Management

### Grundprinzip: **IMMER** Context Managers für Resources

**1. File Operations**

```python
# ❌ FALSCH - Manuelle Resource Management
file = open("data.txt")
try:
    data = file.read()
    process(data)
finally:
    file.close()

# ✅ RICHTIG - with statement
with open("data.txt") as file:
    data = file.read()
    process(data)
# File wird automatisch geschlossen, auch bei Exception
```

**2. Database Connections**

```python
# ❌ FALSCH
conn = get_connection()
try:
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
finally:
    conn.close()

# ✅ RICHTIG
with get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()
```

**3. Custom Context Managers (Class-based)**

```python
class DatabaseTransaction:
    """Context Manager für Database Transactions"""

    def __init__(self, connection):
        self.conn = connection

    def __enter__(self):
        self.conn.begin()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        return False  # Don't suppress exceptions

# Usage
with DatabaseTransaction(conn) as transaction:
    transaction.execute("INSERT ...")
    transaction.execute("UPDATE ...")
# Automatic commit bei Success, rollback bei Exception
```

**4. Custom Context Managers (Decorator-based)**

```python
from contextlib import contextmanager

@contextmanager
def temporary_config(key: str, value: Any):
    """Temporarily change config value"""
    old_value = config.get(key)
    config.set(key, value)
    try:
        yield config
    finally:
        config.set(key, old_value)

# Usage
with temporary_config("debug", True):
    run_tests()
# Config automatisch zurückgesetzt
```

**5. Multiple Context Managers**

```python
# ✅ RICHTIG - Mehrere Context Managers
with open("input.txt") as infile, open("output.txt", "w") as outfile:
    data = infile.read()
    processed = process(data)
    outfile.write(processed)
```

**6. Async Context Managers**

```python
class AsyncResource:
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        return False

# Usage
async with AsyncResource() as resource:
    await resource.do_work()
```

---

## ⚡ Async/Await Patterns

### Wann Async verwenden?

**✅ VERWENDEN für:**
- I/O-bound operations (Network, File, Database)
- Viele concurrent connections
- Web APIs, WebSockets
- Async libraries (httpx, aiofiles, etc.)

**❌ NICHT verwenden für:**
- CPU-bound operations (verwende multiprocessing)
- Simple scripts ohne I/O
- Legacy code das nicht async ist

### Basic Patterns

**1. Simple Async Function**

```python
# ✅ RICHTIG
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Usage
async def main():
    data = await fetch_data("https://api.example.com/data")
    process(data)

if __name__ == "__main__":
    asyncio.run(main())
```

**2. Concurrent Execution - gather()**

```python
# ❌ FALSCH - Sequential (langsam)
async def process_all():
    result1 = await fetch_data(url1)
    result2 = await fetch_data(url2)
    result3 = await fetch_data(url3)
    return [result1, result2, result3]

# ✅ RICHTIG - Concurrent (schnell)
async def process_all():
    results = await asyncio.gather(
        fetch_data(url1),
        fetch_data(url2),
        fetch_data(url3)
    )
    return results
```

**3. Concurrent with create_task()**

```python
# ✅ RICHTIG - Tasks für fine-grained control
async def process_all():
    task1 = asyncio.create_task(fetch_data(url1))
    task2 = asyncio.create_task(fetch_data(url2))
    task3 = asyncio.create_task(fetch_data(url3))

    # Do other work while tasks run
    prepare_processing()

    # Wait for all tasks
    results = await asyncio.gather(task1, task2, task3)
    return results
```

**4. Semaphore für Rate Limiting**

```python
# ✅ RICHTIG - Begrenze concurrent operations
async def fetch_with_limit(urls: list[str], max_concurrent: int = 5):
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_one(url: str):
        async with semaphore:
            return await fetch_data(url)

    results = await asyncio.gather(*[fetch_one(url) for url in urls])
    return results
```

**5. Timeout Handling**

```python
# ✅ RICHTIG - Timeouts für async operations
async def fetch_with_timeout(url: str, timeout: float = 10.0):
    try:
        async with asyncio.timeout(timeout):
            return await fetch_data(url)
    except asyncio.TimeoutError:
        logger.error(f"Timeout fetching {url}")
        raise
```

**6. CPU-Bound Work in Async Context**

```python
# ✅ RICHTIG - Offload zu ThreadPoolExecutor
import concurrent.futures

async def process_heavy_computation(data: bytes):
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(
            executor,
            cpu_intensive_function,
            data
        )
    return result
```

**7. Producer-Consumer with Queue**

```python
# ✅ RICHTIG - Queue für async producer-consumer
async def producer(queue: asyncio.Queue):
    for i in range(10):
        item = await generate_item(i)
        await queue.put(item)
    await queue.put(None)  # Sentinel

async def consumer(queue: asyncio.Queue):
    while True:
        item = await queue.get()
        if item is None:
            break
        await process_item(item)
        queue.task_done()

async def main():
    queue = asyncio.Queue(maxsize=10)
    await asyncio.gather(
        producer(queue),
        consumer(queue)
    )
```

---

## 🧹 Clean Code Principles

### 1. Naming Conventions (PEP 8)

```python
# ✅ RICHTIG
class UserAccount:                    # CamelCase für Classes
    pass

def calculate_total_price():          # snake_case für functions
    pass

MAXIMUM_RETRY_ATTEMPTS = 3           # UPPER_CASE für Constants

user_name = "John"                    # snake_case für variables
total_count = 0

# ❌ FALSCH
class user_account:                   # ❌ Class sollte CamelCase sein
    pass

def CalculateTotalPrice():            # ❌ Function sollte snake_case sein
    pass

MaximumRetryAttempts = 3             # ❌ Constant sollte UPPER_CASE sein
```

### 2. Function Length & Complexity

```python
# ❌ FALSCH - Zu lang, zu komplex
def process_user_request(request):
    # 200+ Zeilen Code
    # Multiple responsibilities
    # Hohe Cyclomatic Complexity
    pass

# ✅ RICHTIG - Single Responsibility, kleine Funktionen
def process_user_request(request: Request) -> Response:
    """Main entry point for user requests"""
    validated_data = validate_request(request)
    user = authenticate_user(validated_data)
    result = execute_business_logic(user, validated_data)
    response = format_response(result)
    return response

def validate_request(request: Request) -> dict:
    """Validate and parse request data"""
    # ~10-20 Zeilen
    pass

def authenticate_user(data: dict) -> User:
    """Authenticate user from request data"""
    # ~10-20 Zeilen
    pass

# ... etc
```

### 3. Avoid Magic Numbers

```python
# ❌ FALSCH
if user.age > 18:
    allow_access()

if retry_count < 5:
    retry()

# ✅ RICHTIG
MINIMUM_AGE = 18
MAXIMUM_RETRIES = 5

if user.age > MINIMUM_AGE:
    allow_access()

if retry_count < MAXIMUM_RETRIES:
    retry()
```

### 4. Avoid Deep Nesting

```python
# ❌ FALSCH - Deep Nesting
def process(data):
    if data:
        if data.valid:
            if data.user:
                if data.user.active:
                    if data.user.has_permission():
                        # Do work
                        pass

# ✅ RICHTIG - Early Returns
def process(data: Data | None) -> Result:
    if not data:
        return error("No data")

    if not data.valid:
        return error("Invalid data")

    if not data.user:
        return error("No user")

    if not data.user.active:
        return error("User inactive")

    if not data.user.has_permission():
        return error("No permission")

    # Do work
    return success(result)
```

### 5. Use Comprehensions (but keep them simple)

```python
# ✅ RICHTIG - Simple Comprehension
squares = [x**2 for x in range(10)]
even_squares = [x**2 for x in range(10) if x % 2 == 0]

# ❌ FALSCH - Zu komplex
result = [
    process(transform(x.value))
    for x in data
    if x.valid and x.user and x.user.active
    for y in x.children
    if y.status == "active"
]

# ✅ RICHTIG - Loop für komplexe Logik
result = []
for item in data:
    if not (item.valid and item.user and item.user.active):
        continue

    for child in item.children:
        if child.status == "active":
            processed = process(transform(item.value))
            result.append(processed)
```

### 6. Docstrings für Public Functions

```python
# ✅ RICHTIG - Comprehensive Docstrings
def calculate_total_price(
    items: list[Item],
    discount: float = 0.0,
    tax_rate: float = 0.19
) -> float:
    """
    Calculate total price with discount and tax.

    Args:
        items: List of items to calculate price for
        discount: Discount percentage (0.0 to 1.0), defaults to 0.0
        tax_rate: Tax rate to apply (0.0 to 1.0), defaults to 0.19

    Returns:
        Total price including discount and tax

    Raises:
        ValueError: If discount or tax_rate is outside valid range

    Example:
        >>> items = [Item("Book", 10.0), Item("Pen", 2.0)]
        >>> calculate_total_price(items, discount=0.1)
        12.85
    """
    if not 0.0 <= discount <= 1.0:
        raise ValueError("Discount must be between 0.0 and 1.0")

    if not 0.0 <= tax_rate <= 1.0:
        raise ValueError("Tax rate must be between 0.0 and 1.0")

    subtotal = sum(item.price for item in items)
    discounted = subtotal * (1 - discount)
    total = discounted * (1 + tax_rate)
    return round(total, 2)
```

---

## 🚫 Anti-Patterns zu vermeiden

### 1. Opening Files ohne Context Manager

```python
# ❌ ANTI-PATTERN
file = open("data.txt")
data = file.read()
file.close()  # Vergessen = Resource Leak!

# ✅ RICHTIG
with open("data.txt") as file:
    data = file.read()
```

### 2. Mutable Default Arguments

```python
# ❌ ANTI-PATTERN
def add_item(item, items=[]):
    items.append(item)
    return items

# Bug: items list wird zwischen Calls geteilt!
list1 = add_item(1)  # [1]
list2 = add_item(2)  # [1, 2] statt [2]!

# ✅ RICHTIG
def add_item(item, items: list | None = None):
    if items is None:
        items = []
    items.append(item)
    return items
```

### 3. Bare except

```python
# ❌ ANTI-PATTERN
try:
    dangerous_operation()
except:  # Catcht ALLES, auch KeyboardInterrupt!
    pass

# ✅ RICHTIG
try:
    dangerous_operation()
except SpecificError as e:
    logger.error(f"Expected error: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### 4. Global State Mutation

```python
# ❌ ANTI-PATTERN
global_config = {}

def update_config(key, value):
    global_config[key] = value  # Mutation von global state

# ✅ RICHTIG
class Config:
    def __init__(self):
        self._config = {}

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def get(self, key: str) -> Any:
        return self._config.get(key)

config = Config()  # Instance statt global state
```

### 5. String Concatenation in Loops

```python
# ❌ ANTI-PATTERN - Langsam!
result = ""
for item in items:
    result += str(item)  # Creates new string each iteration

# ✅ RICHTIG
result = "".join(str(item) for item in items)
```

### 6. Checking Type mit `type()`

```python
# ❌ ANTI-PATTERN
if type(x) == list:
    process_list(x)

# ✅ RICHTIG
if isinstance(x, list):
    process_list(x)
```

### 7. Using `assert` für Validation

```python
# ❌ ANTI-PATTERN - assert kann deaktiviert werden!
def process(value):
    assert value > 0, "Value must be positive"
    return value * 2

# ✅ RICHTIG
def process(value: int) -> int:
    if value <= 0:
        raise ValueError("Value must be positive")
    return value * 2
```

### 8. Silent Failure with pass

```python
# ❌ ANTI-PATTERN
try:
    result = critical_operation()
except Exception:
    pass  # Bugs werden verschluckt!

# ✅ RICHTIG
try:
    result = critical_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    result = fallback_value
```

---

## ✅ Code Review Checklist

Vor jedem Commit diese Punkte prüfen:

### Error Handling
- [ ] Alle Variablen die in `except` verwendet werden sind vor `try` initialisiert
- [ ] Spezifische Exception Types (nicht `Exception` oder bare `except`)
- [ ] Try-Blocks sind minimal (nur der riskante Code)
- [ ] `else` Clause für Success Path verwendet wo sinnvoll
- [ ] Resource Cleanup garantiert (Context Manager oder `finally`)
- [ ] Exceptions werden nicht silent gefailed (`pass`)
- [ ] Error Messages sind actionable und hilfreich

### Type Hints
- [ ] Alle public functions haben vollständige Type Hints
- [ ] Return Type ist angegeben
- [ ] Native types verwendet (`list` statt `List`, `|` statt `Union`)
- [ ] Complex types haben Type Aliases
- [ ] `Any` wird nur verwendet wenn wirklich necessary

### Resource Management
- [ ] Alle File Operations verwenden `with`
- [ ] Alle Database Connections verwenden Context Managers
- [ ] Keine manuellen `.close()` calls
- [ ] Async resources verwenden `async with`

### Async/Await
- [ ] `await` ist vorhanden für alle async calls
- [ ] Sequential `await` nur wenn wirklich sequential notwendig
- [ ] `gather()` für concurrent execution verwendet
- [ ] Timeouts für I/O operations gesetzt
- [ ] CPU-bound work zu Executor offgeloaded

### Clean Code
- [ ] Function Names sind descriptive und folgen PEP 8
- [ ] Functions haben single responsibility
- [ ] Functions sind < 50 Zeilen (idealerweise < 20)
- [ ] Magic Numbers sind durch Constants ersetzt
- [ ] Deep Nesting vermieden (Early Returns)
- [ ] Docstrings für alle public functions
- [ ] No mutable default arguments

### Anti-Patterns
- [ ] Keine bare `except:` Clauses
- [ ] Keine Global State Mutations
- [ ] Kein `type()` checking (use `isinstance()`)
- [ ] Keine `assert` für Validation
- [ ] Files IMMER mit Context Manager öffnen

---

## 📚 Weiterführende Ressourcen

### Official Python Documentation
- [What's New in Python 3.13](https://docs.python.org/3/whatsnew/3.13.html)
- [Python typing Documentation](https://docs.python.org/3/library/typing.html)
- [Python Errors and Exceptions](https://docs.python.org/3/tutorial/errors.html)
- [Context Managers](https://docs.python.org/3/library/contextlib.html)
- [Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

### Style Guides
- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 484 – Type Hints](https://peps.python.org/pep-0484/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

### Tools
- **mypy** - Static type checker
- **pyright** - Microsoft's type checker
- **ruff** - Extremely fast Python linter
- **black** - Uncompromising code formatter
- **beartype** - Runtime type checking

---

## 🔄 Updates & Maintenance

Dieses Dokument wird regelmäßig aktualisiert wenn:
- Neue Python Versionen erscheinen
- Neue Best Practices im Python Community etabliert werden
- Projekt-spezifische Patterns hinzugefügt werden

**Letzte Änderung:** 2025-10-07
**Nächste Review:** Bei Python 3.14 Release

---

**WICHTIG:** Alle Code Changes MÜSSEN diesen Standards entsprechen. Bei Code Reviews gegen diese Checklist prüfen!
