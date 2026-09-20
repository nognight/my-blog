---
title: 'Java 21 Reflection Lesson: Inspect and Invoke Code at Runtime'
pubDate: '2026-09-20'
description: 'A beginner-friendly lesson on Java Reflection — Class, Fields, Methods, Constructors — with runnable Java 21 examples, records, and pitfalls to avoid.'
heroImage: '../../assets/blog-placeholder-1.jpg'
tags:
  - java
  - java21
  - reflection
---

# Java 21 Reflection Lesson: Inspect and Invoke Code at Runtime

Reflection lets your program ask questions about itself at runtime: *What fields does this class have? What methods can I call? Can I create an instance even if I don't know the type at compile time?*

Frameworks you already use — Spring, Jackson, Hibernate, JUnit — are all built on it. This lesson gives you the 80% you actually need, with runnable Java 21 code.

> You need JDK 17+ for all examples below. Records, sealed classes, and pattern matching notes are marked where Java 21 matters.

## TL;DR

| You want to... | Use this | Example |
| :------------- | :------- | :------ |
| Get type metadata | `Class<?>` | `User.class`, `obj.getClass()`, `Class.forName("com.app.User")` |
| List members | `getDeclaredFields()` / `getDeclaredMethods()` / `getDeclaredConstructors()` | introspection |
| Read public API only | `getFields()` / `getMethods()` | includes inherited public members |
| Create instance | `ctor.newInstance(args)` | replaces deprecated `Class.newInstance()` |
| Read / write field | `field.get(obj)` / `field.set(obj, val)` | `setAccessible(true)` for `private` |
| Call method | `method.invoke(obj, args)` | unwrap `InvocationTargetException` |
| Modern alternative | `MethodHandles` / records / annotations | faster, safer when you can |

## 0. Setup: Our Demo Class

We'll reflect on this class through the whole lesson. Copy it into `Demo.java`:

```java
import java.util.Objects;

class User {
    private String name;
    private int age;

    public User() {
        this("anonymous", 0);
    }

    public User(String name, int age) {
        this.name = name;
        this.age = age;
    }

    public String getName() { return name; }
    private void birthday() { this.age++; }

    public String greet(String prefix) {
        return prefix + " " + name + ", age " + age;
    }

    @Override
    public String toString() {
        return "User{name='%s', age=%d}".formatted(name, age);
    }
}
```

Java 21 version with a `record` (we'll compare later):

```java
record UserRecord(String name, int age) {}
```

## 1. What Is Reflection (and When NOT to Use It)?

Normal Java is compile-time checked:

```java
User u = new User("Ada", 36);
u.greet("hello"); // compiler verifies method exists
```

Reflection is runtime-checked:

```java
Object u = Class.forName("User").getDeclaredConstructor().newInstance();
Method m = u.getClass().getDeclaredMethod("greet", String.class);
System.out.println(m.invoke(u, "hello")); // hello anonymous, age 0
```

**Use it when:**

- Writing frameworks, plugins, serializers, DI containers, test runners
- Type is only known at runtime (config file, annotation, JSON `"type"` field)
- Inspecting annotations for validation / routing

**Avoid it when:**

- A normal `interface`, `switch` pattern matching, or overload would do
- You're in hot code — reflective invocation is slower and blocks JIT inlining
- You can break encapsulation and surprise maintainers

> Rule of thumb: application code calls methods directly; library code uses reflection to *find* those methods.

## 2. Getting a `Class<?>` — 3 Ways

```java
// 1. Class literal — best when you know the type
Class<User> c1 = User.class;

// 2. From an instance — best in generic / polymorphic code
User u = new User("Ada", 36);
Class<? extends User> c2 = u.getClass();

// 3. By name — best for plugins / config-driven code
Class<?> c3 = Class.forName("User"); // fully-qualified name, e.g. "com.app.User"

System.out.println(c1 == c2); // true — one Class object per classloader
System.out.println(c1.getName());       // User (or com.app.User with package)
System.out.println(c1.getSimpleName()); // User
System.out.println(c1.getPackageName()); // "" here, usually "com.app"
```

**Beginner trap:** `int.class`, `int[].class`, and `void.class` are valid. Primitives have Class objects too:

```java
System.out.println(int.class.isPrimitive());     // true
System.out.println(String[].class.isArray());    // true
System.out.println(List.class.isInterface());    // true
System.out.println(UserRecord.class.isRecord()); // true — Java 16+
```

## 3. Inspecting Fields, Methods, Constructors

`getDeclared*` = exactly this class, any visibility, no inherited.
`get*` = public only, including inherited from superclasses.

```java
Class<User> c = User.class;

// --- Constructors ---
for (var ctor : c.getDeclaredConstructors()) {
    System.out.println(ctor);
}
// public User()
// public User(java.lang.String,int)

// --- Fields ---
for (var f : c.getDeclaredFields()) {
    System.out.printf("field %s : %s modifiers=%s%n",
        f.getName(), f.getType().getSimpleName(),
        java.lang.reflect.Modifier.toString(f.getModifiers()));
}
// field name : String modifiers=private
// field age : int modifiers=private

// --- Methods ---
for (var m : c.getDeclaredMethods()) {
    System.out.printf("method %s(%s) -> %s%n",
        m.getName(),
        String.join(",", java.util.Arrays.stream(m.getParameterTypes())
            .map(Class::getSimpleName).toList()),
        m.getReturnType().getSimpleName());
}
// method getName() -> String
// method birthday() -> void
// method greet(String) -> String
// method toString() -> String
```

Try this one-liner to see the difference:

```java
System.out.println("declared methods: " + c.getDeclaredMethods().length);
System.out.println("public methods (incl. Object): " + c.getMethods().length);
// getMethods() includes wait(), equals(), hashCode() from Object
```

**Java 21 tip — records are transparent:**

```java
for (var comp : UserRecord.class.getRecordComponents()) {
    System.out.println(comp.getName() + " : " + comp.getType().getSimpleName());
}
// name : String
// age : int
```

Prefer `getRecordComponents()` over field-scanning for records — it respects the canonical constructor contract.

## 4. Creating Instances

Never use the deprecated `Class.newInstance()`. Always go through a `Constructor`:

```java
// No-arg constructor
Constructor<User> noArg = User.class.getDeclaredConstructor();
User u1 = noArg.newInstance();

// Parameterized constructor
Constructor<User> full = User.class.getDeclaredConstructor(String.class, int.class);
User u2 = full.newInstance("Grace", 40);

System.out.println(u1); // User{name='anonymous', age=0}
System.out.println(u2); // User{name='Grace', age=40}
```

Handle the 3 checked exceptions you'll always see:

```java
try {
    var ctor = User.class.getDeclaredConstructor(String.class, int.class);
    User u = ctor.newInstance("Linus", 55);
} catch (NoSuchMethodException e) {
    // wrong parameter types
} catch (InstantiationException | IllegalAccessException e) {
    // abstract class / inaccessible (pre-setAccessible)
} catch (java.lang.reflect.InvocationTargetException e) {
    // constructor itself threw — cause is e.getCause()
    throw new RuntimeException(e.getCause());
}
```

## 5. Reading / Writing Fields (Even `private`)

```java
User u = new User("Ada", 36);
Field nameField = User.class.getDeclaredField("name");

nameField.setAccessible(true); // bypass private — required
System.out.println(nameField.get(u)); // Ada

nameField.set(u, "Hopper");
System.out.println(u); // User{name='Hopper', age=36}

// Type-safe accessors avoid boxing:
Field ageField = User.class.getDeclaredField("age");
ageField.setAccessible(true);
int age = ageField.getInt(u); // 36 — no cast
ageField.setInt(u, 37);
```

**Gotchas:**

1. `getField("name")` only finds `public` fields — use `getDeclaredField` for `private`.
2. `final` fields: you *can* `setAccessible(true)` + `set()` on instance finals, but JIT may have inlined the value. Don't do it — construct a new object instead.
3. Static fields: pass `null` as the instance: `field.get(null)`.

```java
record UserRecord(String name, int age) {}
// Records: fields are private final + canonical accessor name()
// Prefer u.name() over reflection — reflection is for generic code
```

## 6. Invoking Methods (Even `private`)

```java
User u = new User("Ada", 36);

// Public method with args
Method greet = User.class.getDeclaredMethod("greet", String.class);
System.out.println(greet.invoke(u, "hi")); // hi Ada, age 36

// Private method, no args
Method birthday = User.class.getDeclaredMethod("birthday");
birthday.setAccessible(true);
birthday.invoke(u);
System.out.println(u); // User{name='Ada', age=37}
```

Unwrap exceptions correctly — `invoke` wraps everything:

```java
try {
    greet.invoke(u, "hi");
} catch (java.lang.reflect.InvocationTargetException e) {
    Throwable cause = e.getCause(); // the real exception from inside greet()
    throw new RuntimeException(cause);
} catch (IllegalAccessException e) {
    throw new RuntimeException(e);
}
```

**Varargs trap:**

```java
class V {
    public String join(String... parts) { return String.join("-", parts); }
}
Method m = V.class.getDeclaredMethod("join", String[].class);
Object r = m.invoke(new V(), (Object) new String[]{"a", "b"});
// cast to Object! Otherwise invoke thinks a,b are separate args
```

## 7. Annotations + A Mini JSON Mapper (Putting It Together)

This is what frameworks do: scan annotations, then get/set fields.

```java
import java.lang.annotation.*;
import java.lang.reflect.Field;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
@interface JsonName {
    String value();
}

class Product {
    @JsonName("id") private long productId = 7;
    @JsonName("title") private String name = "keyboard";
    private double price = 49.99; // no annotation -> use field name
}

static String toJson(Object obj) throws Exception {
    var sb = new StringBuilder("{");
    boolean first = true;
    for (Field f : obj.getClass().getDeclaredFields()) {
        f.setAccessible(true);
        String key = f.isAnnotationPresent(JsonName.class)
            ? f.getAnnotation(JsonName.class).value()
            : f.getName();
        if (!first) sb.append(",");
        first = false;
        Object v = f.get(obj);
        sb.append('\"').append(key).append("\":");
        sb.append(v instanceof String s ? '\"' + s + '\"' : v);
    }
    return sb.append("}").toString();
}

System.out.println(toJson(new Product()));
// {"id":7,"title":"keyboard","price":49.99}
```

One pattern, endless uses: validation (`@Min(0)`), routing (`@Get("/users")`), DI (`@Inject`).

## 8. Java 21 Realities: Modules, Performance, Safer Alternatives

### a) Modules (JPMS) can block you

On the classpath everything above works. With `module-info.java`, reflective access to another module needs openness:

```java
// module-info.java of the target module
module com.app {
    opens com.app.entities to com.fasterxml.jackson.databind; // reflection allowed
    // exports com.app.api; // compile-time access only, NOT reflection on private members
}
```

If you see `InaccessibleObjectException: Unable to make field private ... accessible`, the fix is `--add-opens` (dev/test) or a proper `opens ... to` directive (production). Don't just add `--add-opens java.base/java.lang=ALL-UNNAMED` everywhere.

### b) Performance: cache everything

Reflection lookup is expensive; invocation is cheaper but still not free.

```java
// BAD: lookup on every call
for (var row : rows) {
    Method m = row.getClass().getMethod("getId"); // repeated scan!
    m.invoke(row);
}

// GOOD: cache Method/Field once
private static final Method GET_ID = init();
static Method init() {
    try {
        return User.class.getMethod("getName");
    } catch (NoSuchMethodException e) {
        throw new IllegalStateException(e);
    }
}
```

For hot paths, `MethodHandles` (Java 7+) inlines better and respects module boundaries:

```java
import java.lang.invoke.*;

MethodHandles.Lookup lookup = MethodHandles.lookup();
MethodHandle greetMH = lookup.findVirtual(User.class, "greet",
    MethodType.methodType(String.class, String.class));
System.out.println((String) greetMH.invokeExact(new User("Ada", 1), "hi"));
```

Rule: reflection for discovery, `MethodHandle` / direct call for repeated invocation.

### c) Pattern matching reduces reflection

Before Java 21 you often reflected to branch on type. Now prefer pattern matching:

```java
// Old: if (obj.getClass().getSimpleName().equals("User")) ...
// New (Java 21):
static String describe(Object o) {
    return switch (o) {
        case User u -> "user " + u.getName();
        case UserRecord r -> "record " + r.name();
        case null -> "null";
        default -> "unknown " + o.getClass().getSimpleName();
    };
}
```

Use reflection to *discover*, pattern matching to *dispatch*.

## 9. Common Mistakes Checklist

- [ ] Used `getField` / `getMethod` and got `NoSuchFieldException` — you wanted `getDeclaredField` / `getDeclaredMethod` for `private` members
- [ ] Forgot `setAccessible(true)` on private field/method/constructor
- [ ] Used deprecated `Class.newInstance()` — use `getDeclaredConstructor().newInstance()`
- [ ] Swallowed `InvocationTargetException` — always unwrap `getCause()`
- [ ] Looked up `Method` in a loop — cache it in a `static final`
- [ ] Tried to mutate `record` / `final` field — construct a new instance instead
- [ ] Hit `InaccessibleObjectException` — missing `opens ... to` in `module-info.java`
- [ ] Used reflection where `interface` + pattern matching would be clearer

## Exercises

1. **Inspector:** write `printClassInfo(Class<?> c)` that prints superclass, interfaces, sealed subclasses (`c.getPermittedSubclasses()`), and whether it's a record/enum/annotation.
2. **DI mini-container:** scan fields annotated with `@Inject`, instantiate them via no-arg constructor, and inject. What happens with `final` fields? With cycles?
3. **Speed test:** time 1M calls of direct `u.greet("hi")` vs cached `Method.invoke` vs `MethodHandle.invokeExact`. What's the ratio on your JDK 21?

> Next: Want a follow-up on `MethodHandles + VarHandles` vs reflection performance on JDK 21, or annotation-processor (compile-time) codegen to avoid reflection entirely? Let me know.
