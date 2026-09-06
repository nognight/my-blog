---
title: 'Top 10 Easy-to-Miss Mistakes in Kotlin Programming'
pubDate: '2026-09-06'
description: '10 Kotlin pitfalls that compile clean but crash in prod — from !! and platform types to coroutine leaks and data-class mutability — with broken code and idiomatic fixes.'
heroImage: '../../assets/blog-placeholder-1.jpg'
tags:
  - kotlin
  - programming
  - pitfalls
---

# Top 10 Easy-to-Miss Mistakes in Kotlin Programming

Kotlin feels safe — null-safety, coroutines, data classes. Until it isn't. The compiler saves you 90% of the time; these 10 slip through the other 10% and blow up in production.

## 1. The `!!` Hammer and `lateinit` Roulette

```kotlin
// BAD: "I know it's not null" — famous last words
fun printName(user: User?) {
    println(user!!.name) // NPE if user is null — you just reintroduced Java's NPE
}

class Screen {
    lateinit var binding: Binding
    fun onCreate() { /* forgot to init binding */ }
    fun onRender() { binding.draw() } // UninitializedPropertyAccessException!
}

// Also BAD: lateinit on nullable or primitive
lateinit var count: String // compile error, but lateinit var name: String? still traps you
```

**Why:** `!!` tells the compiler "trust me" and disables the one guarantee Kotlin gives you. `lateinit` moves the null-check from compile time to runtime and hides initialization order bugs.

**Fix:**
```kotlin
// GOOD: let the type system work for you
fun printName(user: User?) {
    println(user?.name ?: "Guest") // safe call + Elvis
    // Or fail fast with meaning:
    val u = requireNotNull(user) { "user required for printName" }
    println(u.name)
}

class Screen(private val binding: Binding) { // constructor injection > lateinit
    fun onRender() { binding.draw() }
}
// If you must use lateinit, check it:
if (::binding.isInitialized) binding.draw()

// Prefer lazy for immutable deferred init:
val binding: Binding by lazy { createBinding() }
```

**Rule:** `!!` should trigger a lint warning. Prefer `?.`, `?:`, `requireNotNull`, `checkNotNull`, `error()`.

## 2. Platform Types from Java Will Betray You (`String!`)

```kotlin
// Java: public static String maybeNull() { return null; }
// Kotlin sees: fun maybeNull(): String!  — unknown nullability

// BAD: compiler allows both, crash at runtime
val s: String = JavaApi.maybeNull() // compiles, NPE later when you use s
println(s.length) // NPE deep in call stack, not at assignment

// BAD: passing nullable Kotlin to Java without thinking
fun kotlinFunc(name: String?) { JavaApi.takesNonNull(name) } // Java may not check null
```

**Why:** Java has no nullability in its type system. Kotlin represents this as `T!` (platform type) — the compiler trusts you either way and emits no error.

**Fix:**
```kotlin
// GOOD: assume Java is nullable until proven otherwise
val s: String? = JavaApi.maybeNull()
println(s?.length ?: 0)

// Or enforce immediately
val s2: String = requireNotNull(JavaApi.maybeNull()) { "JavaApi returned null" }

// Annotate Java with @Nullable/@NotNull (JSR-305, JetBrains annotations) so Kotlin sees correct type
// In Kotlin, declare stricter boundaries:
fun kotlinFunc(name: String?) {
    val safe = requireNotNull(name) { "name must not be null" }
    JavaApi.takesNonNull(safe)
}
```

**Rule:** At every Java interop boundary, add an explicit `?` or `requireNotNull`. Enable `-Xjsr305=strict` in Gradle.

## 3. Breaking Structured Concurrency — `GlobalScope` and Fire-and-Forget

```kotlin
// BAD: leaks, uncancellable, crashes are lost
class ViewModel {
    fun load() {
        GlobalScope.launch { // lives for app lifetime, not ViewModel lifetime
            val data = repo.fetch()
            updateUI(data) // may run after ViewModel cleared → leak/crash
        }
    }
}

// BAD: fire-and-forget with no error handling
fun onClick() {
    GlobalScope.launch { service.sync() } // exception swallowed, no one observes it
}
```

**Why:** `GlobalScope` breaks parent-child cancellation. Children outlive their screen/scope, leak memory, and their exceptions crash nothing (or crash `UncaughtExceptionHandler`).

**Fix:**
```kotlin
// GOOD: scope tied to lifecycle
class MyViewModel(private val scope: CoroutineScope) {
    fun load() {
        scope.launch { // cancelled when scope.cancel() is called
            val data = repo.fetch()
            updateUI(data)
        }
    }
    fun clear() { scope.cancel() }
}

// In Android: viewModelScope / lifecycleScope
// In Ktor/server: coroutineScope / supervisorScope
suspend fun loadAll(): List<Data> = coroutineScope {
    val a = async { repo.fetchA() }
    val b = async { repo.fetchB() }
    listOf(a.await(), b.await()) // both cancelled if one fails or parent cancelled
}

// For fire-and-forget that you actually mean, make it explicit and handle errors:
scope.launch(CoroutineExceptionHandler { _, e -> log.error("sync failed", e) }) {
    service.sync()
}
```

**Rule:** Never use `GlobalScope`. Pass `CoroutineScope` as dependency or use `coroutineScope` builder. If you must launch, attach `CoroutineExceptionHandler`.

## 4. Blocking the Coroutine Thread — `Thread.sleep` and Blocking I/O

```kotlin
// BAD: blocks the thread that all coroutines share
suspend fun load() {
    Thread.sleep(1000) // blocks Default dispatcher thread → starves other coroutines
    val data = File("data.json").readText() // blocking I/O on Default/Main
}

// BAD: runBlocking inside suspend
suspend fun getUser() = runBlocking { api.fetchUser() } // blocks current thread, deadlock risk
```

**Why:** Coroutines are cheap; threads are not. `Dispatchers.Default` has ~CPU cores threads. Blocking one stalls every coroutine on it. `runBlocking` in `suspend` defeats suspension entirely.

**Fix:**
```kotlin
// GOOD: suspend properly
suspend fun load() {
    delay(1000) // suspends, frees thread
    val data = withContext(Dispatchers.IO) { // move blocking I/O to IO pool
        File("data.json").readText()
    }
}

// For CPU work: stay on Default
// For blocking calls: withContext(Dispatchers.IO)
// For Retrofit/JDBC without suspend support: wrap it
suspend fun fetchUser(): User = withContext(Dispatchers.IO) { api.blockingFetch() }

// Only runBlocking at the very top (main, tests)
fun main() = runBlocking { load() }
```

**Rule:** In `suspend` functions, use `delay` not `sleep`. Wrap every blocking call in `withContext(Dispatchers.IO)`.

## 5. `data class` with Mutable State — `copy()` Is Shallow and `equals` Lies

```kotlin
// BAD: data class with var / MutableList — breaks equals/hashCode/copy contract
data class User(var name: String, val tags: MutableList<String>)

val a = User("Ann", mutableListOf("kotlin"))
val b = a.copy() // shallow copy — same list instance!
b.tags.add("java")
println(a.tags) // [kotlin, java] — mutated original!

// BAD: mutating a key inside HashSet/HashMap
val set = hashSetOf(a)
a.name = "Bob" // hashCode changed!
println(set.contains(a)) // false — lost in set

// BAD: array in data class — equals is referential
data class Holder(val bytes: ByteArray) // equals compares reference, not content
Holder(byteArrayOf(1)) == Holder(byteArrayOf(1)) // false!
```

**Why:** `data class` auto-generates `equals/hashCode/copy/toString` based on properties. If properties are mutable or shallow-copied, two "equal" objects diverge, and hashed collections break.

**Fix:**
```kotlin
// GOOD: data class should be immutable + deeply immutable
data class User(val name: String, val tags: List<String>) // List (read-only) + val

val a = User("Ann", listOf("kotlin"))
val b = a.copy(tags = a.tags + "java") // new list, original untouched
println(a.tags) // [kotlin]

// Need mutation? Use copy:
val renamed = a.copy(name = "Bob")

// For arrays:
data class Holder(val bytes: ByteArray) {
    override fun equals(other: Any?) = other is Holder && bytes.contentEquals(other.bytes)
    override fun hashCode() = bytes.contentHashCode()
}
// Or use Kotlin 1.8.20+: @JvmInline value class with proper handling, or List<Byte>
```

**Rule:** `data class` → all `val` + read-only collections + no `var`. If you need `MutableList`, never expose it directly; `private` + `toList()` defensive copy.

## 6. Scope Function Confusion — `let`/`run`/`apply`/`also`/`with`

```kotlin
// BAD: nesting let for fun, wrong receiver, returning wrong thing
fun bad(user: User?) {
    user.let { it.name }.let { println(it) } // overkill, hard to read
    user.apply { name = "Bob" }.let { save(it) } // apply returns receiver, but reader expects transformed value
    // BAD: also vs let swapped
    val len = name.let { it.length }.also { println(it) } // works but intent unclear
}

// BAD: using let to silently handle null then forgetting else
user?.let { update(it) } // null does nothing — was that intended?
```

**Why:** Each scope function differs by receiver (`this` vs `it`) and return value (receiver vs lambda result). Misusing them returns the wrong object or hides null branches.

**Fix:**
```kotlin
// GOOD: use each for its intent, or skip them
// let — transform nullable and return lambda result
val length: Int? = user?.let { it.name.length }

// apply — configure object, return receiver
val user2 = User("Ann").apply {
    name = "Bob"
    tags = listOf("kotlin")
}

// also — side effect, return receiver
val logged = user.also { log.info("loaded $it") }

// run — compute with receiver as this, return lambda result
val grown = user.run { copy(name = name.uppercase()) }

// with — same as run but not extension
with(binding) { title.text = user.name }

// Prefer explicit over clever:
if (user != null) update(user) else showGuest() // clearer than user?.let { update(it) } ?: showGuest()
```

| Function | Receiver | Returns | Use For |
|---|---|---|---|
| `let` | `it` | lambda result | transform nullable, mapping |
| `run` | `this` | lambda result | compute with object scope |
| `apply` | `this` | receiver | builder/configure |
| `also` | `it` | receiver | side-effects/logging |
| `with` | `this` | lambda result | group calls on object |

**Rule:** If the chain is >2 scope functions, rewrite with `if`/`val`. Readability > cleverness.

## 7. `==` vs `===` and Broken `equals`/`hashCode` with Arrays and Inheritance

```kotlin
// BAD: === when you meant ==
val a = "hello"
val b = String("hello".toCharArray()) // different instance
println(a === b) // false — referential identity
println(a == b)  // true  — structural equality (calls equals)

// BAD: array equals is referential
val x = arrayOf(1,2)
val y = arrayOf(1,2)
println(x == y) // false! — Array.equals is ===

// BAD: open class with equals broken by subclass
open class Point(val x: Int, val y: Int)
class ColorPoint(x: Int, y: Int, val color: String) : Point(x, y)
// symmetry breaks: Point(1,2) == ColorPoint(1,2,"red") != ColorPoint(1,2,"red") == Point(1,2)
```

**Why:** In Kotlin, `==` is `equals()` (structural), `===` is referential identity. Java devs mix them; Kotlin devs forget `Array` doesn't override `equals`.

**Fix:**
```kotlin
// GOOD: default to ==
if (a == b) { ... } // structural

// For arrays: use contentEquals / contentDeepEquals
println(x.contentEquals(y)) // true
println(arrayOf(arrayOf(1)).contentDeepEquals(arrayOf(arrayOf(1)))) // true

// For equality hierarchy: prefer composition or make base sealed/data
sealed class Point {
    data class Plain(val x: Int, val y: Int) : Point()
    data class Colored(val x: Int, val y: Int, val color: String) : Point()
}
// Or if inheritance needed, don't override equals — use instance checks, or make class final
```

**Rule:** Use `==` always; reserve `===` for "is this the exact same instance?" checks. For arrays, always `contentEquals`.

## 8. Exhaustive `when` Defeated by `else`

```kotlin
// BAD: else hides missing branches — compiler can't help you
sealed class Result {
    data class Success(val data: String) : Result()
    data class Error(val msg: String) : Result()
    object Loading : Result()
}

fun handle(r: Result) = when (r) {
    is Result.Success -> show(r.data)
    is Result.Error -> showError(r.msg)
    else -> Unit // Loading silently ignored — bug!
}
// Later you add Result.Retry — else swallows it, no compile error
```

**Why:** `sealed class` + exhaustive `when` is Kotlin's superpower. Adding `else` opts out of the exhaustiveness check, so new subtypes compile but do nothing.

**Fix:**
```kotlin
// GOOD: no else — let compiler enforce exhaustiveness
fun handle(r: Result) = when (r) {
    is Result.Success -> show(r.data)
    is Result.Error -> showError(r.msg)
    Result.Loading -> showSpinner()
}
// Adding a new subtype → compile error here until you handle it

// If you truly need else, make it explicit and loud:
fun handleLenient(r: Result) = when (r) {
    is Result.Success -> show(r.data)
    is Result.Error -> showError(r.msg)
    else -> error("Unhandled Result: $r") // fail fast
}

// For enums, same rule — no else:
enum class Direction { NORTH, SOUTH, EAST, WEST }
fun move(d: Direction) = when (d) {
    Direction.NORTH -> goNorth()
    Direction.SOUTH -> goSouth()
    Direction.EAST -> goEast()
    Direction.WEST -> goWest()
}
```

**Rule:** Never add `else` to `when` on `sealed`/`enum`. Let the compiler be your checklist.

## 9. Swallowed Exceptions and Ignored Cancellation in Coroutines

```kotlin
// BAD: try/catch around launch doesn't catch inside
try {
    scope.launch { throw RuntimeException("boom") } // exception not caught here!
} catch (e: Exception) {
    log.error("never reached", e)
}

// BAD: catching CancellationException as failure
scope.launch {
    try {
        work()
    } catch (e: Exception) { // catches CancellationException too — breaks cancellation
        log.error("failed", e)
    }
}

// BAD: async exception ignored until await (or never)
scope.launch {
    val deferred = async { error("fail") }
    // forgot await() — exception lost, or crashes later via unhandled exception
}
```

**Why:** `launch` returns immediately; exceptions go to its `CoroutineExceptionHandler` or parent. `CancellationException` is how coroutines cancel — catching it as an error prevents cooperative cancellation.

**Fix:**
```kotlin
// GOOD: handle inside coroutine or via handler
scope.launch(CoroutineExceptionHandler { _, e -> log.error("launch failed", e) }) {
    mayThrow()
}

// GOOD: try/catch INSIDE the coroutine
scope.launch {
    try { mayThrow() }
    catch (e: CancellationException) { throw e } // always rethrow!
    catch (e: Exception) { log.error("work failed", e) }
}

// GOOD: supervisorScope for independent children
suspend fun loadAll(): List<Result> = supervisorScope {
    val a = async { fetchA() }
    val b = async { fetchB() }
    listOf(
        runCatching { a.await() },
        runCatching { b.await() }
    )
}

// GOOD: structured error with runCatching / Result
val data = runCatching { repo.fetch() }
    .onFailure { if (it is CancellationException) throw it }
    .getOrElse { fallback() }
```

**Rule:** Never `catch (Exception)` without rethrowing `CancellationException`. Handle coroutine errors *inside* the coroutine or with `CoroutineExceptionHandler`. Always `await()` your `async`.

## 10. Leaking Mutability — `List` vs `MutableList` and Defensive Copies

```kotlin
// BAD: exposing mutable internal state, accepting mutable lists as read-only
class Store(private val _items: MutableList<String>) {
    val items: List<String> get() = _items // still same instance! caller can cast to MutableList
    fun add(s: String) { _items.add(s) }
}

val ext = mutableListOf("a")
val store = Store(ext)
ext.add("b") // mutates store from outside!
(store.items as MutableList<String>).clear() // clears internal list via cast

// BAD: listOf vs mutableListOf confusion + defensive copy forgotten
data class Config(val hosts: List<String>) // caller passes MutableList, later mutates it
```

**Why:** Kotlin's `List` is read-only *view*, not immutable. `MutableList` is a `List`, so the underlying object is still mutable even when typed as `List`. Casting or sharing the reference breaks encapsulation.

**Fix:**
```kotlin
// GOOD: defensive copy + truly read-only exposure
class Store(items: List<String>) {
    private val _items = items.toMutableList() // copy at boundary
    val items: List<String> get() = _items.toList() // copy on read, or expose as unmodifiable
    // Or: val items: List<String> get() = Collections.unmodifiableList(_items) // Java interop safe
    fun add(s: String) { _items.add(s) }
}

// For data classes: copy at construction
data class Config(val hosts: List<String>) {
    init { require(hosts.isNotEmpty()) }
    // hosts is List — but ensure caller can't mutate by passing MutableList and later mutating:
    // Option: store copy
    // class Config(hosts: List<String>) { val hosts: List<String> = hosts.toList() }
}

// GOOD: prefer immutable builders
val items = buildList { add("a"); add("b") } // returns List
val mutable = mutableListOf("a"); val snapshot: List<String> = mutable.toList()

// For truly persistent immutable collections: kotlinx.collections.immutable
// val persistent: PersistentList<String> = persistentListOf("a")
```

**Rule:** At every public boundary, `toList()` / `toMutableList()` — copy in, copy out. Never store or return the same `MutableList` instance.

---

## Checklist Before You Commit

- [ ] No `!!`, no unchecked `lateinit` — use `?.`, `?:`, `requireNotNull`, `check(::x.isInitialized)`
- [ ] Every Java interop value treated as nullable (`String?`) until validated; `-Xjsr305=strict`
- [ ] No `GlobalScope` — scopes are injected and cancelled; use `coroutineScope`/`supervisorScope`
- [ ] No `Thread.sleep` or blocking I/O on `Dispatchers.Default/Main` — `delay` + `withContext(Dispatchers.IO)`
- [ ] `data class` is all `val` + `List` (not `MutableList`) + no arrays without `contentEquals`/`contentHashCode`
- [ ] Scope functions used by intent: `let` transform, `apply` configure, `also` side-effect
- [ ] `==` for structural, `contentEquals` for arrays, no `===` by accident
- [ ] No `else` in `when` on `sealed`/`enum` — let compiler enforce exhaustiveness
- [ ] `catch` rethrows `CancellationException`, `async` always `await`ed, errors handled inside coroutine
- [ ] No leaking `MutableList` — `toList()` at boundaries, `buildList` for construction

Nail these and Kotlin feels like the safe, expressive language it promised to be.

> Next: Kotlin Flow pitfalls (`SharedFlow` replay, `StateFlow` vs `LiveData`, `catch` vs `onEach`) or Gradle/KSP gotchas? Tell me what to cover.
