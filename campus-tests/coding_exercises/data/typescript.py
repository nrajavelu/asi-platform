EXERCISES = [
    {
        "id": "TS-01",
        "flavor": "generics",
        "difficulty": "medium",
        "title": "Generic TTL Cache",
        "scenario": "Your team's backend makes expensive calls to a pricing service. You need a small in-memory cache that can store values of ANY type (strings, numbers, objects) keyed by string, where each entry automatically expires after a given time-to-live (TTL) in milliseconds.",
        "code_reference": "interface CacheEntry<T> {\n  value: T;\n  expiresAt: number;\n}\n\nclass TypedCache<T> {\n  private store = new Map<string, CacheEntry<T>>();\n\n  set(key: string, value: T, ttlMs: number): void {\n    // TODO: implement\n  }\n\n  get(key: string): T | undefined {\n    // TODO: implement\n  }\n}",
        "tasks": [
            "Implement `set` so it stores the value with an expiry timestamp computed from `ttlMs`.",
            "Implement `get` so it returns `undefined` if the key is missing OR if the entry has expired (and delete expired entries when found).",
            "Add a `has(key: string): boolean` method that reuses `get` to check freshness without duplicating expiry logic."
        ],
        "reference_solution_code": "interface CacheEntry<T> {\n  value: T;\n  expiresAt: number;\n}\n\nclass TypedCache<T> {\n  private store = new Map<string, CacheEntry<T>>();\n\n  set(key: string, value: T, ttlMs: number): void {\n    this.store.set(key, { value, expiresAt: Date.now() + ttlMs });\n  }\n\n  get(key: string): T | undefined {\n    const entry = this.store.get(key);\n    if (!entry) return undefined;\n    if (Date.now() > entry.expiresAt) {\n      this.store.delete(key);\n      return undefined;\n    }\n    return entry.value;\n  }\n\n  has(key: string): boolean {\n    return this.get(key) !== undefined;\n  }\n}",
        "check_points": [
            "Class is declared generic over `T` and the internal Map is typed with `CacheEntry<T>`, not `any`.",
            "`get` checks both existence and expiry before returning a value.",
            "Expired entries are removed from the store (not just skipped) when encountered.",
            "`has` does not duplicate the expiry-check logic (reuses `get` or equivalent)."
        ],
        "common_mistakes": [
            "Typing the store as `Map<string, T>` and storing expiry separately, losing atomicity between value and timestamp.",
            "Using `any` for the value type instead of the generic parameter `T`.",
            "Forgetting to delete expired entries, causing the map to grow unbounded.",
            "Comparing `expiresAt` with `<` instead of `>`, inverting the expiry logic."
        ],
        "rubric": [
            ["Correct generic typing throughout", 40],
            ["Correct expiry logic in get/set", 40],
            ["has() implemented cleanly", 20]
        ],
    },
    {
        "id": "TS-02",
        "flavor": "discriminated-union",
        "difficulty": "medium",
        "title": "API Response Renderer",
        "scenario": "A frontend component needs to render three possible states of a data fetch: still loading, successfully loaded with data, or failed with an error message. You want the type system to guarantee every state is handled before the code compiles.",
        "code_reference": "type ApiResponse<T> =\n  | { status: 'loading' }\n  | { status: 'success'; data: T }\n  | { status: 'error'; error: string };\n\nfunction renderResponse<T>(response: ApiResponse<T>, formatData: (data: T) => string): string {\n  // TODO: implement using a switch on response.status\n}",
        "tasks": [
            "Implement `renderResponse` using a `switch` on `response.status` that returns an appropriate string for each state.",
            "For the `success` case, call `formatData` on `response.data`.",
            "Add a `default` branch that assigns the remaining value to a variable typed `never`, so that if a new state is ever added the code fails to compile."
        ],
        "reference_solution_code": "type ApiResponse<T> =\n  | { status: 'loading' }\n  | { status: 'success'; data: T }\n  | { status: 'error'; error: string };\n\nfunction renderResponse<T>(response: ApiResponse<T>, formatData: (data: T) => string): string {\n  switch (response.status) {\n    case 'loading':\n      return 'Loading...';\n    case 'success':\n      return formatData(response.data);\n    case 'error':\n      return `Error: ${response.error}`;\n    default: {\n      const exhaustiveCheck: never = response;\n      return exhaustiveCheck;\n    }\n  }\n}",
        "check_points": [
            "Uses the `status` discriminant to narrow the union in each branch.",
            "Accesses `response.data` only inside the `success` branch and `response.error` only inside `error`.",
            "Includes an exhaustiveness check (`never`) so future added variants cause a compile error.",
            "Does not use type assertions (`as`) to force access to fields that don't exist on a branch."
        ],
        "common_mistakes": [
            "Using `if/else` chains checking `'data' in response` instead of the discriminant field, which is fragile.",
            "Casting `response as any` to access `.data` regardless of status.",
            "Omitting the exhaustiveness (`never`) check so a new union member silently falls through.",
            "Forgetting the generic `<T>` and hardcoding a concrete data type."
        ],
        "rubric": [
            ["Correct discriminated union narrowing", 45],
            ["All three states handled correctly", 35],
            ["Exhaustiveness check present", 20]
        ],
    },
    {
        "id": "TS-03",
        "flavor": "utility-types",
        "difficulty": "medium",
        "title": "Partial Profile Update",
        "scenario": "Your app's 'edit profile' form lets a user change their name, email, age, and bio, but never their `id`. You want a single update function whose type signature makes it impossible to accidentally overwrite the `id` field, while allowing any subset of the other fields to be updated.",
        "code_reference": "interface UserProfile {\n  id: string;\n  name: string;\n  email: string;\n  age: number;\n  bio: string;\n}\n\nfunction updateProfile(profile: UserProfile, updates: /* TODO: type */): UserProfile {\n  // TODO: implement\n}",
        "tasks": [
            "Write the type for `updates` using built-in utility types so it only allows an optional subset of `name`, `email`, `age`, and `bio` (never `id`).",
            "Implement `updateProfile` to merge `updates` into `profile` and return the merged result.",
            "Ensure the return type is still a full `UserProfile` (no fields become optional in the output)."
        ],
        "reference_solution_code": "interface UserProfile {\n  id: string;\n  name: string;\n  email: string;\n  age: number;\n  bio: string;\n}\n\nfunction updateProfile(\n  profile: UserProfile,\n  updates: Partial<Pick<UserProfile, 'name' | 'email' | 'age' | 'bio'>>\n): UserProfile {\n  return { ...profile, ...updates };\n}",
        "check_points": [
            "Uses `Pick` (or an equivalent explicit union of keys) to exclude `id` from the updatable fields.",
            "Wraps the picked type in `Partial` so any subset (including zero fields) can be passed.",
            "Return type remains the full, non-optional `UserProfile`.",
            "Implementation actually merges via spread rather than mutating the input `profile`."
        ],
        "common_mistakes": [
            "Using `Partial<UserProfile>` directly, which allows `id` to be overwritten.",
            "Mutating `profile` in place instead of returning a new merged object.",
            "Making the return type `Partial<UserProfile>` instead of the full interface.",
            "Manually retyping name/email/age/bio instead of deriving from `UserProfile` with `Pick`."
        ],
        "rubric": [
            ["Correct utility-type composition excluding id", 45],
            ["Correct merge implementation", 35],
            ["Return type integrity", 20]
        ],
    },
    {
        "id": "TS-04",
        "flavor": "async-typing",
        "difficulty": "medium",
        "title": "Retry With Backoff",
        "scenario": "Network calls to a flaky downstream service occasionally fail. You need a generic retry helper that re-runs an async operation up to N times with a delay between attempts, and preserves the original operation's return type end-to-end.",
        "code_reference": "async function retry<T>(\n  fn: () => Promise<T>,\n  attempts: number,\n  delayMs: number\n): Promise<T> {\n  // TODO: implement\n}",
        "tasks": [
            "Implement `retry` so it calls `fn` up to `attempts` times, returning the first successful result.",
            "Wait `delayMs` milliseconds between failed attempts (but not after the final attempt).",
            "If every attempt fails, re-throw the last error captured."
        ],
        "reference_solution_code": "async function retry<T>(\n  fn: () => Promise<T>,\n  attempts: number,\n  delayMs: number\n): Promise<T> {\n  let lastError: unknown;\n  for (let i = 0; i < attempts; i++) {\n    try {\n      return await fn();\n    } catch (err) {\n      lastError = err;\n      if (i < attempts - 1) {\n        await new Promise<void>((resolve) => setTimeout(resolve, delayMs));\n      }\n    }\n  }\n  throw lastError;\n}",
        "check_points": [
            "Function signature preserves the generic `T` all the way to the returned `Promise<T>`.",
            "Caught error is typed as `unknown` (not `any`), consistent with modern strict TS catch typing.",
            "Delay only occurs between attempts, not after the last failed attempt.",
            "Final failure re-throws rather than returning `undefined` or swallowing the error."
        ],
        "common_mistakes": [
            "Typing the caught error as `any` or `Error` without a runtime check.",
            "Adding a delay after the last (final) failed attempt, wasting time needlessly.",
            "Returning `undefined` when all attempts are exhausted instead of throwing.",
            "Forgetting `await` before calling `fn()`, causing unhandled promise rejections."
        ],
        "rubric": [
            ["Correct generic async typing", 35],
            ["Correct retry/delay control flow", 40],
            ["Proper error propagation on exhaustion", 25]
        ],
    },
    {
        "id": "TS-05",
        "flavor": "type-guards",
        "difficulty": "medium",
        "title": "Payment Method Narrowing",
        "scenario": "A checkout page accepts three payment method shapes, each with different fields. You need to safely narrow the union to display a masked summary string without ever accessing a field that doesn't exist on the current variant.",
        "code_reference": "type PaymentMethod =\n  | { type: 'credit_card'; cardNumber: string; cvv: string }\n  | { type: 'paypal'; email: string }\n  | { type: 'bank_transfer'; accountNumber: string; routingNumber: string };\n\nfunction maskPaymentInfo(method: PaymentMethod): string {\n  // TODO: implement, showing only the last 4 digits for card/account numbers\n}",
        "tasks": [
            "Write a user-defined type guard `isCreditCard(method: PaymentMethod)` using an `is` predicate.",
            "Use the guard (or discriminant narrowing) inside `maskPaymentInfo` to branch on all three variants.",
            "For `credit_card`, return a string showing only the last 4 digits of `cardNumber`; similarly mask `accountNumber` for `bank_transfer`."
        ],
        "reference_solution_code": "type PaymentMethod =\n  | { type: 'credit_card'; cardNumber: string; cvv: string }\n  | { type: 'paypal'; email: string }\n  | { type: 'bank_transfer'; accountNumber: string; routingNumber: string };\n\nfunction isCreditCard(\n  method: PaymentMethod\n): method is { type: 'credit_card'; cardNumber: string; cvv: string } {\n  return method.type === 'credit_card';\n}\n\nfunction maskPaymentInfo(method: PaymentMethod): string {\n  if (isCreditCard(method)) {\n    return `Card ending in ${method.cardNumber.slice(-4)}`;\n  }\n  if (method.type === 'paypal') {\n    return `PayPal: ${method.email}`;\n  }\n  return `Bank account ending in ${method.accountNumber.slice(-4)}`;\n}",
        "check_points": [
            "`isCreditCard` is written as a proper `method is {...}` type predicate function.",
            "Fields are accessed only after narrowing (no unchecked access to `cardNumber` on the raw union).",
            "All three payment method variants are handled distinctly.",
            "Masking logic correctly slices the last 4 characters."
        ],
        "common_mistakes": [
            "Accessing `method.cardNumber` before narrowing, causing a compile error.",
            "Writing `isCreditCard` as a plain boolean-returning function without the `is` predicate, losing narrowing in callers.",
            "Using `as` casts to force the type instead of proper narrowing.",
            "Missing the `bank_transfer` branch and falling through incorrectly."
        ],
        "rubric": [
            ["Correct type predicate usage", 35],
            ["Correct narrowing for all variants", 40],
            ["Correct masking logic", 25]
        ],
    },
    {
        "id": "TS-06",
        "flavor": "builder-pattern",
        "difficulty": "medium",
        "title": "Fluent Query Builder",
        "scenario": "You're building a tiny internal query-builder library so engineers can write `new QueryBuilder('users').where(\"age > 18\").limit(10).build()` instead of hand-writing SQL strings. Method chaining must keep working through subclasses without hardcoding the return type.",
        "code_reference": "interface QueryState {\n  table: string;\n  filters: string[];\n  limitValue?: number;\n}\n\nclass QueryBuilder {\n  private state: QueryState;\n\n  constructor(table: string) {\n    this.state = { table, filters: [] };\n  }\n\n  where(condition: string): this {\n    // TODO: implement\n  }\n\n  limit(n: number): this {\n    // TODO: implement\n  }\n\n  build(): string {\n    // TODO: implement\n  }\n}",
        "tasks": [
            "Implement `where` to push a condition and return `this` for chaining.",
            "Implement `limit` to set the limit value and return `this`.",
            "Implement `build` to assemble a SQL-like string: `SELECT * FROM <table>` plus an optional `WHERE ... AND ...` clause and an optional `LIMIT <n>` clause."
        ],
        "reference_solution_code": "interface QueryState {\n  table: string;\n  filters: string[];\n  limitValue?: number;\n}\n\nclass QueryBuilder {\n  private state: QueryState;\n\n  constructor(table: string) {\n    this.state = { table, filters: [] };\n  }\n\n  where(condition: string): this {\n    this.state.filters.push(condition);\n    return this;\n  }\n\n  limit(n: number): this {\n    this.state.limitValue = n;\n    return this;\n  }\n\n  build(): string {\n    let query = `SELECT * FROM ${this.state.table}`;\n    if (this.state.filters.length > 0) {\n      query += ` WHERE ${this.state.filters.join(' AND ')}`;\n    }\n    if (this.state.limitValue !== undefined) {\n      query += ` LIMIT ${this.state.limitValue}`;\n    }\n    return query;\n  }\n}",
        "check_points": [
            "`where` and `limit` are typed to return `this` (polymorphic self-type), not the literal class name.",
            "Internal mutable state is kept private and not exposed directly.",
            "`build` correctly joins multiple filters with `AND`.",
            "`build` omits the `WHERE`/`LIMIT` clauses entirely when not set, rather than emitting empty clauses."
        ],
        "common_mistakes": [
            "Returning `QueryBuilder` instead of `this`, which breaks chaining correctness in subclasses.",
            "Making `state` public, breaking encapsulation.",
            "Emitting `WHERE ` with a trailing empty clause when no filters were added.",
            "Using `0` as a falsy check for `limitValue` instead of `!== undefined`, causing `limit(0)` to be silently dropped."
        ],
        "rubric": [
            ["Correct chainable typing (this)", 35],
            ["Correct state accumulation", 30],
            ["Correct build() string assembly", 35]
        ],
    },
    {
        "id": "TS-07",
        "flavor": "typed-events",
        "difficulty": "medium",
        "title": "Strongly Typed Event Emitter",
        "scenario": "Your app currently uses Node's untyped `EventEmitter`, and it keeps causing bugs where a listener expects the wrong payload shape. You want an emitter where the event name determines the payload type at compile time, for a fixed set of app events (`login`, `logout`, `error`).",
        "code_reference": "interface EventMap {\n  login: { userId: string };\n  logout: { userId: string };\n  error: { message: string; code: number };\n}\n\nclass TypedEmitter<T extends object> {\n  private listeners: { [K in keyof T]?: Array<(payload: T[K]) => void> } = {};\n\n  on<K extends keyof T>(event: K, handler: (payload: T[K]) => void): void {\n    // TODO: implement\n  }\n\n  emit<K extends keyof T>(event: K, payload: T[K]): void {\n    // TODO: implement\n  }\n}",
        "tasks": [
            "Implement `on` to register a handler for the given event, lazily initializing the listener array.",
            "Implement `emit` to call all registered handlers for that event with the payload.",
            "Verify (by writing an example usage) that calling `emitter.on('login', handler)` types `handler`'s parameter as `{ userId: string }` automatically."
        ],
        "reference_solution_code": "interface EventMap {\n  login: { userId: string };\n  logout: { userId: string };\n  error: { message: string; code: number };\n}\n\nclass TypedEmitter<T extends object> {\n  private listeners: { [K in keyof T]?: Array<(payload: T[K]) => void> } = {};\n\n  on<K extends keyof T>(event: K, handler: (payload: T[K]) => void): void {\n    if (!this.listeners[event]) {\n      this.listeners[event] = [];\n    }\n    this.listeners[event]!.push(handler);\n  }\n\n  emit<K extends keyof T>(event: K, payload: T[K]): void {\n    this.listeners[event]?.forEach((handler) => handler(payload));\n  }\n}\n\nconst emitter = new TypedEmitter<EventMap>();\nemitter.on('login', (payload) => {\n  console.log(payload.userId);\n});\nemitter.emit('login', { userId: 'u1' });",
        "check_points": [
            "`on` and `emit` are generic over `K extends keyof T`, tying the event name to its payload type.",
            "The listeners map is typed with a mapped type keyed by `T`, not `Record<string, Function[]>`.",
            "Example usage shows the handler parameter is inferred correctly without manual annotation.",
            "`emit` safely handles the case where no listeners are registered for an event."
        ],
        "common_mistakes": [
            "Typing `handler` as `(payload: any) => void`, losing all payload safety.",
            "Using a plain `string` for the event name parameter instead of `K extends keyof T`.",
            "Forgetting the non-null assertion or initialization check before pushing into `listeners[event]`.",
            "Not handling the case where `listeners[event]` is undefined in `emit`, causing a runtime error."
        ],
        "rubric": [
            ["Correct generic event/payload coupling", 45],
            ["Correct on/emit implementation", 35],
            ["Working example demonstrating inference", 20]
        ],
    },
    {
        "id": "TS-08",
        "flavor": "typed-collections",
        "difficulty": "medium",
        "title": "Generic Stack",
        "scenario": "You're implementing an 'undo' feature for a text editor. It needs a simple, type-safe stack of editor snapshots (or any other type callers choose), supporting push/pop/peek and reporting whether it's empty.",
        "code_reference": "class Stack<T> {\n  private items: T[] = [];\n\n  push(item: T): void {\n    // TODO: implement\n  }\n\n  pop(): T | undefined {\n    // TODO: implement\n  }\n\n  peek(): T | undefined {\n    // TODO: implement\n  }\n}",
        "tasks": [
            "Implement `push`, `pop`, and `peek`.",
            "Add a read-only `size` accessor (getter) returning the current number of items.",
            "Add an `isEmpty(): boolean` method."
        ],
        "reference_solution_code": "class Stack<T> {\n  private items: T[] = [];\n\n  push(item: T): void {\n    this.items.push(item);\n  }\n\n  pop(): T | undefined {\n    return this.items.pop();\n  }\n\n  peek(): T | undefined {\n    return this.items[this.items.length - 1];\n  }\n\n  get size(): number {\n    return this.items.length;\n  }\n\n  isEmpty(): boolean {\n    return this.items.length === 0;\n  }\n}",
        "check_points": [
            "`pop` and `peek` are typed to return `T | undefined`, correctly reflecting the empty-stack case under strict null checks.",
            "Internal array is private and generic over `T`.",
            "`size` is implemented as a getter (property access, not a method call) or clearly documented as such.",
            "`isEmpty` correctly reflects the internal array length."
        ],
        "common_mistakes": [
            "Typing `pop`/`peek` as returning `T` (non-optional), which is unsound when the stack is empty.",
            "Using `any[]` instead of `T[]` for internal storage.",
            "Implementing `size` as a regular method but calling it like a property (or vice versa) inconsistently.",
            "Mutating `items` directly from outside the class due to a public field."
        ],
        "rubric": [
            ["Correct generic typing and encapsulation", 40],
            ["Correct push/pop/peek behavior", 40],
            ["size/isEmpty correctness", 20]
        ],
    },
    {
        "id": "TS-09",
        "flavor": "function-overloads",
        "difficulty": "medium",
        "title": "Typed Config Parser",
        "scenario": "Your app reads configuration values from environment variables, which always arrive as raw strings. You want a single `parseConfigValue` function whose return type automatically matches the requested target type (`number`, `boolean`, or `string`), so callers don't need manual casts.",
        "code_reference": "// TODO: add overload signatures so the return type depends on `type`\nfunction parseConfigValue(value: string, type: 'number' | 'boolean' | 'string'): number | boolean | string {\n  // TODO: implement\n}",
        "tasks": [
            "Add three overload signatures: one each for `type: 'number'` (returns `number`), `type: 'boolean'` (returns `boolean`), and `type: 'string'` (returns `string`).",
            "Implement the single implementation signature that satisfies all three overloads.",
            "Ensure `parseConfigValue('true', 'boolean')` is inferred as `boolean` at the call site (not `number | boolean | string`)."
        ],
        "reference_solution_code": "function parseConfigValue(value: string, type: 'number'): number;\nfunction parseConfigValue(value: string, type: 'boolean'): boolean;\nfunction parseConfigValue(value: string, type: 'string'): string;\nfunction parseConfigValue(\n  value: string,\n  type: 'number' | 'boolean' | 'string'\n): number | boolean | string {\n  switch (type) {\n    case 'number':\n      return Number(value);\n    case 'boolean':\n      return value === 'true';\n    case 'string':\n      return value;\n  }\n}\n\nconst port = parseConfigValue('8080', 'number');\nconst enabled = parseConfigValue('true', 'boolean');",
        "check_points": [
            "Three distinct overload signatures are declared above the implementation signature.",
            "The implementation signature's parameter/return types are a superset compatible with all overloads.",
            "Example call-site variables show narrowed return types (number, boolean) rather than the union.",
            "Switch/implementation body actually returns correctly-typed values for each branch."
        ],
        "common_mistakes": [
            "Only writing the union-typed implementation signature without any overloads, forcing callers to cast the result.",
            "Declaring overloads but with a mismatched or incompatible implementation signature that TS rejects.",
            "Returning `value` (string) for the `number` case without converting via `Number()`.",
            "Comparing `value === true` instead of `value === 'true'` for the boolean branch (type error since value is a string)."
        ],
        "rubric": [
            ["Correct overload declarations", 45],
            ["Correct implementation signature and body", 35],
            ["Demonstrated correct inference at call sites", 20]
        ],
    },
    {
        "id": "TS-10",
        "flavor": "mapped-types",
        "difficulty": "medium",
        "title": "Deep Readonly Settings",
        "scenario": "Application settings are loaded once at startup and must never be mutated afterward, including nested objects like `notifications`. TypeScript's built-in `Readonly<T>` only protects the top level. You need a `DeepReadonly<T>` mapped type that recursively locks nested objects too.",
        "code_reference": "interface AppSettings {\n  theme: string;\n  notifications: {\n    email: boolean;\n    sms: boolean;\n  };\n}\n\ntype DeepReadonly<T> = /* TODO: define recursively using a mapped type */;\n\nfunction freezeSettings(settings: AppSettings): DeepReadonly<AppSettings> {\n  // TODO: implement\n}",
        "tasks": [
            "Define `DeepReadonly<T>` as a mapped type that makes every property `readonly`, recursing into properties that are themselves objects.",
            "Implement `freezeSettings` to return the settings typed as `DeepReadonly<AppSettings>`.",
            "Write a short comment or example showing that `result.notifications.email = false` would now be a compile error."
        ],
        "reference_solution_code": "interface AppSettings {\n  theme: string;\n  notifications: {\n    email: boolean;\n    sms: boolean;\n  };\n}\n\ntype DeepReadonly<T> = {\n  readonly [K in keyof T]: T[K] extends object ? DeepReadonly<T[K]> : T[K];\n};\n\nfunction freezeSettings(settings: AppSettings): DeepReadonly<AppSettings> {\n  return settings as DeepReadonly<AppSettings>;\n}\n\n// const frozen = freezeSettings({ theme: 'dark', notifications: { email: true, sms: false } });\n// frozen.notifications.email = false; // would be a compile error: Cannot assign to 'email' because it is a read-only property",
        "check_points": [
            "`DeepReadonly` is a mapped type using `[K in keyof T]` with a `readonly` modifier.",
            "Recursion condition correctly checks `T[K] extends object` (or similar) before recursing, falling back to `T[K]` for primitives.",
            "`freezeSettings` return type is `DeepReadonly<AppSettings>`, not plain `AppSettings`.",
            "Candidate demonstrates understanding that nested mutation is now blocked, not just top-level."
        ],
        "common_mistakes": [
            "Using the built-in `Readonly<T>` directly, which does not recurse into nested objects.",
            "Forgetting the conditional recursion, applying `readonly` but leaving nested object types unchanged (still mutable).",
            "Applying `DeepReadonly` to array types incorrectly without considering array element behavior (acceptable to note as a limitation, but should not crash the type).",
            "Returning `settings` typed as plain `AppSettings` instead of `DeepReadonly<AppSettings>`."
        ],
        "rubric": [
            ["Correct recursive mapped type definition", 50],
            ["Correct application in freezeSettings", 30],
            ["Correct explanation/demonstration of effect", 20]
        ],
    },
    {
        "id": "TS-11",
        "flavor": "conditional-types",
        "difficulty": "medium",
        "title": "Async Return Type Extractor",
        "scenario": "You have many `async` service functions across the codebase and want a reusable utility type that extracts the resolved data type from any of them, similar to how TypeScript's built-in `ReturnType` works but unwrapping the `Promise`.",
        "code_reference": "type AsyncReturnType<T extends (...args: any[]) => Promise<any>> = /* TODO: conditional type using infer */;\n\nasync function fetchUser(id: string): Promise<{ id: string; name: string }> {\n  return { id, name: 'Alice' };\n}\n\ntype User = /* TODO: use AsyncReturnType here */;",
        "tasks": [
            "Define `AsyncReturnType<T>` using a conditional type with `infer` to extract the resolved value type from a function returning a `Promise`.",
            "Use it to derive `User` from `typeof fetchUser` without manually writing out the `{ id, name }` shape.",
            "Write a function `printUser(user: User): void` that uses the derived type to prove it resolved correctly."
        ],
        "reference_solution_code": "type AsyncReturnType<T extends (...args: any[]) => Promise<any>> =\n  T extends (...args: any[]) => Promise<infer R> ? R : never;\n\nasync function fetchUser(id: string): Promise<{ id: string; name: string }> {\n  return { id, name: 'Alice' };\n}\n\ntype User = AsyncReturnType<typeof fetchUser>;\n\nfunction printUser(user: User): void {\n  console.log(user.id, user.name);\n}",
        "check_points": [
            "`AsyncReturnType` uses `infer` inside a conditional type to pull out the Promise's resolved type.",
            "Type parameter is constrained to functions returning a `Promise` (`(...args: any[]) => Promise<any>`).",
            "`User` is derived via `typeof fetchUser` rather than hand-typed, proving the utility works.",
            "`printUser` successfully accesses `.id` and `.name` on the derived type with no casts."
        ],
        "common_mistakes": [
            "Forgetting `infer` and instead writing `T extends Promise<any> ? T : never`, which doesn't unwrap function return types.",
            "Not constraining `T` to a function type, causing the conditional type to be inapplicable to `typeof fetchUser`.",
            "Manually retyping `User` as `{ id: string; name: string }` instead of deriving it, defeating the purpose of the exercise.",
            "Using `ReturnType<typeof fetchUser>` alone (without unwrapping), leaving `User` as `Promise<{...}>`."
        ],
        "rubric": [
            ["Correct conditional type with infer", 50],
            ["Correct derivation via typeof", 30],
            ["Correct usage in printUser", 20]
        ],
    },
    {
        "id": "TS-12",
        "flavor": "state-machine",
        "difficulty": "medium",
        "title": "Order Status Transitions",
        "scenario": "An e-commerce order moves through a strict lifecycle: pending, shipped, delivered, or cancelled — and each state carries different extra data (e.g. `shipped` has a tracking number). You need a `nextState` function that advances an order to its next logical state, fully typed so invalid states are impossible to construct.",
        "code_reference": "type OrderState =\n  | { status: 'pending' }\n  | { status: 'shipped'; trackingNumber: string }\n  | { status: 'delivered'; deliveredAt: Date }\n  | { status: 'cancelled'; reason: string };\n\nfunction nextState(state: OrderState): OrderState {\n  // TODO: implement: pending -> shipped -> delivered; delivered/cancelled stay as-is\n}",
        "tasks": [
            "Implement `nextState` using a `switch` on `state.status`.",
            "`pending` should transition to `shipped` (invent a tracking number), `shipped` should transition to `delivered` (using the current time).",
            "`delivered` and `cancelled` are terminal — return the state unchanged."
        ],
        "reference_solution_code": "type OrderState =\n  | { status: 'pending' }\n  | { status: 'shipped'; trackingNumber: string }\n  | { status: 'delivered'; deliveredAt: Date }\n  | { status: 'cancelled'; reason: string };\n\nfunction nextState(state: OrderState): OrderState {\n  switch (state.status) {\n    case 'pending':\n      return { status: 'shipped', trackingNumber: 'TRK-0001' };\n    case 'shipped':\n      return { status: 'delivered', deliveredAt: new Date() };\n    case 'delivered':\n      return state;\n    case 'cancelled':\n      return state;\n  }\n}",
        "check_points": [
            "Each returned object literal includes exactly the fields required by its target discriminant (no missing or extra fields).",
            "Switch covers all four discriminant values.",
            "Terminal states (`delivered`, `cancelled`) return the original state object rather than constructing a new one.",
            "No use of `as OrderState` casts to bypass literal shape checking."
        ],
        "common_mistakes": [
            "Returning `{ status: 'shipped' }` without the required `trackingNumber` field.",
            "Forgetting to handle `cancelled` as a distinct terminal case (falling through to a default that changes it).",
            "Using string literals like `'Shipped'` (wrong case) that don't match the discriminant exactly.",
            "Casting the return value with `as OrderState` to silence a legitimate missing-field error."
        ],
        "rubric": [
            ["Correct discriminated union transitions", 50],
            ["Correct handling of terminal states", 30],
            ["No unsafe casts / clean typing", 20]
        ],
    },
    {
        "id": "TS-13",
        "flavor": "generic-constraints",
        "difficulty": "medium",
        "title": "Sort Items By Key",
        "scenario": "A product listing page needs to sort arrays of objects (products, users, orders — any shape) by a given property name chosen at the call site, e.g. `sortByKey(products, 'price')`. The property name must be validated against the object's actual keys at compile time.",
        "code_reference": "function sortByKey<T, K extends keyof T>(items: T[], key: K): T[] {\n  // TODO: implement, supporting both number and string field comparisons\n}",
        "tasks": [
            "Constrain the generic so `key` can only be a valid property name of `T` (using `keyof`).",
            "Implement the sort without mutating the original array.",
            "Handle both numeric fields (numeric comparison) and string fields (locale-aware string comparison) correctly."
        ],
        "reference_solution_code": "function sortByKey<T, K extends keyof T>(items: T[], key: K): T[] {\n  return [...items].sort((a, b) => {\n    const aVal = a[key];\n    const bVal = b[key];\n    if (typeof aVal === 'number' && typeof bVal === 'number') {\n      return aVal - bVal;\n    }\n    return String(aVal).localeCompare(String(bVal));\n  });\n}",
        "check_points": [
            "Generic constraint `K extends keyof T` ensures `sortByKey(items, 'nonExistentField')` is a compile error.",
            "Original array is not mutated (uses a copy via spread or `.slice()`).",
            "Numeric fields are compared numerically, not via string coercion (which would sort '10' before '2').",
            "Function works generically across different object shapes without `any`."
        ],
        "common_mistakes": [
            "Using `key: string` instead of `K extends keyof T`, losing compile-time validation of the key name.",
            "Comparing values directly with `<`/`>` operators on a generic-typed value, which TypeScript rejects for non-primitive-constrained generics.",
            "Mutating the input array via `.sort()` directly instead of copying first.",
            "Not handling numeric fields specially, causing incorrect lexicographic sorting of numbers."
        ],
        "rubric": [
            ["Correct keyof generic constraint", 40],
            ["Correct non-mutating sort implementation", 35],
            ["Correct numeric vs string comparison handling", 25]
        ],
    },
    {
        "id": "TS-14",
        "flavor": "index-signatures",
        "difficulty": "medium",
        "title": "HTTP Status Lookup Table",
        "scenario": "You're building a small helper that maps HTTP status codes to human-readable messages for logging. The table should be type-safe (keys are numbers, values are strings) and the lookup function must gracefully handle unknown codes.",
        "code_reference": "type HttpStatusMessages = /* TODO: type this as a lookup from number to string */;\n\nconst statusMessages: HttpStatusMessages = {\n  200: 'OK',\n  404: 'Not Found',\n  500: 'Internal Server Error',\n};\n\nfunction getStatusMessage(messages: HttpStatusMessages, code: number): string {\n  // TODO: implement, returning 'Unknown Status' for missing codes\n}",
        "tasks": [
            "Define `HttpStatusMessages` using `Record<number, string>` (or an equivalent index signature).",
            "Implement `getStatusMessage` to look up the code and fall back to `'Unknown Status'` when not present.",
            "Use the nullish coalescing operator (`??`) rather than a manual `if` check for the fallback."
        ],
        "reference_solution_code": "type HttpStatusMessages = Record<number, string>;\n\nconst statusMessages: HttpStatusMessages = {\n  200: 'OK',\n  404: 'Not Found',\n  500: 'Internal Server Error',\n};\n\nfunction getStatusMessage(messages: HttpStatusMessages, code: number): string {\n  return messages[code] ?? 'Unknown Status';\n}",
        "check_points": [
            "`HttpStatusMessages` correctly types keys as `number` and values as `string`.",
            "`getStatusMessage` returns the fallback string for missing codes rather than `undefined`.",
            "Uses `??` (nullish coalescing) rather than `||`, which would also (incorrectly, though not harmful here) trigger on empty string values.",
            "The sample `statusMessages` object satisfies the declared type without extra casts."
        ],
        "common_mistakes": [
            "Using `Record<string, string>` for numeric codes, forcing awkward string-key access.",
            "Returning `messages[code]` directly, which is `string | undefined` under strict mode and would fail to satisfy a `string` return type.",
            "Using `||` instead of `??`, which is technically fine here but shows a misunderstanding of the two operators.",
            "Not marking the lookup table type reusable (inlining the shape ad-hoc at both declaration sites)."
        ],
        "rubric": [
            ["Correct Record/index-signature typing", 40],
            ["Correct fallback lookup logic", 40],
            ["Type-safe handling of possibly-undefined access", 20]
        ],
    },
    {
        "id": "TS-15",
        "flavor": "async-iterators",
        "difficulty": "medium",
        "title": "Paginated Data Generator",
        "scenario": "An admin dashboard needs to stream through every record of a paginated API (which returns a page of items plus a `nextCursor`) without loading everything into memory at once. You want an async generator that callers can iterate with `for await...of`.",
        "code_reference": "interface Page<T> {\n  items: T[];\n  nextCursor: string | null;\n}\n\nasync function* paginate<T>(\n  fetchPage: (cursor: string | null) => Promise<Page<T>>\n): AsyncGenerator<T, void, unknown> {\n  // TODO: implement, fetching pages until nextCursor is null\n}",
        "tasks": [
            "Implement `paginate` to repeatedly call `fetchPage` starting with a `null` cursor, `yield`-ing each item from each page.",
            "Continue fetching subsequent pages using the returned `nextCursor` until it is `null`.",
            "Ensure the function's declared type correctly reflects that it yields individual items of type `T`, not whole pages."
        ],
        "reference_solution_code": "interface Page<T> {\n  items: T[];\n  nextCursor: string | null;\n}\n\nasync function* paginate<T>(\n  fetchPage: (cursor: string | null) => Promise<Page<T>>\n): AsyncGenerator<T, void, unknown> {\n  let cursor: string | null = null;\n  do {\n    const page = await fetchPage(cursor);\n    for (const item of page.items) {\n      yield item;\n    }\n    cursor = page.nextCursor;\n  } while (cursor !== null);\n}",
        "check_points": [
            "Function is declared `async function*` and typed `AsyncGenerator<T, void, unknown>`.",
            "Loop correctly re-fetches with the updated cursor and terminates when `nextCursor` is `null`.",
            "`yield`s individual items (`T`), not entire `Page<T>` objects.",
            "Handles the first call correctly by starting with a `null` cursor."
        ],
        "common_mistakes": [
            "Declaring the return type as `Promise<T[]>` instead of an async generator, defeating the purpose of streaming.",
            "Using a `while (true)` loop without a proper termination check on `nextCursor`, risking an infinite loop.",
            "Yielding the whole `page` object instead of iterating `page.items`.",
            "Forgetting `await` on `fetchPage(cursor)`, causing a type error (page would be a Promise, not a Page)."
        ],
        "rubric": [
            ["Correct async generator typing", 40],
            ["Correct pagination loop and termination", 40],
            ["Correct per-item yielding", 20]
        ],
    },
    {
        "id": "TS-16",
        "flavor": "reducer-pattern",
        "difficulty": "medium",
        "title": "Typed Counter Reducer",
        "scenario": "You're wiring up Redux-style state management for a counter widget that supports incrementing, decrementing by a variable amount, and resetting. The reducer must be fully typed so dispatching an invalid action shape is a compile error.",
        "code_reference": "interface CounterState {\n  count: number;\n}\n\ntype CounterAction =\n  | { type: 'increment'; by: number }\n  | { type: 'decrement'; by: number }\n  | { type: 'reset' };\n\nfunction counterReducer(state: CounterState, action: CounterAction): CounterState {\n  // TODO: implement\n}",
        "tasks": [
            "Implement `counterReducer` using a `switch` over `action.type`.",
            "`increment`/`decrement` should adjust `count` by `action.by`; `reset` should set `count` back to 0.",
            "Return a new state object each time rather than mutating the input `state`."
        ],
        "reference_solution_code": "interface CounterState {\n  count: number;\n}\n\ntype CounterAction =\n  | { type: 'increment'; by: number }\n  | { type: 'decrement'; by: number }\n  | { type: 'reset' };\n\nfunction counterReducer(state: CounterState, action: CounterAction): CounterState {\n  switch (action.type) {\n    case 'increment':\n      return { count: state.count + action.by };\n    case 'decrement':\n      return { count: state.count - action.by };\n    case 'reset':\n      return { count: 0 };\n  }\n}",
        "check_points": [
            "`action.by` is accessed only within the `increment`/`decrement` branches where it's guaranteed to exist by the discriminated union.",
            "`reset` branch does not attempt to read a `by` field (which doesn't exist on that variant).",
            "Reducer returns a brand-new state object rather than mutating `state.count` directly.",
            "Switch is exhaustive across all three action types."
        ],
        "common_mistakes": [
            "Mutating `state.count += action.by; return state;` instead of returning a new object, breaking immutability expectations.",
            "Trying to access `action.by` on the `reset` branch (compile error) or ignoring the discriminated union and using a generic `action.by` with optional chaining as a workaround.",
            "Missing a `case` for one of the three action types, causing an implicit-any-like fallthrough (should be a TS error if strict + noImplicitReturns, but is a design flaw regardless).",
            "Not typing `CounterAction` as a discriminated union at all, using a single interface with optional fields."
        ],
        "rubric": [
            ["Correct discriminated action typing/usage", 40],
            ["Correct reducer logic per action", 40],
            ["Immutability of returned state", 20]
        ],
    },
    {
        "id": "TS-17",
        "flavor": "class-design",
        "difficulty": "medium",
        "title": "Service Registry Singleton",
        "scenario": "Your app has several cross-cutting services (logger, analytics client, feature-flag client) that should be instantiated once and looked up by name anywhere in the codebase, with type-safe registration and resolution.",
        "code_reference": "class ServiceRegistry {\n  private static instance: ServiceRegistry;\n  private services = new Map<string, unknown>();\n\n  private constructor() {}\n\n  static getInstance(): ServiceRegistry {\n    // TODO: implement singleton access\n  }\n\n  register<T>(key: string, service: T): void {\n    // TODO: implement\n  }\n\n  resolve<T>(key: string): T {\n    // TODO: implement, throwing if not found\n  }\n}",
        "tasks": [
            "Implement `getInstance` so the class is a true singleton (only one instance ever created).",
            "Implement `register` to store a service of any type under a string key.",
            "Implement `resolve<T>` to retrieve and cast the stored service back to `T`, throwing a descriptive error if the key is missing."
        ],
        "reference_solution_code": "class ServiceRegistry {\n  private static instance: ServiceRegistry;\n  private services = new Map<string, unknown>();\n\n  private constructor() {}\n\n  static getInstance(): ServiceRegistry {\n    if (!ServiceRegistry.instance) {\n      ServiceRegistry.instance = new ServiceRegistry();\n    }\n    return ServiceRegistry.instance;\n  }\n\n  register<T>(key: string, service: T): void {\n    this.services.set(key, service);\n  }\n\n  resolve<T>(key: string): T {\n    const service = this.services.get(key);\n    if (service === undefined) {\n      throw new Error(`Service not found: ${key}`);\n    }\n    return service as T;\n  }\n}",
        "check_points": [
            "Constructor is `private`, preventing `new ServiceRegistry()` from outside the class.",
            "`getInstance` lazily creates and caches exactly one instance.",
            "Internal map is typed `Map<string, unknown>` rather than `Map<string, any>`, requiring an explicit cast on retrieval.",
            "`resolve` throws (rather than returning `undefined as T`) when the key is missing."
        ],
        "common_mistakes": [
            "Making the constructor public, defeating the singleton guarantee.",
            "Storing services in a `Map<string, any>`, silently losing type safety on resolve.",
            "Returning `undefined` cast as `T` when a key is missing instead of throwing, causing confusing downstream null errors.",
            "Re-creating a new instance on every call to `getInstance` instead of caching it."
        ],
        "rubric": [
            ["Correct singleton enforcement", 35],
            ["Correct generic register/resolve typing", 40],
            ["Proper error handling on missing key", 25]
        ],
    },
    {
        "id": "TS-18",
        "flavor": "unknown-narrowing",
        "difficulty": "medium",
        "title": "Safe JSON Product Parser",
        "scenario": "Your service receives product data as raw JSON strings from an untrusted external partner feed. Before using the data, you must validate its shape at runtime — `JSON.parse` alone only gives you `any`, which is unsafe to trust blindly.",
        "code_reference": "interface Product {\n  id: string;\n  name: string;\n  price: number;\n}\n\nfunction isProduct(value: unknown): value is Product {\n  // TODO: implement runtime shape validation\n}\n\nfunction parseProduct(json: string): Product | null {\n  // TODO: implement using JSON.parse + isProduct, returning null on any failure\n}",
        "tasks": [
            "Implement `isProduct` as a type guard that checks, at runtime, that `value` has `id` (string), `name` (string), and `price` (number).",
            "Implement `parseProduct` to safely `JSON.parse` the input, catching parse errors and returning `null` on failure.",
            "Use `isProduct` to validate the parsed result before returning it, returning `null` if validation fails."
        ],
        "reference_solution_code": "interface Product {\n  id: string;\n  name: string;\n  price: number;\n}\n\nfunction isProduct(value: unknown): value is Product {\n  if (typeof value !== 'object' || value === null) return false;\n  const candidate = value as Record<string, unknown>;\n  return (\n    typeof candidate.id === 'string' &&\n    typeof candidate.name === 'string' &&\n    typeof candidate.price === 'number'\n  );\n}\n\nfunction parseProduct(json: string): Product | null {\n  let parsed: unknown;\n  try {\n    parsed = JSON.parse(json);\n  } catch {\n    return null;\n  }\n  return isProduct(parsed) ? parsed : null;\n}",
        "check_points": [
            "`JSON.parse`'s result is held in an `unknown`-typed variable, not implicitly `any`.",
            "`isProduct` checks `typeof value !== 'object' || value === null` before accessing properties, avoiding a crash on primitives/null.",
            "Each field is checked with `typeof` against its expected primitive type.",
            "`parseProduct` wraps `JSON.parse` in a try/catch and returns `null` for malformed JSON."
        ],
        "common_mistakes": [
            "Letting `JSON.parse`'s result flow through as implicit `any`, skipping real validation entirely.",
            "Not checking `value === null` before treating it as an object (since `typeof null === 'object'`), causing a runtime crash on property access.",
            "Only checking that fields exist (`'id' in candidate`) without checking their types.",
            "Forgetting to catch `JSON.parse` exceptions, letting malformed JSON throw uncaught."
        ],
        "rubric": [
            ["Correct unknown-based type guard implementation", 45],
            ["Correct handling of parse failures", 30],
            ["No unsafe any/implicit trust of external data", 25]
        ],
    },
    {
        "id": "TS-19",
        "flavor": "optional-chaining",
        "difficulty": "medium",
        "title": "Nested Config Resolver",
        "scenario": "An app's configuration object is loaded from a partially-filled JSON file, so every nested section is optional. You need helper functions that read specific settings and fall back to sensible defaults when any part of the path is missing.",
        "code_reference": "interface AppConfig {\n  api?: {\n    baseUrl?: string;\n    timeout?: number;\n  };\n  featureFlags?: {\n    darkMode?: boolean;\n  };\n}\n\nfunction getBaseUrl(config: AppConfig): string {\n  // TODO: implement, default 'https://api.default.com'\n}\n\nfunction getTimeout(config: AppConfig): number {\n  // TODO: implement, default 5000\n}",
        "tasks": [
            "Implement `getBaseUrl` and `getTimeout` using optional chaining (`?.`) to safely traverse the nested optional structure.",
            "Use nullish coalescing (`??`) to supply the defaults, only falling back on `null`/`undefined` (not on falsy-but-valid values like `0`).",
            "Add a third function `isDarkModeEnabled(config: AppConfig): boolean` defaulting to `false`."
        ],
        "reference_solution_code": "interface AppConfig {\n  api?: {\n    baseUrl?: string;\n    timeout?: number;\n  };\n  featureFlags?: {\n    darkMode?: boolean;\n  };\n}\n\nfunction getBaseUrl(config: AppConfig): string {\n  return config.api?.baseUrl ?? 'https://api.default.com';\n}\n\nfunction getTimeout(config: AppConfig): number {\n  return config.api?.timeout ?? 5000;\n}\n\nfunction isDarkModeEnabled(config: AppConfig): boolean {\n  return config.featureFlags?.darkMode ?? false;\n}",
        "check_points": [
            "Uses `?.` to traverse `api` and `featureFlags`, which are both typed optional.",
            "Uses `??` (not `||`) for defaults, correctly preserving an explicit `timeout: 0` if ever set.",
            "All three functions have concrete, non-optional return types (`string`, `number`, `boolean`).",
            "No non-null assertions (`!`) used to bypass the optionality instead of proper chaining."
        ],
        "common_mistakes": [
            "Using `config.api!.baseUrl` with a non-null assertion instead of `?.`, which would crash at runtime if `api` is actually missing.",
            "Using `||` instead of `??` for the timeout default, which would incorrectly override an explicit `timeout: 0`.",
            "Writing verbose manual `if (config.api && config.api.baseUrl)` chains instead of optional chaining (not wrong, but misses the intended feature).",
            "Forgetting a default and returning `string | undefined` instead of a guaranteed `string`."
        ],
        "rubric": [
            ["Correct optional chaining usage", 40],
            ["Correct nullish coalescing for defaults", 40],
            ["Return types are non-optional as specified", 20]
        ],
    },
    {
        "id": "TS-20",
        "flavor": "recursive-types",
        "difficulty": "medium",
        "title": "Tree Search Utility",
        "scenario": "A file-explorer UI represents folders and files as a nested tree. You need a generic, reusable function that searches any such tree (regardless of what data it holds) for the first node matching a predicate, e.g. finding a file by name.",
        "code_reference": "interface TreeNode<T> {\n  value: T;\n  children: TreeNode<T>[];\n}\n\nfunction findInTree<T>(node: TreeNode<T>, predicate: (value: T) => boolean): TreeNode<T> | null {\n  // TODO: implement depth-first search\n}",
        "tasks": [
            "Implement `findInTree` as a depth-first search: check the current node first, then recurse into children in order.",
            "Return the first matching `TreeNode<T>` found, or `null` if nothing matches anywhere in the tree.",
            "Ensure the function type-checks generically for any `T` (strings, numbers, custom objects) without using `any`."
        ],
        "reference_solution_code": "interface TreeNode<T> {\n  value: T;\n  children: TreeNode<T>[];\n}\n\nfunction findInTree<T>(node: TreeNode<T>, predicate: (value: T) => boolean): TreeNode<T> | null {\n  if (predicate(node.value)) return node;\n  for (const child of node.children) {\n    const found = findInTree(child, predicate);\n    if (found) return found;\n  }\n  return null;\n}",
        "check_points": [
            "`TreeNode<T>` is used recursively (children are `TreeNode<T>[]`, not a different shape).",
            "Search checks the current node's value before descending into children (correct DFS pre-order).",
            "Recursive call's result is properly checked and propagated up (`if (found) return found`), not discarded.",
            "Function returns `null` (not `undefined`) when no match exists anywhere, matching the declared return type."
        ],
        "common_mistakes": [
            "Forgetting to return the recursive call's result, causing the search to always fall through to `null` even on a match.",
            "Checking children before checking the current node, producing incorrect traversal order.",
            "Using `any` for `T` or for the tree structure instead of keeping it fully generic.",
            "Returning `undefined` in some branch while the signature promises `TreeNode<T> | null`."
        ],
        "rubric": [
            ["Correct recursive generic type usage", 35],
            ["Correct DFS traversal order", 35],
            ["Correct propagation of found results and null", 30]
        ],
    },
    {
        "id": "TS-21",
        "flavor": "template-literal-types",
        "difficulty": "medium",
        "title": "Typed API Route Builder",
        "scenario": "Your frontend calls a REST API with routes shaped like `/v1/users` or `/v2/orders`. You want the compiler to reject any route string that doesn't match this exact versioned-resource pattern, catching typos like `/v1/usres` before runtime.",
        "code_reference": "type ApiVersion = 'v1' | 'v2';\ntype Resource = 'users' | 'orders' | 'products';\n\ntype ApiRoute = /* TODO: template literal type combining ApiVersion and Resource */;\n\nfunction buildRoute(version: ApiVersion, resource: Resource): ApiRoute {\n  // TODO: implement\n}",
        "tasks": [
            "Define `ApiRoute` as a template literal type of the form `/${ApiVersion}/${Resource}`.",
            "Implement `buildRoute` to construct and return a valid `ApiRoute` from its parts.",
            "Write a `callApi(route: ApiRoute): string` function and show that passing a malformed literal string would be rejected (as a comment)."
        ],
        "reference_solution_code": "type ApiVersion = 'v1' | 'v2';\ntype Resource = 'users' | 'orders' | 'products';\n\ntype ApiRoute = `/${ApiVersion}/${Resource}`;\n\nfunction buildRoute(version: ApiVersion, resource: Resource): ApiRoute {\n  return `/${version}/${resource}`;\n}\n\nfunction callApi(route: ApiRoute): string {\n  return `Calling ${route}`;\n}\n\n// callApi('/v1/usres'); // would be a compile error: not assignable to ApiRoute",
        "check_points": [
            "`ApiRoute` is defined as a template literal type referencing the `ApiVersion` and `Resource` unions (not a plain `string`).",
            "`buildRoute`'s return type is inferred/declared as `ApiRoute`, and the implementation actually produces a matching string.",
            "`callApi` accepts only `ApiRoute`, not arbitrary strings.",
            "Candidate demonstrates (in a comment or explanation) that an invalid literal would fail to compile."
        ],
        "common_mistakes": [
            "Declaring `ApiRoute` as plain `string`, losing all the compile-time route validation benefit.",
            "Hardcoding the union of all six literal combinations manually instead of using a template literal type.",
            "Making `callApi` accept `string` instead of `ApiRoute`, defeating the purpose.",
            "Building the route with string concatenation whose type doesn't get narrowed back to `ApiRoute` without an explicit type layer (should rely on the template literal type, not a cast)."
        ],
        "rubric": [
            ["Correct template literal type definition", 45],
            ["Correct buildRoute implementation", 30],
            ["Correct restrictive usage in callApi", 25]
        ],
    },
    {
        "id": "TS-22",
        "flavor": "function-composition",
        "difficulty": "medium",
        "title": "Typed Pipe Utility",
        "scenario": "You keep writing chains like `exclaim(toUpperCase(shout(text)))` for text transformations and want a `pipe` helper that composes two functions left-to-right, with the compiler correctly inferring the intermediate and final types.",
        "code_reference": "function pipe<A, B, C>(fn1: (a: A) => B, fn2: (b: B) => C): (a: A) => C {\n  // TODO: implement\n}",
        "tasks": [
            "Implement `pipe` to return a new function that applies `fn1` then `fn2` in sequence.",
            "Demonstrate usage by composing a `toUpperCase: (s: string) => string` and an `exclaim: (s: string) => string` function into a `shout` function.",
            "Explain (briefly, as a comment) why the generic parameters `A`, `B`, `C` are each necessary rather than using a single type parameter."
        ],
        "reference_solution_code": "function pipe<A, B, C>(fn1: (a: A) => B, fn2: (b: B) => C): (a: A) => C {\n  return (a: A) => fn2(fn1(a));\n}\n\nconst toUpperCase = (s: string): string => s.toUpperCase();\nconst exclaim = (s: string): string => `${s}!`;\n\nconst shout = pipe(toUpperCase, exclaim);\n// shout('hello') === 'HELLO!'\n\n// A, B, C are each necessary because fn1 and fn2 can have different input/output\n// types (e.g. pipe(parseInt, isPositive) goes string -> number -> boolean);\n// collapsing them to one type parameter would wrongly force fn1 and fn2 to share types.",
        "check_points": [
            "`pipe` is generic over three independent type parameters representing input, intermediate, and output types.",
            "Returned function correctly threads the input through `fn1` then `fn2` in that order.",
            "Usage example shows correct type inference without explicit type annotations at the call site.",
            "Explanation correctly identifies why a single shared type parameter would be too restrictive."
        ],
        "common_mistakes": [
            "Using a single type parameter `T` for both functions, forcing `fn1` and `fn2` to have matching input/output types unnecessarily.",
            "Applying the functions in the wrong order (`fn1(fn2(a))` instead of `fn2(fn1(a))`).",
            "Typing the parameters as `Function` instead of proper generic function signatures, losing type safety entirely.",
            "Not returning a function at all — eagerly computing a single result instead of a reusable composed function."
        ],
        "rubric": [
            ["Correct 3-parameter generic composition", 45],
            ["Correct execution order", 30],
            ["Clear demonstration + explanation", 25]
        ],
    },
    {
        "id": "TS-23",
        "flavor": "error-handling",
        "difficulty": "medium",
        "title": "Result Type For Division",
        "scenario": "Rather than throwing exceptions for expected failure cases (like division by zero), your team wants to adopt a Rust-style `Result<T, E>` pattern so callers are forced by the type system to handle both success and failure explicitly.",
        "code_reference": "type Result<T, E = string> = /* TODO: discriminated union with an `ok` boolean */;\n\nfunction divide(a: number, b: number): Result<number> {\n  // TODO: implement, returning an error Result instead of throwing on division by zero\n}",
        "tasks": [
            "Define `Result<T, E = string>` as a discriminated union with an `ok: true` variant holding `value: T` and an `ok: false` variant holding `error: E`.",
            "Implement `divide` to return an error Result (not throw) when `b === 0`, and a success Result otherwise.",
            "Write a `handleResult(result: Result<number>): string` function that narrows on `result.ok` to safely access `value` or `error`."
        ],
        "reference_solution_code": "type Result<T, E = string> = { ok: true; value: T } | { ok: false; error: E };\n\nfunction divide(a: number, b: number): Result<number> {\n  if (b === 0) {\n    return { ok: false, error: 'Division by zero' };\n  }\n  return { ok: true, value: a / b };\n}\n\nfunction handleResult(result: Result<number>): string {\n  if (result.ok) {\n    return `Result: ${result.value}`;\n  }\n  return `Error: ${result.error}`;\n}",
        "check_points": [
            "`Result` is a discriminated union keyed on a literal boolean `ok` field, with a default error type parameter.",
            "`divide` never throws for the divide-by-zero case; it returns the `ok: false` variant instead.",
            "`handleResult` narrows on `result.ok` before accessing `value` or `error`, with no unchecked access.",
            "Generic default `E = string` is used correctly (callers don't have to specify it for the common case)."
        ],
        "common_mistakes": [
            "Throwing an exception from `divide` on division by zero instead of returning the error variant, defeating the purpose of the Result pattern.",
            "Accessing `result.value` without first checking `result.ok`, which is a compile error under the discriminated union.",
            "Making `ok` a plain `boolean` type instead of the literal `true`/`false` per variant, which breaks discrimination.",
            "Omitting the default type parameter, forcing verbose `Result<number, string>` everywhere."
        ],
        "rubric": [
            ["Correct Result discriminated union design", 40],
            ["Correct divide implementation without throwing", 35],
            ["Correct narrowing usage in handleResult", 25]
        ],
    },
    {
        "id": "TS-24",
        "flavor": "repository-pattern",
        "difficulty": "medium",
        "title": "In-Memory Entity Repository",
        "scenario": "Multiple domain objects in your app (users, products, orders) all need basic CRUD storage during tests, before a real database is wired up. You want a single generic repository implementation that works for any entity type as long as it has an `id`.",
        "code_reference": "interface Entity {\n  id: string;\n}\n\ninterface Repository<T extends Entity> {\n  findById(id: string): T | undefined;\n  save(entity: T): void;\n  delete(id: string): boolean;\n  findAll(): T[];\n}\n\nclass InMemoryRepository<T extends Entity> implements Repository<T> {\n  private items = new Map<string, T>();\n  // TODO: implement all Repository methods\n}",
        "tasks": [
            "Implement all four `Repository<T>` methods on `InMemoryRepository`.",
            "`save` should upsert using the entity's own `id` as the map key.",
            "`delete` should return `true` if an entity was removed, `false` if the id didn't exist."
        ],
        "reference_solution_code": "interface Entity {\n  id: string;\n}\n\ninterface Repository<T extends Entity> {\n  findById(id: string): T | undefined;\n  save(entity: T): void;\n  delete(id: string): boolean;\n  findAll(): T[];\n}\n\nclass InMemoryRepository<T extends Entity> implements Repository<T> {\n  private items = new Map<string, T>();\n\n  findById(id: string): T | undefined {\n    return this.items.get(id);\n  }\n\n  save(entity: T): void {\n    this.items.set(entity.id, entity);\n  }\n\n  delete(id: string): boolean {\n    return this.items.delete(id);\n  }\n\n  findAll(): T[] {\n    return Array.from(this.items.values());\n  }\n}",
        "check_points": [
            "`T extends Entity` constraint is present on both the interface and the class, guaranteeing an `id` field exists.",
            "`class ... implements Repository<T>` is used, so a missing/mistyped method is caught at compile time.",
            "`save` correctly uses `entity.id` as the map key (upsert semantics), not a separately-generated key.",
            "`delete` leverages `Map.delete`'s existing boolean return rather than reimplementing existence-checking logic."
        ],
        "common_mistakes": [
            "Omitting `implements Repository<T>` on the class, losing the compile-time contract check.",
            "Forgetting the `T extends Entity` constraint, making `entity.id` inaccessible in `save`.",
            "Returning `void` from `delete` instead of a `boolean` indicating success.",
            "Using `any` for the internal map value type instead of `T`."
        ],
        "rubric": [
            ["Correct generic constraint and interface implementation", 40],
            ["Correct CRUD method behavior", 40],
            ["Idiomatic use of Map semantics", 20]
        ],
    },
    {
        "id": "TS-25",
        "flavor": "pub-sub-pattern",
        "difficulty": "medium",
        "title": "Typed Publish-Subscribe Channel",
        "scenario": "Different parts of your app need to react to 'order placed' events without being tightly coupled. You want a reusable `Channel<T>` class (usable for any single event payload type) where subscribers can cleanly unsubscribe later, e.g. when a UI component unmounts.",
        "code_reference": "type Handler<T> = (payload: T) => void;\ntype Unsubscribe = () => void;\n\nclass Channel<T> {\n  private handlers: Set<Handler<T>> = new Set();\n\n  subscribe(handler: Handler<T>): Unsubscribe {\n    // TODO: implement, returning a function that removes this handler\n  }\n\n  publish(payload: T): void {\n    // TODO: implement\n  }\n}",
        "tasks": [
            "Implement `subscribe` to register the handler and return an `Unsubscribe` function that removes it from the set.",
            "Implement `publish` to invoke every currently-registered handler with the payload.",
            "Demonstrate usage with a `Channel<{ orderId: string; total: number }>` and show calling the returned unsubscribe function."
        ],
        "reference_solution_code": "type Handler<T> = (payload: T) => void;\ntype Unsubscribe = () => void;\n\nclass Channel<T> {\n  private handlers: Set<Handler<T>> = new Set();\n\n  subscribe(handler: Handler<T>): Unsubscribe {\n    this.handlers.add(handler);\n    return () => this.handlers.delete(handler);\n  }\n\n  publish(payload: T): void {\n    this.handlers.forEach((handler) => handler(payload));\n  }\n}\n\ninterface OrderPlaced {\n  orderId: string;\n  total: number;\n}\n\nconst orderChannel = new Channel<OrderPlaced>();\nconst unsubscribe = orderChannel.subscribe((order) => console.log(order.orderId));\norderChannel.publish({ orderId: 'o1', total: 42 });\nunsubscribe();",
        "check_points": [
            "`Unsubscribe` is its own named function type (`() => void`), improving readability over an inline type.",
            "`subscribe` returns a closure that removes exactly the handler it was given, not all handlers.",
            "`publish` calls every handler currently in the set with the correctly-typed payload.",
            "Usage example shows `unsubscribe()` actually being invoked, proving the returned function works."
        ],
        "common_mistakes": [
            "Using an array with `indexOf`/`splice` in a way that breaks if the same handler function reference is subscribed twice (a `Set` avoids duplicate storage issues cleanly, but candidate should at least handle removal correctly).",
            "Returning `void` from `subscribe` instead of an unsubscribe function, making cleanup impossible.",
            "Typing `handler` as `Function` or `(payload: any) => void` instead of `Handler<T>`.",
            "Forgetting to bind/capture the specific handler in the closure, accidentally removing a different or all handlers."
        ],
        "rubric": [
            ["Correct generic channel typing", 35],
            ["Correct subscribe/unsubscribe closure behavior", 40],
            ["Correct publish + working demonstration", 25]
        ],
    },
    {
        "id": "TS-26",
        "flavor": "array-utilities",
        "difficulty": "medium",
        "title": "Typed Group By Utility",
        "scenario": "You constantly need to group arrays of objects by some derived key — grouping orders by status, users by role, etc. You want one reusable, fully generic `groupBy` utility instead of writing this loop over and over.",
        "code_reference": "function groupBy<T, K extends string | number>(items: T[], keyFn: (item: T) => K): Record<K, T[]> {\n  // TODO: implement\n}",
        "tasks": [
            "Implement `groupBy` to bucket items into a `Record<K, T[]>` using the result of `keyFn(item)` as the bucket key.",
            "Initialize each bucket array lazily the first time a given key is encountered.",
            "Demonstrate usage grouping a small array of `{ status: string }` objects by `status`."
        ],
        "reference_solution_code": "function groupBy<T, K extends string | number>(items: T[], keyFn: (item: T) => K): Record<K, T[]> {\n  const result = {} as Record<K, T[]>;\n  for (const item of items) {\n    const key = keyFn(item);\n    if (!result[key]) {\n      result[key] = [];\n    }\n    result[key].push(item);\n  }\n  return result;\n}\n\ninterface Order {\n  id: string;\n  status: 'pending' | 'shipped' | 'delivered';\n}\n\nconst orders: Order[] = [\n  { id: '1', status: 'pending' },\n  { id: '2', status: 'shipped' },\n  { id: '3', status: 'pending' },\n];\n\nconst grouped = groupBy(orders, (order) => order.status);",
        "check_points": [
            "`K` is constrained to `string | number` so it can be used as a `Record` key.",
            "Each bucket is lazily initialized before pushing (`if (!result[key])`), avoiding a crash on first insert.",
            "`keyFn` is a generic parameter, not hardcoded to a specific field name, so the utility is reusable across shapes.",
            "Demonstration shows correct grouping behavior for at least two distinct keys."
        ],
        "common_mistakes": [
            "Using `Record<string, T[]>` regardless of `K`, losing the more precise key typing when `K` is a literal union.",
            "Forgetting to initialize the array before pushing, causing a runtime error on the first item for each new key.",
            "Hardcoding the grouping field (e.g. always `item.status`) instead of accepting a generic `keyFn`.",
            "Mutating a shared external object across calls instead of creating a fresh `result` each invocation."
        ],
        "rubric": [
            ["Correct generic key constraint and Record typing", 40],
            ["Correct lazy bucket initialization", 35],
            ["Working, reusable demonstration", 25]
        ],
    },
    {
        "id": "TS-27",
        "flavor": "generic-interfaces",
        "difficulty": "medium",
        "title": "Typed HTTP Client",
        "scenario": "You're defining the contract for an HTTP client abstraction used across the app, so that different implementations (real fetch-based, mocked for tests) can be swapped freely while every call site still gets full type safety on request and response bodies.",
        "code_reference": "interface HttpClient {\n  get<T>(url: string): Promise<T>;\n  post<T, B = unknown>(url: string, body: B): Promise<T>;\n}\n\ninterface CreateOrderRequest {\n  productId: string;\n  quantity: number;\n}\n\ninterface OrderResponse {\n  orderId: string;\n  status: string;\n}\n\nasync function createOrder(client: HttpClient, request: CreateOrderRequest): Promise<OrderResponse> {\n  // TODO: implement using client.post with explicit type arguments\n}",
        "tasks": [
            "Implement `createOrder` using `client.post` with explicit generic type arguments for both the response and body types.",
            "Ensure the function's own return type (`Promise<OrderResponse>`) lines up with the type argument passed to `post`.",
            "Explain briefly why `B = unknown` (rather than `any`) is a safer default for the body type parameter."
        ],
        "reference_solution_code": "interface HttpClient {\n  get<T>(url: string): Promise<T>;\n  post<T, B = unknown>(url: string, body: B): Promise<T>;\n}\n\ninterface CreateOrderRequest {\n  productId: string;\n  quantity: number;\n}\n\ninterface OrderResponse {\n  orderId: string;\n  status: string;\n}\n\nasync function createOrder(client: HttpClient, request: CreateOrderRequest): Promise<OrderResponse> {\n  return client.post<OrderResponse, CreateOrderRequest>('/orders', request);\n}\n\n// B defaults to `unknown` rather than `any` so that callers who omit the body\n// type argument still get a type that must be checked/narrowed before use,\n// instead of silently disabling type checking on the request body entirely.",
        "check_points": [
            "`client.post` is called with explicit `<OrderResponse, CreateOrderRequest>` type arguments (or types that TS can correctly infer to the same effect).",
            "`createOrder`'s declared return type matches what `client.post` actually resolves to.",
            "Explanation correctly distinguishes `unknown`'s safety (forces narrowing) from `any`'s lack of checking.",
            "No `any` used anywhere in the implementation."
        ],
        "common_mistakes": [
            "Calling `client.post(url, request)` without type arguments where inference fails to produce `OrderResponse`, resulting in an implicit or unresolved generic.",
            "Using `any` as the default for `B` instead of `unknown`, which silently disables checking for callers.",
            "Returning `client.post(...)` without `await`, which still type-checks (Promise<OrderResponse> matches) but shows a misunderstanding of when await is needed — acceptable to note as a discussion point, not a hard type error here.",
            "Defining a separate ad-hoc response type instead of reusing `OrderResponse`."
        ],
        "rubric": [
            ["Correct generic method invocation with proper type args", 45],
            ["Return type correctness", 30],
            ["Correct unknown vs any reasoning", 25]
        ],
    },
    {
        "id": "TS-28",
        "flavor": "dto-mapping",
        "difficulty": "medium",
        "title": "Public User DTO Transform",
        "scenario": "Your database layer returns full user rows including a hashed password, but API responses must never include that field. You want a type-safe transform function whose return type makes it structurally impossible to leak `passwordHash` to a client.",
        "code_reference": "interface DbUser {\n  id: string;\n  name: string;\n  email: string;\n  passwordHash: string;\n  createdAt: Date;\n}\n\ntype PublicUser = /* TODO: derive from DbUser, excluding passwordHash */;\n\nfunction toPublicUser(user: DbUser): PublicUser {\n  // TODO: implement\n}",
        "tasks": [
            "Define `PublicUser` using a built-in utility type that derives it from `DbUser` while excluding `passwordHash`.",
            "Implement `toPublicUser` to strip `passwordHash` and return the remaining fields.",
            "Do this without manually re-listing every remaining field name in the type definition."
        ],
        "reference_solution_code": "interface DbUser {\n  id: string;\n  name: string;\n  email: string;\n  passwordHash: string;\n  createdAt: Date;\n}\n\ntype PublicUser = Omit<DbUser, 'passwordHash'>;\n\nfunction toPublicUser(user: DbUser): PublicUser {\n  const { passwordHash, ...publicUser } = user;\n  return publicUser;\n}",
        "check_points": [
            "`PublicUser` is derived via `Omit<DbUser, 'passwordHash'>` rather than a manually re-declared interface.",
            "`toPublicUser` actually removes `passwordHash` at runtime (via destructuring or delete), not just at the type level.",
            "Return type of `toPublicUser` is `PublicUser`, not `DbUser`, so callers can't accidentally access `passwordHash`.",
            "No use of `as PublicUser` casts that would bypass actually removing the field at runtime."
        ],
        "common_mistakes": [
            "Manually rewriting `PublicUser` as a fresh interface listing all fields except `passwordHash`, which drifts out of sync if `DbUser` changes.",
            "Returning `user as PublicUser` (a cast) without actually stripping `passwordHash` at runtime, so the field is still present on the object despite the type saying otherwise.",
            "Using `Pick` and manually listing every remaining field instead of `Omit` with just the one excluded field.",
            "Forgetting to destructure `passwordHash` out, causing the unused-variable pattern to be missing (candidate directly returns `user` typed as `PublicUser`, silently keeping the sensitive field in the actual object)."
        ],
        "rubric": [
            ["Correct Omit-based type derivation", 40],
            ["Correct runtime field stripping", 40],
            ["No unsafe casts / DRY definition", 20]
        ],
    },
    {
        "id": "TS-29",
        "flavor": "higher-order-functions",
        "difficulty": "medium",
        "title": "Typed Debounce Function",
        "scenario": "A search-as-you-type input fires an API call on every keystroke, overwhelming the backend. You need a generic `debounce` higher-order function that wraps ANY function (preserving its exact parameter types) and delays invocation until the user pauses typing.",
        "code_reference": "function debounce<Args extends unknown[]>(\n  fn: (...args: Args) => void,\n  waitMs: number\n): (...args: Args) => void {\n  // TODO: implement\n}",
        "tasks": [
            "Implement `debounce` so repeated calls within `waitMs` of each other cancel the pending invocation and reschedule it.",
            "Preserve the wrapped function's exact parameter types via the `Args` generic (no `any[]`).",
            "Demonstrate usage by debouncing a `search(query: string): void` function."
        ],
        "reference_solution_code": "function debounce<Args extends unknown[]>(\n  fn: (...args: Args) => void,\n  waitMs: number\n): (...args: Args) => void {\n  let timeoutId: ReturnType<typeof setTimeout> | undefined;\n  return (...args: Args) => {\n    if (timeoutId !== undefined) {\n      clearTimeout(timeoutId);\n    }\n    timeoutId = setTimeout(() => fn(...args), waitMs);\n  };\n}\n\nfunction search(query: string): void {\n  console.log('searching for', query);\n}\n\nconst debouncedSearch = debounce(search, 300);\ndebouncedSearch('hello');",
        "check_points": [
            "`Args extends unknown[]` (a tuple/array generic with rest parameters) is used to preserve the wrapped function's exact parameter list.",
            "`timeoutId` is typed via `ReturnType<typeof setTimeout>` rather than hardcoding a platform-specific timer type.",
            "Each new call clears any pending timeout before scheduling a new one.",
            "The returned function's parameters match `fn`'s parameters exactly at the call site (shown via the `search` example)."
        ],
        "common_mistakes": [
            "Using `any[]` for the arguments instead of a generic `Args extends unknown[]`, losing parameter type checking at call sites.",
            "Typing `timeoutId` as `number`, which is incorrect/unsafe across Node vs browser timer return types.",
            "Forgetting to clear the previous timeout, causing multiple queued invocations instead of true debouncing.",
            "Not spreading `args` correctly into the delayed call, or capturing stale arguments incorrectly across closures."
        ],
        "rubric": [
            ["Correct generic parameter preservation", 40],
            ["Correct debounce timing/cancellation logic", 40],
            ["Correct portable timer typing", 20]
        ],
    },
    {
        "id": "TS-30",
        "flavor": "chain-pattern",
        "difficulty": "medium",
        "title": "Middleware Pipeline",
        "scenario": "You're building a tiny Express-like middleware system for an internal tool: each middleware receives a shared context object and a `next` callback, and can choose whether to call `next()` to continue the chain. You need this fully typed against the context shape.",
        "code_reference": "type Middleware<T> = (context: T, next: () => void) => void;\n\nclass MiddlewarePipeline<T> {\n  private middlewares: Middleware<T>[] = [];\n\n  use(middleware: Middleware<T>): this {\n    // TODO: implement\n  }\n\n  execute(context: T): void {\n    // TODO: implement, running middlewares in registration order\n  }\n}",
        "tasks": [
            "Implement `use` to register a middleware and return `this` for chaining.",
            "Implement `execute` to run middlewares in the order they were registered, where each middleware controls advancement by calling `next()`.",
            "Ensure that if a middleware never calls `next()`, the chain correctly stops (later middlewares do not run)."
        ],
        "reference_solution_code": "type Middleware<T> = (context: T, next: () => void) => void;\n\nclass MiddlewarePipeline<T> {\n  private middlewares: Middleware<T>[] = [];\n\n  use(middleware: Middleware<T>): this {\n    this.middlewares.push(middleware);\n    return this;\n  }\n\n  execute(context: T): void {\n    let index = 0;\n    const next = (): void => {\n      const middleware = this.middlewares[index];\n      index++;\n      if (middleware) {\n        middleware(context, next);\n      }\n    };\n    next();\n  }\n}",
        "check_points": [
            "`use` returns `this`, enabling fluent chaining of multiple `.use()` calls.",
            "`execute` correctly threads a `next` closure that advances an index and invokes the following middleware.",
            "Chain naturally halts when a middleware omits calling `next()` (no forced continuation).",
            "`context` is passed through unchanged to every middleware, typed as `T` (not `any`) throughout."
        ],
        "common_mistakes": [
            "Iterating middlewares with a plain `for` loop that always calls every middleware regardless of whether `next()` was invoked, breaking the short-circuit contract.",
            "Returning `void` from `use` instead of `this`, breaking fluent chaining.",
            "Losing the shared context type by typing it as `any` or `unknown` instead of `T`.",
            "Off-by-one errors in the index increment causing either an infinite loop or skipping the first/last middleware."
        ],
        "rubric": [
            ["Correct chainable use() typing", 30],
            ["Correct next()-driven execution control flow", 45],
            ["Correct context typing throughout", 25]
        ],
    },
]
