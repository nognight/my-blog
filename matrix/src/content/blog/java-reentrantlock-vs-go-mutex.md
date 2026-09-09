---
title: 'Java ReentrantLock vs Go Mutex: Semantics and How to Use'
pubDate: '2026-09-09'
description: 'Same word lock, different contract — reentrancy, fairness, timeouts, and idiomatic usage with runnable Java and Go examples.'
heroImage: '../../assets/blog-placeholder-3.jpg'
tags:
  - java
  - go
  - concurrency
---

# Java ReentrantLock vs Go Mutex: Semantics and How to Use

Both guard shared state. The contract differs: Java's `ReentrantLock` is reentrant, interruptible, and timed. Go's `sync.Mutex` is minimal, non-reentrant, and relies on `defer`. Mix them up and you get deadlocks in Go or leaked locks in Java.

## TL;DR

| Feature | Java `ReentrantLock` | Go `sync.Mutex` |
| :------ | :------------------- | :-------------- |
| Reentrant (same thread/goroutine relock) | Yes — hold count++ | No — self-deadlock |
| Ownership tracking | Yes (`getHoldCount`, `isHeldByCurrentThread`) | No |
| Fair mode | `new ReentrantLock(true)` FIFO | No — starvation possible |
| Timeout / interrupt | `tryLock(ms)`, `lockInterruptibly()` | None built-in |
| Condition wait | `newCondition().await()/signal()` | `sync.Cond` or channels |
| Zero value ready | No — `new ReentrantLock()` | Yes — `var mu sync.Mutex` |
| Must not copy | N/A (reference type) | Yes — `go vet -copylocks` fails on copy |
| Idiom | `lock(); try { ... } finally { unlock(); }` | `mu.Lock(); defer mu.Unlock()` |

## 1. Java: basic usage

Always unlock in `finally`. If `lock()` itself is inside `try`, an exception path can unlock a lock you never held.

```java
import java.util.concurrent.locks.ReentrantLock;

class Counter {
    private final ReentrantLock lock = new ReentrantLock();
    private int count = 0;

    // GOOD
    public void inc() {
        lock.lock();
        try {
            count++;
        } finally {
            lock.unlock();
        }
    }

    // BAD: lock inside try — unlock in finally may release unheld lock
    public void incBad() {
        try {
            lock.lock();
            count++;
        } finally {
            lock.unlock();
        }
    }
}
```

**Why:** `lock()` can throw (e.g. interrupt). `finally` must only release what was acquired.

**Fix:** `lock()` before `try`, `unlock()` in `finally`.

## 2. Java: reentrancy

Same thread can relock. Hold count tracks depth.

```java
public void reentrant() {
    lock.lock();
    try {
        System.out.println(lock.getHoldCount()); // 1
        inc(); // relocks same thread — OK, hold stays 1 after inner unlock
        System.out.println(lock.getHoldCount()); // 1
    } finally {
        lock.unlock();
    }
}
```

Useful for recursive code or `outer()` calling `inner()` where both lock. Verified: `count=2000` with 2 threads x 1000 increments, `hold=1`, `hold-after-inc=1`.

## 3. Java: timeouts, interrupt, fairness

```java
import java.util.concurrent.TimeUnit;

public boolean tryInc() throws InterruptedException {
    if (lock.tryLock(100, TimeUnit.MILLISECONDS)) {
        try {
            count++;
            return true;
        } finally {
            lock.unlock();
        }
    }
    return false; // busy — skip or retry with backoff
}

public void cancellable() throws InterruptedException {
    lock.lockInterruptibly(); // responds to Thread.interrupt()
    try {
        // work
    } finally {
        lock.unlock();
    }
}

// Fair constructor — FIFO waiters, lower throughput
ReentrantLock fair = new ReentrantLock(true);
```

**When:** `tryLock` for best-effort paths (cache refresh, opportunistic write). Fair lock only when starvation hurts more than throughput.

`Condition` for wait/notify without `synchronized`:

```java
var cond = lock.newCondition();
// await() releases lock, parks, relocks on signal
cond.await(1, TimeUnit.SECONDS);
cond.signal();
```

## 4. Go: basic usage

Zero value is ready. `defer` pairs lock/unlock.

```go
var mu sync.Mutex
count := 0

// GOOD
mu.Lock()
count++
mu.Unlock()

// GOOD with early returns
func Inc() {
    mu.Lock()
    defer mu.Unlock()
    count++
    if count > 100 {
        return // unlock still runs
    }
}
```

```go
// BAD: missing unlock on some path
mu.Lock()
if err != nil {
    return // deadlock for next locker!
}
count++
mu.Unlock()
```

**Fix:** `defer mu.Unlock()` immediately after `Lock()` unless the critical section is hot and tiny.

Verified counter:

```go
var mu sync.Mutex
var wg sync.WaitGroup
for i := 0; i < 2; i++ {
    wg.Add(1)
    go func() {
        defer wg.Done()
        for j := 0; j < 1000; j++ {
            mu.Lock()
            count++
            mu.Unlock()
        }
    }()
}
wg.Wait() // count == 2000
```

## 5. Go: NOT reentrant — the #1 trap for Java devs

```go
var mu sync.Mutex

func outer() {
    mu.Lock()
    defer mu.Unlock()
    inner() // BAD: tries to Lock again — self-deadlock
}

func inner() {
    mu.Lock()
    defer mu.Unlock()
}
```

Same goroutine relocking blocks forever. Go runtime does not detect it as `fatal error` — it just hangs.

**Fix:** restructure so only the outer layer locks, or split `doThingLocked()` internal that assumes lock held:

```go
func outer() {
    mu.Lock()
    defer mu.Unlock()
    doThingLocked()
}

func doThingLocked() { /* no lock here */ }
```

Java devs expect `getHoldCount()` — Go has no equivalent by design.

## 6. Go: `RWMutex`, no-copy, race detector

Read-heavy map:

```go
var rw sync.RWMutex
m := map[string]int{"a": 1}

rw.RLock()
v := m["a"]
rw.RUnlock()

rw.Lock()
m["a"] = v + 1
rw.Unlock()
```

Rules:

```go
// BAD: copies mutex — vet error
type S struct { mu sync.Mutex }
func f(s S) { /* copy! */ }

// GOOD: pointer or embed by pointer
func f(s *S) { /* ... */ }
```

```bash
go vet ./...          # catches copylocks
go run -race main.go  # catches missing locks
```

`sync.Map` only for key-stable, mostly-read cases. Otherwise owner-goroutine + channel beats shared map + mutex.

## 7. Side-by-side: guarded counter

Java:

```java
lock.lock();
try { count++; } finally { lock.unlock(); }
```

Go:

```go
mu.Lock()
count++
mu.Unlock()
// or: mu.Lock(); defer mu.Unlock()
```

Same shape, different guarantees. Java version survives reentry and can time out. Go version is 2 lines, zero-alloc, but caller must never relock or copy.

## Checklist

- [ ] Java: `lock()` before `try`, `unlock()` in `finally`
- [ ] Java: `tryLock(timeout)` for best-effort, `lockInterruptibly()` for cancellable
- [ ] Java: fair lock only when starvation matters
- [ ] Go: `defer Unlock()` right after `Lock()` when early returns exist
- [ ] Go: never relock, never copy `Mutex` (`go vet`), run `-race`
- [ ] Go: `RWMutex` for read-heavy, `sync.Map`/channels when shape fits

> Next: `ReentrantReadWriteLock` vs `sync.RWMutex` starvation, or Java `StampedLock` optimistic reads vs Go `atomic.*`.
