---
title: 'Top 10 Easy-to-Miss Mistakes in JavaScript Programming'
pubDate: '2026-08-25'
description: '10 JavaScript pitfalls that trip up beginners and seniors alike — from == vs === to closure traps and async gotchas — with broken code and fixes.'
heroImage: '../../assets/blog-placeholder-3.jpg'
tags:
  - javascript
  - programming
  - pitfalls
---

# Top 10 Easy-to-Miss Mistakes in JavaScript Programming

JavaScript is forgiving until it isn't. These 10 bugs survive code reviews, pass local tests, then explode in production.

## 1. `==` vs `===` — Loose Equality Coercion

```js
// BAD: loose equality does type coercion
0 == ''      // true
0 == '0'     // true
null == undefined // true
'0' == false // true

// GOOD: strict equality
0 === ''     // false
0 === '0'    // false
null === undefined // false
```

**Why:** `==` triggers `Abstract Equality Comparison` — it coerces types via `ToNumber`, `ToPrimitive`.

**Fix:** Always use `===` / `!==`. Enable ESLint `eqeqeq`. The only allowed `== null` is a shorthand for `x === null || x === undefined`.

## 2. `var` Hoisting & Function Scoping

```js
// BROKEN
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}
// logs 3, 3, 3 — not 0,1,2

// Reason: var is function-scoped & hoisted; the closure captures ONE binding

// FIXED
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}
// 0,1,2 — let is block-scoped, new binding per iteration

// Or IIFE for legacy
for (var i = 0; i < 3; i++) {
  (function(j){ setTimeout(() => console.log(j), 0); })(i);
}
```

**Fix:** Never use `var`. Use `let`/`const`. `const` by default, `let` when reassignment is needed.

## 3. `this` Lost in Callbacks

```js
class Counter {
  count = 0;
  inc() { this.count++; }
}
const c = new Counter();
setTimeout(c.inc, 0); // this === undefined (strict) or window
console.log(c.count); // still 0

// FIX
setTimeout(() => c.inc(), 0);           // arrow preserves lexical this
setTimeout(c.inc.bind(c), 0);            // bind
// Or class field arrow:
class Counter2 {
  count = 0;
  inc = () => { this.count++; }
}
```

**Why:** `this` is set by call-site, not definition-site. Passing `obj.method` detaches it.

**Fix:** Use arrow wrappers, `bind`, or arrow class fields.

## 4. Async Errors Swallowed

```js
// BAD: try/catch won't catch async
try {
  setTimeout(() => { throw new Error('boom'); }, 0);
} catch (e) { /* never reaches */ }

// BAD: floating promise — unhandled rejection
async function load() {
  fetch('/api'); // missing await → errors silently lost
}

// GOOD
async function load() {
  try {
    const res = await fetch('/api');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.error('load failed', e);
    throw e; // or return fallback
  }
}
// Top-level: handle rejections
window.addEventListener('unhandledrejection', e => {
  console.error(e.reason);
});
```

**Fix:** Always `await` or `return` promises. `try/catch` only works *inside* `async` functions with `await`.

## 5. Mutating While Iterating & Reference Sharing

```js
// BAD: object reference shared
const row = { x: 0 };
const matrix = Array(3).fill(row); // same object 3 times
matrix[0].x = 1; // matrix[1].x and [2].x also 1!

// GOOD
const matrix2 = Array.from({length: 3}, () => ({ x: 0 }));
// Or
const a = [1,2,3];
const b = [...a];        // shallow copy
const c = structuredClone(a); // deep (Node 17+/modern browsers)

// BAD: splice while forEach
const list = [1,2,3,4];
list.forEach((n, i) => { if (n === 2) list.splice(i,1); }); // skips elements

// GOOD
const filtered = list.filter(n => n !== 2);
```

## 6. `NaN`, `0.1 + 0.2`, and Type Checks

```js
typeof NaN          // 'number' — yep
NaN === NaN         // false
Number.isNaN('hi')  // false (correct) — vs isNaN('hi') → true (coerces!)

0.1 + 0.2 === 0.3   // false → 0.30000000000000004

// FIX
Number.isNaN(x)              // strict check
Object.is(NaN, NaN)          // true
Math.abs(0.1+0.2 - 0.3) < Number.EPSILON // true
// For money: use integers (cents) or Decimal.js
const cents = Math.round((0.1 + 0.2) * 100); // 30
```

## 7. Falsy Traps — `0`, `''`, `false` as Valid Values

```js
function setPage(page) {
  // BAD: 0 is valid but falsy
  const p = page || 1; // setPage(0) → 1, wrong
  // BAD: same with ??
  // Actually ?? is GOOD — only null/undefined

  // GOOD
  const p1 = page ?? 1;          // 0 stays 0, only null/undefined → 1
  const p2 = page !== undefined ? page : 1;

  // Same trap with destructuring defaults:
  function greet({name} = {}) {
    // name = '' (empty) is valid but || would replace it
    const n = name ?? 'guest';
  }
}
```

**Fix:** Use `??` (nullish coalescing) and `?.` (optional chaining) for defaults. Reserve `||` for boolean defaults only.

## 8. Forgetting `await` in Loops (Parallel vs Sequential)

```js
// BAD: forEach doesn't await
const ids = [1,2,3];
ids.forEach(async id => {
  await fetch(`/api/${id}`); // fires in parallel, outer function doesn't wait
});
console.log('done'); // runs before fetches finish

// BAD: sequential when you wanted parallel
for (const id of ids) {
  await fetch(`/api/${id}`); // waits one by one → slow
}

// GOOD: parallel
await Promise.all(ids.map(id => fetch(`/api/${id}`)));
// GOOD: sequential (when order matters)
for (const id of ids) {
  await fetch(`/api/${id}`);
}
// GOOD: with concurrency limit (p-limit)
```

**Fix:** Never `forEach(async)`. Use `for...of` with `await` or `Promise.all`.

## 9. Prototype Pollution & `hasOwnProperty` Bypass

```js
const user = {};
// BAD: if payload contains __proto__, you pollute Object.prototype
// JSON.parse('{"__proto__": {"isAdmin": true}}') can poison all objects

// BAD: hasOwnProperty can be shadowed
const obj = { hasOwnProperty: () => true, x: 1 };
obj.hasOwnProperty('y'); // true — lies!

// GOOD
Object.prototype.hasOwnProperty.call(obj, 'y'); // false
// Or
Object.hasOwn(obj, 'y'); // ES2022

// For dict maps: use null-prototype or Map
const dict = Object.create(null); // no prototype
dict['__proto__'] = 1; // safe
// Or
const map = new Map();
map.set('__proto__', 1);

// Parse JSON safely
function safeParse(json) {
  const data = JSON.parse(json);
  if ('__proto__' in data || 'constructor' in data) throw new Error('pollution');
  return data;
}
```

## 10. Timer / Event Listener Leaks

```js
// BAD: setInterval never cleared, listeners never removed
useEffect(() => {
  const id = setInterval(tick, 1000);
  window.addEventListener('resize', handler);
  // no cleanup → leak on unmount, duplicate handlers
}, []);

// GOOD: React
useEffect(() => {
  const id = setInterval(tick, 1000);
  window.addEventListener('resize', handler);
  return () => {
    clearInterval(id);
    window.removeEventListener('resize', handler);
  };
}, []);

// GOOD: vanilla
const controller = new AbortController();
window.addEventListener('click', handler, { signal: controller.signal });
// later: controller.abort(); // removes all listeners with signal

// Debounce expensive handlers
const onScroll = debounce(handler, 100);
```

**Why:** SPAs live long. Leaked intervals/listeners accumulate → memory bloat, duplicate calls.

---

## Checklist Before You Commit

- [ ] No `==`, no `var`, `===` + `let`/`const` only
- [ ] Every promise `await`ed or `return`ed, `unhandledrejection` handled
- [ ] No `forEach(async)`, use `for...of` or `Promise.all`
- [ ] `this` preserved via arrow/bind when passing methods
- [ ] Falsy defaults use `??` not `||`
- [ ] `0.1+0.2` compared with `EPSILON` or cents
- [ ] Object maps use `Map` or `Object.create(null)`, check with `Object.hasOwn`
- [ ] Intervals/listeners cleaned up with `clearInterval` / `AbortController`

Catch these once and you'll stop chasing ghosts at 2am.

> Next up: `fetch` vs `axios` footguns, or `TypeScript` strict-mode saves? Let me know what to cover.
