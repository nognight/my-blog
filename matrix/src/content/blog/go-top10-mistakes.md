---
title: 'Top 10 Easy-to-Miss Mistakes in Go Programming'
pubDate: '2026-08-25'
description: '10 Go pitfalls that compile fine but fail in production — from nil interfaces to goroutine leaks — with broken code and idiomatic fixes.'
heroImage: '../../assets/blog-placeholder-4.jpg'
tags:
  - go
  - golang
  - programming
  - pitfalls
---

# Top 10 Easy-to-Miss Mistakes in Go Programming

Go is simple by design, but its simplicity hides traps. These 10 pass `go vet`, compile, then break at 3am.

## 1. `nil` Interface != `nil` Pointer

```go
func returnsError() error {
    var p *MyError = nil
    return p // BAD: returns (type *MyError, nil) — interface is NOT nil
}

err := returnsError()
fmt.Println(err == nil) // false! — contains (type, value) = (*MyError, nil)
if err != nil { log.Fatal(err) } // always triggers
```

**Why:** An `interface` is `(type, value)`. Returning a typed `nil` pointer gives a non-nil interface.

**Fix:**
```go
func returnsError() error {
    var p *MyError = nil
    if p == nil { return nil } // return untyped nil
    return p
}
// Or: return nil directly, never return typed nil as error
```

## 2. Loop Variable Captured by Goroutine/Closure (Fixed in Go 1.22, Still Bites)

```go
// Before Go 1.22: BROKEN
for _, v := range []int{1,2,3} {
    go func() { fmt.Println(v) }() // all goroutines print 3 (or race)
}

// FIX: capture param
for _, v := range []int{1,2,3} {
    v := v // new binding per iteration (pre-1.22 idiom)
    go func() { fmt.Println(v) }()
}
// Go 1.22+: loop vars are per-iteration, but still capture explicitly for clarity
for _, v := range []int{1,2,3} {
    go func(val int) { fmt.Println(val) }(v)
}
```

**Fix:** Always pass loop vars as func args. `go vet` now warns.

## 3. Slices Share Underlying Arrays

```go
a := []int{1,2,3,4,5}
b := a[1:3] // [2,3] — shares array with a
b[0] = 99
fmt.Println(a) // [1 99 3 4 5] — mutated!

// Append can alias or reallocate unpredictably
c := append(a[:2], 100) // may overwrite a[2] if cap allows, or allocate new

// FIX: copy when you need independence
b2 := append([]int(nil), a[1:3]...) // copy
// Or: b2 := make([]int, 2); copy(b2, a[1:3])

// For append, assign result and don't keep old refs
a = append(a, 100) // always re-assign
```

## 4. Maps Are Not Concurrent-Safe

```go
m := make(map[string]int)
go func(){ m["a"] = 1 }()
go func(){ fmt.Println(m["a"]) }() // fatal error: concurrent map read and map write

// FIX
var mu sync.RWMutex
mu.Lock(); m["a"] = 1; mu.Unlock()
mu.RLock(); v := m["a"]; mu.RUnlock()

// Or: sync.Map for mostly-read, key-stable cases
var sm sync.Map
sm.Store("a", 1)
v, _ := sm.Load("a")

// Or: single goroutine owns the map, talk via channel
```

## 5. `defer` in Loops & Leaked Resources

```go
// BAD: defers execute at function return, not loop iteration — holds 1000 files open
for _, path := range paths {
    f, _ := os.Open(path)
    defer f.Close() // stacks up!
    io.ReadAll(f)
}

// GOOD: wrap in func or close explicitly
for _, path := range paths {
    func() {
        f, _ := os.Open(path)
        defer f.Close()
        io.ReadAll(f)
    }()
}
// Or:
for _, path := range paths {
    f, _ := os.Open(path)
    io.ReadAll(f)
    f.Close()
}
```

## 6. Ignoring Errors & `err` Shadowing

```go
// BAD: ignored
os.MkdirAll("/tmp/x", 0755) // error dropped

// BAD: shadowing with :=
if err := do(); err != nil { /* handles inner err */ }
 // outer err is still nil here unexpectedly
// Later:
if err != nil { /* checks wrong err */ }

// GOOD
if err := do(); err != nil {
    return fmt.Errorf("do: %w", err)
}
// Use = when you intend to assign to outer
var err error
x, err = foo() // = not :=
```

**Fix:** `golangci-lint` with `errcheck`, `govet -shadow`. Handle every `error` return.

## 7. Context Cancellation Ignored

```go
// BAD: goroutine leaks after request cancelled
func handler(w http.ResponseWriter, r *http.Request) {
    go doWork() // keeps running after client disconnects
}

// GOOD: propagate context
func handler(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    go doWork(ctx)
}
func doWork(ctx context.Context) {
    select {
    case <-ctx.Done():
        return // cancelled
    case <-time.After(5*time.Second):
        // work
    }
    // For DB/HTTP: pass ctx to queries
    // db.QueryContext(ctx, ...)
}

// Always: func Do(ctx context.Context, ...) error
```

## 8. Value vs Pointer Receiver — Mutations Lost

```go
type Counter struct{ n int }
func (c Counter) Inc() { c.n++ } // value receiver — modifies copy!

c := Counter{}
c.Inc()
fmt.Println(c.n) // 0 — not incremented

// FIX
func (c *Counter) Inc() { c.n++ }
c2 := &Counter{}
c2.Inc() // 1

// Rule: if ANY method needs pointer, use pointer for ALL (consistency)
// Also affects interface satisfaction: *Counter != Counter
```

## 9. `time.After` in Loops Leaks Timers

```go
// BAD: each iteration creates a timer never GC'd until fired
for {
    select {
    case <-time.After(1*time.Second): // leaks
        tick()
    case <-ctx.Done(): return
    }
}

// GOOD: reuse ticker
ticker := time.NewTicker(1*time.Second)
defer ticker.Stop()
for {
    select {
    case <-ticker.C: tick()
    case <-ctx.Done(): return
    }
}

// Similarly: time.After inside hot select → use time.NewTimer and Reset
```

## 10. Goroutine Leaks & No Bounded Concurrency

```go
// BAD: unbounded goroutines, no backpressure
for _, job := range jobs {
    go process(job) // 1M jobs → 1M goroutines → OOM
}

// BAD: channel without receiver leaks sender
ch := make(chan int)
go func(){ ch <- 1 }() // blocks forever if no one receives

// GOOD: worker pool + context + buffered/semaphore
ctx, cancel := context.WithCancel(ctx)
defer cancel()
g, ctx := errgroup.WithContext(ctx)
g.SetLimit(10) // Go 1.20+ / x/sync
for _, job := range jobs {
    job := job
    g.Go(func() error {
        select {
        case <-ctx.Done(): return ctx.Err()
        default: return process(ctx, job)
        }
    })
}
if err := g.Wait(); err != nil { log.Fatal(err) }

// Or: semaphore channel
sem := make(chan struct{}, 10)
for _, job := range jobs {
    sem <- struct{}{}
    go func(j Job){
        defer func(){ <-sem }()
        process(j)
    }(job)
}
```

---

## Checklist Before `go vet` Passes

- [ ] No `return typedNil` as `error` — return `nil` explicitly
- [ ] Loop vars captured via param `go func(v T){}(v)`
- [ ] Slices copied before mutate: `append([]T(nil), s...)`
- [ ] Maps guarded by `sync.Mutex` / `sync.Map` / owner goroutine
- [ ] No `defer` in loop — wrap in func
- [ ] All `error`s checked, no `:=` shadow
- [ ] `context.Context` first arg, checked via `select { case <-ctx.Done(): }`
- [ ] Pointer receiver for mutating methods
- [ ] No `time.After` in loop — use `NewTicker`/`NewTimer`
- [ ] Bounded concurrency: `errgroup.SetLimit` / semaphore, no fire-and-forget `go`

Fix these and Go feels like the simple language it promised to be.

> Next: Go generics pitfalls (`comparable` surprises) or `pprof` leak hunting? Tell me.
