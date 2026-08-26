---
title: 'Top 10 Easy-to-Miss Mistakes in Python Programming'
pubDate: '2026-08-25'
description: '10 Python pitfalls that look harmless — from mutable defaults to late-binding closures — with broken code, why they fail, and idiomatic fixes.'
heroImage: '../../assets/blog-placeholder-5.jpg'
tags:
  - python
  - programming
  - pitfalls
---

# Top 10 Easy-to-Miss Mistakes in Python Programming

Python reads like English but bites like a viper. These 10 pass `flake8`, look fine in review, then corrupt data in prod.

## 1. Mutable Default Arguments

```python
# BAD: default [] is created ONCE at function definition
def add_item(item, lst=[]):
    lst.append(item)
    return lst

print(add_item(1)) # [1]
print(add_item(2)) # [1, 2] — surprise!

# GOOD
def add_item(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst

# Same trap with dict/set: def foo(d={}): ...
```

**Why:** Defaults are evaluated at definition time, not call time.

**Fix:** Use `None` sentinel and create new object inside.

## 2. Late-Binding Closures in Loops

```python
# BAD: all lambdas capture same variable `i` by reference
funcs = [lambda: i for i in range(3)]
print([f() for f in funcs]) # [2, 2, 2] — not [0,1,2]

# GOOD: capture via default arg
funcs = [lambda i=i: i for i in range(3)]
print([f() for f in funcs]) # [0, 1, 2]

# Or with functools.partial
from functools import partial
def make_fn(v): return lambda: v
funcs = [make_fn(i) for i in range(3)]

# Same bug with threads:
import threading
for i in range(3):
    threading.Thread(target=lambda: print(i)).start() # all print 2
```

**Fix:** Bind loop var as default arg or via factory function.

## 3. `is` vs `==` & String Interning Surprises

```python
# BAD
a = 1000
b = 1000
a is b   # False — `is` checks identity, not value
a == b   # True

# CPython caches small ints -256..256 and some strings, so it *seems* to work
x = 256; y = 256; x is y # True (cached)
x = 257; y = 257; x is y # False — breaks in prod

# GOOD
if a == b: ...          # value comparison
if x is None: ...       # only use `is` with None/True/False singletons
if x is not None: ...
```

**Fix:** `==` for values, `is` only for `None`.

## 4. Modifying List/Dict While Iterating

```python
# BAD: skipping / RuntimeError
nums = [1,2,3,4]
for n in nums:
    if n == 2:
        nums.remove(n) # skips 3

d = {'a':1, 'b':2}
for k in d:
    if k == 'a': del d[k] # RuntimeError: dictionary changed size

# GOOD
nums = [n for n in nums if n != 2]  # filter via comprehension
d = {k:v for k,v in d.items() if k != 'a'}

# Or iterate over copy
for k in list(d.keys()):
    if k == 'a': del d[k]
```

## 5. Shallow Copy Surprises

```python
import copy
a = [[1,2], [3,4]]
b = a[:]              # shallow — inner lists shared
b[0][0] = 99
print(a) # [[99,2], [3,4]] — mutated!

b2 = copy.copy(a)     # still shallow
b3 = copy.deepcopy(a) # deep — safe
b3[0][0] = 0
print(a) # unchanged

# Same with dict
d2 = d.copy()         # shallow
```

**Fix:** Use `copy.deepcopy` for nested structures. Or `import copy`.

## 6. `except` Too Broad & Swallowed Tracebacks

```python
# BAD: hides KeyboardInterrupt, SystemExit, and every bug
try:
    do_work()
except:
    pass # silent death

try:
    data = json.loads(payload)
except Exception as e:
    print("error", e) # loses traceback

# GOOD
try:
    do_work()
except ValueError as e: # specific
    logger.exception("bad value %s", payload) # logs traceback
    raise
except Exception: # if must catch all
    logger.exception("unexpected")
    raise

# Or: except Exception as e: raise MyError("context") from e  # chain
```

**Fix:** Catch narrow exceptions, use `logger.exception` / `raise ... from e`.

## 7. `__init__` Without `super()`, MRO & Diamond

```python
# BAD: parent not initialized
class Base:
    def __init__(self): self.id = 1

class Child(Base):
    def __init__(self):
        self.name = "hi"  # Base.__init__ never ran, self.id missing

# GOOD
class Child(Base):
    def __init__(self):
        super().__init__() # cooperative MRO
        self.name = "hi"

# With multiple inheritance, always super()
class A:
    def __init__(self): super().__init__(); print("A")
class B:
    def __init__(self): super().__init__(); print("B")
class C(A, B):
    def __init__(self): super().__init__(); print("C")
# MRO: C -> A -> B -> object
```

## 8. File / Resource Leaks & `open` Without `with`

```python
# BAD: leaks file handle on exception
f = open("data.txt")
data = f.read()
f.close() # never reached if read() raises

# BAD: encoding not specified → platform-dependent
open("data.txt").read() # Windows vs Linux differ

# GOOD
with open("data.txt", encoding="utf-8") as f:
    data = f.read()  # auto-closed even on exception

# For multiple files
with open("a.txt", encoding="utf-8") as a, open("b.txt", "w", encoding="utf-8") as b:
    b.write(a.read())
```

**Fix:** Always `with open(..., encoding="utf-8")`.

## 9. `== None` / Truthiness & `0` / `[]` as Valid Values

```python
# BAD: 0 and [] are falsy but valid
def paginate(page):
    if not page: # page=0 is valid but goes to 1
        page = 1
    return page

paginate(0) # 1 — wrong

# GOOD
def paginate(page):
    if page is None:
        page = 1
    return page

# Same with default `or`
cfg = user.get("retries") or 3 # retries=0 → 3, wrong
cfg = user.get("retries", 3) if user.get("retries") is not None else 3
# Or: cfg = user["retries"] if "retries" in user else 3
```

**Fix:** `is None` checks, not `not x` or `x or default` when `0`/`""`/`[]` are valid.

## 10. GIL, `time.sleep` & CPU-Bound Threads

```python
# BAD: threads don't parallelize CPU work due to GIL, sleep blocks
import threading, time
def cpu(n):
    return sum(i*i for i in range(n))

threads = [threading.Thread(target=cpu, args=(10**7,)) for _ in range(4)]
[t.start() for t in threads]
[t.join() for t in threads] # 4x slower than expected — GIL serializes

# GOOD: for CPU-bound → multiprocessing or native
from concurrent.futures import ProcessPoolExecutor
with ProcessPoolExecutor() as ex:
    ex.map(cpu, [10**7]*4) # true parallelism

# For I/O-bound → asyncio/aiohttp, not thread-per-request + sleep
import asyncio
async def fetch(url):
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r: return await r.text()

# Don't: time.sleep in async code
# asyncio.sleep is needed
```

**Why:** CPython's GIL allows one thread to execute Python bytecode at a time. `time.sleep` holds no CPU but blocks the thread.

**Fix:** `ProcessPoolExecutor` for CPU, `asyncio` for I/O.

---

## Checklist Before `python -m py_compile` Passes

- [ ] No `def foo(x=[])` — use `None`
- [ ] Loop lambdas bind via `lambda x=x: ...`
- [ ] `==` for values, `is` only for `None`
- [ ] No mutate-while-iterate — use comprehensions / `list(d)`
- [ ] Nested structures `copy.deepcopy`
- [ ] Narrow `except`, `logger.exception`, `raise ... from`
- [ ] `super().__init__()` in every subclass
- [ ] `with open(..., encoding="utf-8")`
- [ ] `is None` not `not x` when `0`/`[]` valid
- [ ] CPU → `ProcessPoolExecutor`, I/O → `asyncio`

Nail these and Python feels like the forgiving language it promised to be.

> Next: `asyncio` pitfalls (`gather` + exceptions, `Task` leaks) or `type hints` gotchas? Let me know.
