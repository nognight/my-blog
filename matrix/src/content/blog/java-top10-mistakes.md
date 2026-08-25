---
title: 'Top 10 Easy-to-Miss Mistakes in Java Programming'
pubDate: '2026-08-25'
description: '10 classic Java pitfalls that even experienced developers hit — from == vs equals to concurrency traps — with real code examples and fixes.'
heroImage: '../../assets/blog-placeholder-2.jpg'
tags:
  - java
  - programming
  - pitfalls
---

# Top 10 Easy-to-Miss Mistakes in Java Programming

Java looks simple, but its details will bite you. Here are 10 traps I see most often in code reviews — each with a broken example, why it fails, and the fix.

## 1. `==` vs `equals()` on Strings (and Wrappers)

```java
String a = new String("hello");
String b = new String("hello");
System.out.println(a == b);        // false — compares references!
System.out.println(a.equals(b));   // true  — compares content

Integer x = 127, y = 127;
System.out.println(x == y);        // true  (cached -128..127)
Integer m = 128, n = 128;
System.out.println(m == n);        // false — different objects!
```

**Why:** `==` checks identity, `equals()` checks value. `Integer` cache only covers `-128` to `127`.

**Fix:** Always use `equals()` for object value comparison. For null-safe: `Objects.equals(a, b)`.

## 2. String Concatenation in Loops

```java
// BAD: creates O(n²) garbage
String s = "";
for (String w : words) s += w;

// GOOD
StringBuilder sb = new StringBuilder(words.size() * 8);
for (String w : words) sb.append(w);
String s2 = sb.toString();
```

**Why:** `String` is immutable — each `+=` copies the whole string.

**Fix:** Use `StringBuilder` (or `StringJoiner` / `String.join()`). In Java 8+ streams: `Collectors.joining()`.

## 3. Forgetting `equals()`/`hashCode()` Contract

```java
class User {
    String id; String name;
    // equals() overridden but hashCode() not — breaks HashMap/HashSet
}

Set<User> set = new HashSet<>();
set.add(new User("1", "A"));
set.contains(new User("1", "A")); // false!
```

**Why:** `HashMap`/`HashSet` bucket by `hashCode()` first. If `a.equals(b)` then `a.hashCode() == b.hashCode()` must hold.

**Fix:** Override both together. Use `record` (Java 16+) or Lombok `@EqualsAndHashCode`, or IDE generation. Or `Objects.hash(id, name)`.

## 4. Mutable `Date` / `SimpleDateFormat` Shared Across Threads

```java
// BAD: SimpleDateFormat is NOT thread-safe
private static final SimpleDateFormat FMT = new SimpleDateFormat("yyyy-MM-dd");

// Thread A and B call FMT.format() concurrently -> corrupt output / exception
```

**Fix:**
```java
// Java 8+: use immutable java.time
private static final DateTimeFormatter FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd");
LocalDate.now().format(FMT);

// Or ThreadLocal if stuck on old API
private static final ThreadLocal<DateFormat> TL = ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd"));
```

## 5. `ConcurrentModificationException` — Modifying List While Iterating

```java
List<String> list = new ArrayList<>(List.of("a","b","c"));
for (String s : list) {
    if (s.equals("b")) list.remove(s); // throws!
}
```

**Fix:**
```java
// Option 1: Iterator
Iterator<String> it = list.iterator();
while (it.hasNext()) if (it.next().equals("b")) it.remove();

// Option 2: removeIf (Java 8+)
list.removeIf(s -> s.equals("b"));

// Option 3: CopyOnWrite or stream filter
list = list.stream().filter(s -> !s.equals("b")).toList();
```

## 6. Resource Leaks — Not Closing Streams / Connections

```java
// BAD: leaks file handle if exception occurs
BufferedReader br = new BufferedReader(new FileReader("data.txt"));
String line = br.readLine();
```

**Fix:** try-with-resources (Java 7+):
```java
try (var br = new BufferedReader(new FileReader("data.txt"));
     var conn = dataSource.getConnection();
     var ps = conn.prepareStatement(sql)) {
    // auto-closed even on exception
}
```

## 7. `NullPointerException` via Autoboxing & Unboxing

```java
Map<String, Integer> map = new HashMap<>();
Integer count = map.get("missing"); // null
int total = count + 1;              // NPE on unboxing!

// Also:
void foo(Integer n) { ... }
foo(null); // NPE if you do n + 1 inside
```

**Fix:**
```java
int total = map.getOrDefault("missing", 0) + 1;
int safe = Objects.requireNonNullElse(count, 0);
if (count != null) { ... }
```

## 8. Off-by-One & `subString` / `Array` Bounds

```java
String s = "hello";
s.substring(1, 5); // "ello" — end is exclusive
s.substring(1, 6); // StringIndexOutOfBoundsException

List<String> list = Arrays.asList("a","b");
list.get(2); // IndexOutOfBoundsException — last index is 1
```

**Common variant:** `for (int i = 0; i <= list.size(); i++)` — the `<=` is wrong.

**Fix:** Remember `length-1` and exclusive end. Prefer enhanced for / `list.forEach` / streams.

## 9. Ignoring Exceptions & Swallowing Stack Traces

```java
try {
    doSomething();
} catch (Exception e) {
    // BAD: silent failure
}
// Or:
catch (IOException e) {
    e.printStackTrace(); // goes to stderr, lost in prod
    return null;         // caller gets NPE later
}
```

**Fix:**
```java
catch (IOException e) {
    log.error("Failed to load config {}", path, e);
    throw new ServiceException("load failed", e); // preserve cause
}
// Or if you really must ignore, comment why:
// ignored: timeout is best-effort
```

## 10. Concurrency: `volatile` Is Not `synchronized`, Double-Checked Locking Broken

```java
// BAD: two threads can both see count==0 and create two instances
class Lazy {
    private static Lazy instance;
    public static Lazy get() {
        if (instance == null) instance = new Lazy(); // race!
        return instance;
    }
}

// Also BAD: volatile alone doesn't make increment atomic
private volatile int count;
public void inc() { count++; } // read-modify-write, still racy
```

**Fix:**
```java
// Option 1: enum singleton (simplest)
enum Lazy { INSTANCE; }

// Option 2: correct DCL with volatile + synchronized
class Lazy {
    private static volatile Lazy instance;
    public static Lazy get() {
        if (instance == null) {
            synchronized (Lazy.class) {
                if (instance == null) instance = new Lazy();
            }
        }
        return instance;
    }
}

// Option 3: atomics for counters
private final AtomicInteger count = new AtomicInteger();
public void inc() { count.incrementAndGet(); }
```

---

## Checklist Before You Commit

- [ ] `equals()` ⇔ `equals()` + `hashCode()` together, or use `record`
- [ ] No `==` on Strings/Wrappers
- [ ] No `String +=` in loops
- [ ] No shared `SimpleDateFormat` / mutable statics
- [ ] No `list.remove()` inside for-each — use `removeIf` / `Iterator`
- [ ] Every `Closeable` in try-with-resources
- [ ] Null-check before unboxing (`getOrDefault`, `Optional`)
- [ ] Thread-safety reviewed for singletons & counters

Small details, big bugs. Fix them once and they stay fixed.

> Next: Want a follow-up on Java Stream pitfalls (`flatMap` + `null`, `collect` vs `reduce`)? Let me know.
