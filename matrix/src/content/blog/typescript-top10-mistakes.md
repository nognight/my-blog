---
title: 'Top 10 Easy-to-Miss Mistakes in TypeScript Programming'
pubDate: '2026-09-06'
description: '10 common TypeScript mistakes, from any and unsafe assertions to missing runtime validation and incomplete unions, with practical examples and fixes.'
heroImage: '../../assets/blog-placeholder-3.jpg'
tags:
  - typescript
  - programming
  - pitfalls
---

# Top 10 Easy-to-Miss Mistakes in TypeScript Programming

TypeScript helps catch mistakes before code runs, but its protection depends on the types you give it. These ten pitfalls show where that protection can disappear and how to restore it.

Examples marked BAD demonstrate either a compiler error or a runtime bug, as noted. Treat each code block as an independent example.

## 1. Using `any` as a Shortcut

```ts
// BAD: compiles, then throws at runtime
function shout(value: any) {
  return value.toUpperCase();
}
shout(42);

// GOOD: require callers to supply a string
function shoutText(value: string) {
  return value.toUpperCase();
}
```

**Fix:** Describe known inputs precisely. For values you have not validated, use `unknown` and check them before accessing properties. `any` lets unchecked operations propagate through your code. See the [handbook on any](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#any).

## 2. Assuming an API Response Matches an Interface

```ts
type User = { name: string };

// BAD: the annotation does not inspect the parsed JSON
const user: User = JSON.parse('{"name":42}');
// user.name.toUpperCase() would throw

// GOOD: validate the external value
function parseUser(value: unknown): User {
  if (
    typeof value !== 'object' ||
    value === null ||
    !('name' in value) ||
    typeof value.name !== 'string'
  ) {
    throw new Error('Expected a user with a string name');
  }
  return { name: value.name };
}

const raw: unknown = JSON.parse('{"name":"Ada"}');
const validated = parseUser(raw);
console.log(validated.name.toUpperCase());
```

**Fix:** Validate data where it enters your application: API responses, storage, configuration, and forms. For larger structures, use a runtime schema validator. An interface alone cannot reject malformed input.

## 3. Treating `as` as a Conversion

```ts
// BAD: a double assertion hides the mismatch
const raw = '42';
const fakeNumber = raw as unknown as number;
console.log(fakeNumber + 1); // '421'

// GOOD: convert the value and check the result
const number = Number(raw);
if (raw.trim() === '' || !Number.isFinite(number)) {
  throw new Error('Expected a finite number');
}
console.log(number + 1); // 43
```

**Why:** Assertions change the compiler's view, not the runtime value. Use conversion functions when the value must change, and validation when its shape is uncertain. See [type assertions](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions).

## 4. Silencing Missing Values with `!`

```ts
const users = [{ id: 1, name: 'Ada' }];

// BAD: compiles, but find() can return undefined
function unsafeName(id: number) {
  return users.find(user => user.id === id)!.name;
}

// GOOD: decide what a missing user means
function getName(id: number) {
  const user = users.find(user => user.id === id);
  if (!user) throw new Error(`User ${id} was not found`);
  return user.name;
}
```

**Fix:** Handle absence with a guard, an explicit error, or a meaningful fallback. The [non-null assertion operator](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#non-null-assertion-operator-postfix-) does not add a runtime check.

## 5. Leaving Strict Checks Disabled

```ts
// BAD: accepted with strictNullChecks disabled; throws if called
function broken(): string {
  const name: string = undefined;
  return name.toUpperCase();
}
```

**Fix:** Enable strict checking in your project's existing `tsconfig.json`. Consider these additional checks too:

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

`strict` includes null and implicit-any checks. The two additional options are separate: one exposes potentially missing indexed values; the other distinguishes an absent optional property from an explicitly assigned `undefined`. See the [TSConfig reference](https://www.typescriptlang.org/tsconfig/).

## 6. Assuming Array and Dictionary Lookups Always Succeed

```ts
const names: string[] = [];

// BAD: throws at runtime; flagged with noUncheckedIndexedAccess
// names[0].toUpperCase();

// GOOD: handle the empty collection
const first = names[0];
if (first !== undefined) {
  console.log(first.toUpperCase());
}

// GOOD: describe a dictionary whose keys may be missing
const scores: Record<string, number | undefined> = {};
const score = scores['Ada'] ?? 0;
```

**Fix:** Make missing entries part of your design. `Record<string, number>` does not populate a dictionary, and an array type does not guarantee an element exists at every index. The [noUncheckedIndexedAccess option](https://www.typescriptlang.org/tsconfig/#noUncheckedIndexedAccess) helps expose this assumption.

## 7. Using Truthiness When Zero or Empty Text Is Valid

```ts
// BAD: skips a valid zero
function printCount(count: number | undefined) {
  if (count) console.log(count);
}

// GOOD: check the missing value explicitly
function printCountSafely(count: number | undefined) {
  if (count !== undefined) console.log(count);
}

const settings: { volume?: number } = { volume: 0 };
const volume = settings.volume ?? 50; // keeps 0
```

**Fix:** Distinguish absence from falsy values. Use `??` for nullish defaults and explicit checks when `0`, `false`, or `''` carries meaning. See [truthiness narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#truthiness-narrowing).

## 8. Modeling Related States with Unrelated Optional Properties

```ts
// BAD: permits success without data
type LooseResult = {
  status: 'success' | 'error';
  data?: string;
  error?: string;
};
const invalid: LooseResult = { status: 'success' };

// GOOD: each status requires its corresponding payload
type Result =
  | { status: 'success'; data: string }
  | { status: 'error'; error: string };

function render(result: Result): string {
  switch (result.status) {
    case 'success': return result.data;
    case 'error': return result.error;
    default: {
      const exhaustive: never = result;
      return exhaustive;
    }
  }
}
```

**Fix:** Use a discriminated union for mutually exclusive states. The `never` assignment also produces a compiler error if you add a new variant without handling it. See [discriminated unions and exhaustiveness checking](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#discriminated-unions).

## 9. Assuming `Readonly<T>` Makes Nested Data Immutable

```ts
type Settings = Readonly<{
  theme: { color: string };
}>;

const original: Settings = { theme: { color: 'blue' } };
const copy = { ...original };

// BAD: allowed, and also changes original.theme.color
copy.theme.color = 'red';

// GOOD: copy the nested object when updating it
const updated: Settings = {
  ...original,
  theme: { ...original.theme, color: 'green' },
};
```

**Fix:** Apply readonly types at each level you need to protect, and copy the nested branches you change. Readonly types provide compile-time restrictions; they do not freeze JavaScript objects. A spread copy is also shallow.

## 10. Casting Caught Errors Instead of Narrowing Them

```ts
// BAD: JavaScript can throw strings, null, or other values
function unsafeMessage(error: unknown) {
  return (error as Error).message.toUpperCase();
}

// GOOD: check before using Error properties
function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

try {
  throw 'Connection closed';
} catch (error) {
  console.error(errorMessage(error));
}
```

**Fix:** Keep caught values as `unknown` until checked. Strict mode enables this through [useUnknownInCatchVariables](https://www.typescriptlang.org/tsconfig/#useUnknownInCatchVariables). Decide separately whether to recover, report, or rethrow the failure.

---

## Checklist Before You Commit

- [ ] Known inputs have precise types; unvalidated inputs use `unknown`.
- [ ] External data is validated at runtime.
- [ ] Assertions are justified; conversions actually transform values.
- [ ] Missing values are handled without relying on `!`.
- [ ] Strict checks are enabled and indexed-access checks considered.
- [ ] Empty arrays and missing dictionary keys are handled.
- [ ] Zero, false, and empty strings survive defaults when valid.
- [ ] Related states use discriminated unions with exhaustive handling.
- [ ] Nested updates avoid accidental shared mutation.
- [ ] Caught errors are narrowed before accessing their properties.

Run your project's type-check command before committing, alongside tests for runtime behavior. Types are most useful when they accurately describe what your code can receive and return.
