EXERCISES = [
    {
        "id": "RCT-01",
        "flavor": "hooks",
        "difficulty": "medium",
        "title": "Build a useToggle Hook",
        "scenario": "Your team keeps writing the same three lines (a boolean piece of state plus a handler that flips it) in every component that has a show/hide button, an accordion, or a modal. The lead engineer asks you to extract this into a small reusable custom hook so it can be imported anywhere instead of re-implemented.",
        "code_reference": """function useToggle(initialValue?: boolean) {
  // TODO: implement this hook
}

function ToggleDemo() {
  const [isOn, toggle] = useToggle(false);
  return <button onClick={toggle}>{isOn ? "ON" : "OFF"}</button>;
}""",
        "tasks": [
            "Implement useToggle(initialValue) so it returns a tuple [value, toggle] where toggle flips the boolean value.",
            "Make sure the toggle function does not become a new function identity on every render (it should be stable across re-renders).",
            "Give the hook and its return value correct TypeScript types (no implicit any).",
        ],
        "reference_solution_code": """function useToggle(initialValue: boolean = false): [boolean, () => void] {
  const [value, setValue] = useState(initialValue);
  const toggle = useCallback(() => setValue((v) => !v), []);
  return [value, toggle];
}

function ToggleDemo() {
  const [isOn, toggle] = useToggle(false);
  return <button onClick={toggle}>{isOn ? "ON" : "OFF"}</button>;
}""",
        "check_points": [
            "Hook returns a tuple (array) of [boolean, function], not an object, matching the usage in ToggleDemo.",
            "Toggle uses a functional state update (setValue(v => !v)) rather than referencing the outer value directly.",
            "toggle is wrapped in useCallback (or otherwise made referentially stable) so it does not change identity every render.",
            "Default parameter / typing is correct: initialValue is a boolean, default false.",
        ],
        "common_mistakes": [
            "Writing toggle as () => setValue(!value), which relies on a closure over value and can be stale if called multiple times before re-render.",
            "Returning an object instead of a tuple, breaking the array-destructuring call site.",
            "Forgetting useCallback, so every consumer re-renders unnecessarily when passed to memoized children.",
            "Leaving initialValue and the return type implicitly typed as any under strict mode.",
        ],
        "rubric": [
            ["Correct toggle logic and stable identity", 45],
            ["Correct hook signature and tuple return", 30],
            ["TypeScript typing correctness", 25],
        ],
    },
    {
        "id": "RCT-02",
        "flavor": "stale-closure",
        "difficulty": "medium",
        "title": "Fix the Stale Closure Counter",
        "scenario": "A junior developer built a live counter that should tick up once per second, but QA reports it only ever goes from 0 to 1 and then freezes. The code below is what they wrote.",
        "code_reference": """function Counter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setCount(count + 1);
    }, 1000);
    return () => clearInterval(id);
  }, []);

  return <p>{count}</p>;
}""",
        "tasks": [
            "Explain in one or two sentences why the counter stops at 1.",
            "Fix the code so the counter keeps incrementing every second, without adding count to the dependency array (that would re-create the interval every tick).",
        ],
        "reference_solution_code": """function Counter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setCount((c) => c + 1);
    }, 1000);
    return () => clearInterval(id);
  }, []);

  return <p>{count}</p>;
}""",
        "check_points": [
            "Identifies that the interval callback closes over count from the first render (stale closure), so it always sets count to 0 + 1.",
            "Fix uses the functional updater form setCount(c => c + 1) instead of setCount(count + 1).",
            "Dependency array remains empty ([]) so the interval is created exactly once and not re-created every second.",
            "Cleanup (clearInterval) is preserved.",
        ],
        "common_mistakes": [
            "Adding count to the dependency array, which 'fixes' the bug by tearing down and recreating the interval every second (works but defeats the purpose and can cause drift).",
            "Wrapping setCount(count + 1) in useCallback without changing to a functional update — the stale closure bug remains.",
            "Removing the cleanup function, causing multiple intervals to stack up on re-mount.",
        ],
        "rubric": [
            ["Correct root-cause explanation", 30],
            ["Correct fix using functional update", 50],
            ["Cleanup and empty dependency array preserved", 20],
        ],
    },
    {
        "id": "RCT-03",
        "flavor": "forms",
        "difficulty": "medium",
        "title": "Controlled Signup Form Validation",
        "scenario": "Build a small signup form component with an email field and a password field. It should validate as the user types: the email must look like a valid address, and the password must be at least 8 characters. The submit button should be disabled while the form is invalid, and each invalid field should show its own inline error message.",
        "code_reference": """interface FormState {
  email: string;
  password: string;
}

function SignupForm() {
  // TODO: implement controlled state, validation, and submit handling
  return null;
}""",
        "tasks": [
            "Implement SignupForm as a fully controlled component using a single FormState object in useState.",
            "Write a validate(values) function that returns an errors object with optional email/password messages.",
            "Render an inline error message next to each invalid field, and disable the submit button while any errors exist.",
            "Handle form submission by preventing the default page reload.",
        ],
        "reference_solution_code": """interface FormState {
  email: string;
  password: string;
}

interface FormErrors {
  email?: string;
  password?: string;
}

function validate(values: FormState): FormErrors {
  const errors: FormErrors = {};
  if (!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(values.email)) {
    errors.email = "Enter a valid email address";
  }
  if (values.password.length < 8) {
    errors.password = "Password must be at least 8 characters";
  }
  return errors;
}

function SignupForm() {
  const [values, setValues] = useState<FormState>({ email: "", password: "" });
  const errors = validate(values);
  const isValid = Object.keys(errors).length === 0;

  function handleChange(field: keyof FormState) {
    return (e: ChangeEvent<HTMLInputElement>) => {
      setValues((prev) => ({ ...prev, [field]: e.target.value }));
    };
  }

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (isValid) {
      console.log("submitting", values);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={values.email} onChange={handleChange("email")} />
      {errors.email && <span>{errors.email}</span>}
      <input type="password" value={values.password} onChange={handleChange("password")} />
      {errors.password && <span>{errors.password}</span>}
      <button type="submit" disabled={!isValid}>Sign up</button>
    </form>
  );
}""",
        "check_points": [
            "Both inputs use value + onChange (fully controlled), updating state immutably via spread rather than mutation.",
            "validate() correctly flags a malformed email and a password under 8 characters.",
            "Submit button's disabled prop is derived from whether errors is empty.",
            "handleSubmit calls e.preventDefault().",
        ],
        "common_mistakes": [
            "Using defaultValue or leaving inputs uncontrolled, then reading values only on submit.",
            "Mutating the FormState object directly (values.email = ...) instead of creating a new object.",
            "Forgetting e.preventDefault(), causing a full page reload on submit.",
            "Only validating in the submit handler instead of deriving errors from current state on every render, so the disabled state doesn't update as the user types.",
        ],
        "rubric": [
            ["Correct validation logic", 40],
            ["Correct controlled input wiring", 30],
            ["Submit handling and disabled-button logic", 20],
            ["Code quality / typing", 10],
        ],
    },
    {
        "id": "RCT-04",
        "flavor": "list-rendering",
        "difficulty": "medium",
        "title": "Fix Index as Key Bug",
        "scenario": "A todo list lets users check off items and also supports drag-to-reorder (implemented elsewhere, not shown). Testers noticed that after reordering the list, the checkboxes appear checked next to the wrong todo text. The component below is the suspected cause.",
        "code_reference": """function TodoList({ todos }: { todos: { id: string; text: string }[] }) {
  return (
    <ul>
      {todos.map((todo, index) => (
        <li key={index}>
          <input type="checkbox" /> {todo.text}
        </li>
      ))}
    </ul>
  );
}""",
        "tasks": [
            "Explain why using the array index as the key causes checkbox state to appear attached to the wrong item after reordering.",
            "Fix the component so each list item is keyed stably regardless of position.",
        ],
        "reference_solution_code": """function TodoList({ todos }: { todos: { id: string; text: string }[] }) {
  return (
    <ul>
      {todos.map((todo) => (
        <li key={todo.id}>
          <input type="checkbox" /> {todo.text}
        </li>
      ))}
    </ul>
  );
}""",
        "check_points": [
            "Explanation correctly notes that React uses the key to match old and new elements between renders, and an index key means position (not identity) is used to match, so DOM nodes (and their uncontrolled state like checked) get reused for a different todo after reorder.",
            "Fix changes the key to todo.id, a stable unique identifier that travels with the item.",
            "No other unrelated logic is changed.",
        ],
        "common_mistakes": [
            "Believing the bug is in the checkbox itself rather than the key strategy.",
            "'Fixing' it with key={index + todo.text}, which is still position-dependent and does not solve reordering.",
            "Removing the key entirely, which produces a React warning and does not fix the underlying issue.",
        ],
        "rubric": [
            ["Correct explanation of index-key + reorder bug", 45],
            ["Correct fix using stable id key", 45],
            ["No unrelated changes / clean diff", 10],
        ],
    },
    {
        "id": "RCT-05",
        "flavor": "state-management",
        "difficulty": "medium",
        "title": "Shopping Cart Context and Reducer",
        "scenario": "The app has cart-related UI scattered across several unrelated components (product cards, a mini-cart badge, a checkout summary), all of which need to read and update the same cart contents. Rather than passing cart state down through many props, build a CartContext backed by useReducer that any component can consume.",
        "code_reference": """interface CartItem {
  id: string;
  name: string;
  quantity: number;
}

// TODO: define CartAction, cartReducer, CartContext, CartProvider, and useCart""",
        "tasks": [
            "Define a CartAction union type supporting ADD_ITEM (adding one unit, or incrementing quantity if already present) and REMOVE_ITEM.",
            "Write cartReducer(state, action) implementing both actions immutably.",
            "Create CartContext plus a CartProvider component that wraps useReducer and provides { items, dispatch }.",
            "Write a useCart() hook that reads the context and throws a clear error if used outside CartProvider.",
        ],
        "reference_solution_code": """interface CartItem {
  id: string;
  name: string;
  quantity: number;
}

type CartAction =
  | { type: "ADD_ITEM"; item: { id: string; name: string } }
  | { type: "REMOVE_ITEM"; id: string };

function cartReducer(state: CartItem[], action: CartAction): CartItem[] {
  switch (action.type) {
    case "ADD_ITEM": {
      const existing = state.find((i) => i.id === action.item.id);
      if (existing) {
        return state.map((i) =>
          i.id === action.item.id ? { ...i, quantity: i.quantity + 1 } : i
        );
      }
      return [...state, { ...action.item, quantity: 1 }];
    }
    case "REMOVE_ITEM":
      return state.filter((i) => i.id !== action.id);
    default:
      return state;
  }
}

interface CartContextValue {
  items: CartItem[];
  dispatch: Dispatch<CartAction>;
}

const CartContext = createContext<CartContextValue | undefined>(undefined);

function CartProvider({ children }: { children: ReactNode }) {
  const [items, dispatch] = useReducer(cartReducer, []);
  return (
    <CartContext.Provider value={{ items, dispatch }}>
      {children}
    </CartContext.Provider>
  );
}

function useCart(): CartContextValue {
  const ctx = useContext(CartContext);
  if (!ctx) {
    throw new Error("useCart must be used within CartProvider");
  }
  return ctx;
}

function AddToCartButton({ id, name }: { id: string; name: string }) {
  const { dispatch } = useCart();
  return (
    <button onClick={() => dispatch({ type: "ADD_ITEM", item: { id, name } })}>
      Add {name}
    </button>
  );
}""",
        "check_points": [
            "cartReducer never mutates state; it returns new arrays/objects for every case.",
            "ADD_ITEM correctly increments quantity for an existing item instead of adding a duplicate row.",
            "useCart throws when context is undefined, guarding against use outside the provider.",
            "CartProvider supplies both items and dispatch through context value.",
        ],
        "common_mistakes": [
            "Mutating state with state.push(...) or state[i].quantity++ inside the reducer.",
            "Forgetting the 'already in cart' branch, so ADD_ITEM always appends a new duplicate entry.",
            "Returning only items from context (omitting dispatch), forcing consumers to lift dispatch some other way.",
            "Not guarding useCart, so a missing provider silently returns undefined and crashes later with a confusing error.",
        ],
        "rubric": [
            ["Correct, immutable reducer logic", 40],
            ["Correct context/provider wiring", 30],
            ["useCart guard and hook design", 20],
            ["Typing correctness", 10],
        ],
    },
    {
        "id": "RCT-06",
        "flavor": "memoization",
        "difficulty": "medium",
        "title": "Memoize a Filtered Product List",
        "scenario": "A product list screen has an unrelated click counter in the corner (for a feature flag experiment). Every time the counter is clicked, the entire filtered product list visibly flickers and console logs show the memoized child list re-rendering even though the products and query haven't changed.",
        "code_reference": """interface Product {
  id: string;
  name: string;
}

const MemoList = memo(function MemoList({ items }: { items: Product[] }) {
  return (
    <ul>
      {items.map((p) => (
        <li key={p.id}>{p.name}</li>
      ))}
    </ul>
  );
});

function ProductList({ products, query }: { products: Product[]; query: string }) {
  const [count, setCount] = useState(0);

  const filtered = products.filter((p) => p.name.includes(query));

  return (
    <div>
      <button onClick={() => setCount(count + 1)}>Clicks: {count}</button>
      <MemoList items={filtered} />
    </div>
  );
}""",
        "tasks": [
            "Explain why MemoList re-renders on every click even though it is wrapped in memo().",
            "Fix ProductList so the filtered array keeps the same reference across renders unless products or query actually change.",
        ],
        "reference_solution_code": """interface Product {
  id: string;
  name: string;
}

const MemoList = memo(function MemoList({ items }: { items: Product[] }) {
  return (
    <ul>
      {items.map((p) => (
        <li key={p.id}>{p.name}</li>
      ))}
    </ul>
  );
});

function ProductList({ products, query }: { products: Product[]; query: string }) {
  const [count, setCount] = useState(0);

  const filtered = useMemo(
    () => products.filter((p) => p.name.includes(query)),
    [products, query]
  );

  return (
    <div>
      <button onClick={() => setCount(count + 1)}>Clicks: {count}</button>
      <MemoList items={filtered} />
    </div>
  );
}""",
        "check_points": [
            "Explanation correctly identifies that .filter() creates a brand new array every render, so memo's shallow prop comparison always sees a 'changed' items prop.",
            "Fix wraps the filter call in useMemo with dependency array [products, query].",
            "MemoList itself is left unchanged (the fix is in the parent, not by removing memo).",
        ],
        "common_mistakes": [
            "Removing memo() from MemoList instead of fixing the reference-stability problem in the parent.",
            "Adding useMemo but forgetting query or products in the dependency array, causing stale filtered results.",
            "Using useCallback instead of useMemo (useCallback memoizes functions, not the array value here).",
        ],
        "rubric": [
            ["Correct explanation of reference-identity issue", 35],
            ["Correct useMemo fix with right dependencies", 50],
            ["No unnecessary changes to MemoList", 15],
        ],
    },
    {
        "id": "RCT-07",
        "flavor": "lifting-state",
        "difficulty": "medium",
        "title": "Lift State Between Temperature Inputs",
        "scenario": "Design a small temperature calculator with two sibling inputs, Celsius and Fahrenheit. Typing in either input should immediately update the other so they always represent the same temperature. TemperatureInput is a presentational component that has already been written for you; you need to build the parent that lifts the shared state up.",
        "code_reference": """type Scale = "c" | "f";

function TemperatureInput({
  scale,
  temperature,
  onTemperatureChange,
}: {
  scale: Scale;
  temperature: string;
  onTemperatureChange: (value: string) => void;
}) {
  return (
    <fieldset>
      <legend>{scale === "c" ? "Celsius" : "Fahrenheit"}</legend>
      <input value={temperature} onChange={(e) => onTemperatureChange(e.target.value)} />
    </fieldset>
  );
}

// TODO: implement Calculator, which renders two TemperatureInputs kept in sync""",
        "tasks": [
            "Write helper functions toCelsius, toFahrenheit, and tryConvert(temperature, convert) that returns an empty string for invalid numeric input.",
            "Implement Calculator, holding the shared temperature value and which scale was last edited in state at the parent level.",
            "Pass each TemperatureInput its own derived value (converting when it is not the source of truth) and an onTemperatureChange handler that updates the lifted state.",
        ],
        "reference_solution_code": """type Scale = "c" | "f";

function toCelsius(f: number): number {
  return ((f - 32) * 5) / 9;
}

function toFahrenheit(c: number): number {
  return (c * 9) / 5 + 32;
}

function tryConvert(temperature: string, convert: (n: number) => number): string {
  const input = parseFloat(temperature);
  if (Number.isNaN(input)) {
    return "";
  }
  const output = convert(input);
  return output.toFixed(1);
}

function TemperatureInput({
  scale,
  temperature,
  onTemperatureChange,
}: {
  scale: Scale;
  temperature: string;
  onTemperatureChange: (value: string) => void;
}) {
  return (
    <fieldset>
      <legend>{scale === "c" ? "Celsius" : "Fahrenheit"}</legend>
      <input value={temperature} onChange={(e) => onTemperatureChange(e.target.value)} />
    </fieldset>
  );
}

function Calculator() {
  const [temperature, setTemperature] = useState("");
  const [scale, setScale] = useState<Scale>("c");

  const celsius = scale === "f" ? tryConvert(temperature, toCelsius) : temperature;
  const fahrenheit = scale === "c" ? tryConvert(temperature, toFahrenheit) : temperature;

  return (
    <div>
      <TemperatureInput
        scale="c"
        temperature={celsius}
        onTemperatureChange={(value) => {
          setScale("c");
          setTemperature(value);
        }}
      />
      <TemperatureInput
        scale="f"
        temperature={fahrenheit}
        onTemperatureChange={(value) => {
          setScale("f");
          setTemperature(value);
        }}
      />
    </div>
  );
}""",
        "check_points": [
            "State (current temperature string + which scale was last edited) lives in Calculator, not in either TemperatureInput.",
            "The non-source-of-truth input's displayed value is derived via tryConvert on every render rather than stored separately.",
            "tryConvert returns an empty string for non-numeric input instead of throwing or rendering NaN.",
            "Both onTemperatureChange callbacks update both the temperature and which scale is authoritative.",
        ],
        "common_mistakes": [
            "Giving each TemperatureInput its own independent useState, so they immediately fall out of sync.",
            "Forgetting to track which scale was last edited, causing rounding to compound or the wrong field to be treated as source of truth.",
            "Letting NaN leak into the rendered value when the user clears the input or types non-numeric text.",
        ],
        "rubric": [
            ["Correct lifted-state architecture", 45],
            ["Correct conversion / derived-value logic", 35],
            ["Handles invalid input gracefully", 20],
        ],
    },
    {
        "id": "RCT-08",
        "flavor": "conditional-rendering",
        "difficulty": "medium",
        "title": "Fix Conditional Rendering Zero Bug",
        "scenario": "A cart summary widget is supposed to show either the list of items or an 'empty cart' message. Instead, when the cart is empty, users see a stray '0' rendered on the page.",
        "code_reference": """function CartSummary({ items }: { items: string[] }) {
  return (
    <div>
      {items.length && <ul>{items.map((i) => <li key={i}>{i}</li>)}</ul>}
    </div>
  );
}""",
        "tasks": [
            "Explain why an empty items array causes the literal text '0' to render.",
            "Fix CartSummary so it shows the list when there are items and an 'Your cart is empty' message otherwise, with no stray output.",
        ],
        "reference_solution_code": """function CartSummary({ items }: { items: string[] }) {
  return (
    <div>
      {items.length > 0 ? (
        <ul>
          {items.map((i) => (
            <li key={i}>{i}</li>
          ))}
        </ul>
      ) : (
        <p>Your cart is empty</p>
      )}
    </div>
  );
}""",
        "check_points": [
            "Explanation notes that items.length && (...) evaluates to the number 0 (not false) when the array is empty, and React renders numbers (including 0) as text, unlike false/null/undefined which render nothing.",
            "Fix uses a proper boolean condition (items.length > 0) or a ternary, not a bare && on a number.",
            "Empty-state message is rendered when there are no items.",
        ],
        "common_mistakes": [
            "Wrapping the whole thing in Boolean(items.length) && ... which works but is a less idiomatic patch than comparing explicitly.",
            "Fixing the rendering but forgetting to add an actual empty-state message, leaving a blank div.",
            "Assuming the bug is with the .map() or the key prop instead of the && short-circuit.",
        ],
        "rubric": [
            ["Correct explanation of the falsy/zero pitfall", 40],
            ["Correct conditional fix", 40],
            ["Empty-state UX included", 20],
        ],
    },
    {
        "id": "RCT-09",
        "flavor": "composition",
        "difficulty": "medium",
        "title": "Build a Compound Tabs Component",
        "scenario": "Design a reusable Tabs component using the compound component pattern so consumers can write markup like <Tabs><Tabs.List><Tabs.Tab index={0}>...</Tabs.Tab></Tabs.List><Tabs.Panel index={0}>...</Tabs.Panel></Tabs>, without Tabs needing to know its children's exact structure in advance. The active tab index should be shared implicitly between the sub-components.",
        "code_reference": """// TODO: implement Tabs, Tabs.List, Tabs.Tab, and Tabs.Panel
// so that clicking a Tab shows the matching Panel and hides the others.""",
        "tasks": [
            "Share the active tab index between sub-components using React context, not prop drilling.",
            "Implement Tab so clicking it sets the active index, and give it an aria-selected attribute reflecting whether it's active.",
            "Implement Panel so it renders its children only when its index matches the active index.",
            "Attach List, Tab, and Panel onto Tabs as Tabs.List, Tabs.Tab, Tabs.Panel.",
        ],
        "reference_solution_code": """interface TabsContextValue {
  activeIndex: number;
  setActiveIndex: (index: number) => void;
}

const TabsContext = createContext<TabsContextValue | undefined>(undefined);

function useTabsContext(): TabsContextValue {
  const ctx = useContext(TabsContext);
  if (!ctx) {
    throw new Error("Tabs components must be used inside <Tabs>");
  }
  return ctx;
}

function TabsBase({
  children,
  defaultIndex = 0,
}: {
  children: ReactNode;
  defaultIndex?: number;
}) {
  const [activeIndex, setActiveIndex] = useState(defaultIndex);
  return (
    <TabsContext.Provider value={{ activeIndex, setActiveIndex }}>
      <div>{children}</div>
    </TabsContext.Provider>
  );
}

function TabList({ children }: { children: ReactNode }) {
  return <div role="tablist">{children}</div>;
}

function Tab({ index, children }: { index: number; children: ReactNode }) {
  const { activeIndex, setActiveIndex } = useTabsContext();
  return (
    <button role="tab" aria-selected={activeIndex === index} onClick={() => setActiveIndex(index)}>
      {children}
    </button>
  );
}

function TabPanel({ index, children }: { index: number; children: ReactNode }) {
  const { activeIndex } = useTabsContext();
  if (activeIndex !== index) return null;
  return <div role="tabpanel">{children}</div>;
}

const Tabs = TabsBase as typeof TabsBase & {
  List: typeof TabList;
  Tab: typeof Tab;
  Panel: typeof TabPanel;
};
Tabs.List = TabList;
Tabs.Tab = Tab;
Tabs.Panel = TabPanel;""",
        "check_points": [
            "Active tab index lives in context, shared implicitly between Tab and Panel without manual prop threading.",
            "useTabsContext throws a clear error when used outside a Tabs provider.",
            "TabPanel renders null (not empty string or undefined) for non-active panels.",
            "List/Tab/Panel are attached as static properties on Tabs so consumers can write Tabs.Tab, Tabs.Panel.",
        ],
        "common_mistakes": [
            "Prop-drilling activeIndex and setActiveIndex through List manually instead of using context.",
            "Forgetting to guard useTabsContext, so it silently returns undefined and crashes with a confusing error deep in Tab/Panel.",
            "Using array index of children instead of an explicit index prop, which breaks if tabs are conditionally rendered or reordered.",
        ],
        "rubric": [
            ["Correct context-based state sharing", 40],
            ["Correct Tab / Panel active-state logic", 35],
            ["Correct compound static-property attachment", 25],
        ],
    },
    {
        "id": "RCT-10",
        "flavor": "hooks",
        "difficulty": "medium",
        "title": "Build a useDebounce Hook",
        "scenario": "A search box fires an expensive network request on every keystroke, overwhelming the backend. Product wants the search to only fire 300ms after the user stops typing. Extract a generic useDebounce hook that can be reused for any value, not just strings.",
        "code_reference": """function useDebounce<T>(value: T, delay: number): T {
  // TODO: implement
}

function SearchBox() {
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounce(query, 300);
  // TODO: trigger the search whenever debouncedQuery changes
  return <input value={query} onChange={(e) => setQuery(e.target.value)} />;
}""",
        "tasks": [
            "Implement useDebounce(value, delay) so it returns a debounced copy of value that only updates after the value has been stable for delay milliseconds.",
            "Make sure a pending timeout from a previous render is cancelled if value changes again before delay elapses.",
            "Wire SearchBox to log/search using debouncedQuery whenever it changes.",
        ],
        "reference_solution_code": """function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timeout = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timeout);
  }, [value, delay]);

  return debounced;
}

function SearchBox() {
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounce(query, 300);

  useEffect(() => {
    if (debouncedQuery) {
      console.log("searching for", debouncedQuery);
    }
  }, [debouncedQuery]);

  return <input value={query} onChange={(e) => setQuery(e.target.value)} />;
}""",
        "check_points": [
            "useDebounce stores its own state initialized to value and updates it via setTimeout.",
            "The effect's cleanup function calls clearTimeout so rapid changes reset the timer instead of stacking updates.",
            "Dependency array includes both value and delay.",
            "SearchBox reacts to debouncedQuery (not query) for the expensive operation.",
        ],
        "common_mistakes": [
            "Forgetting the cleanup/clearTimeout, so every keystroke schedules an extra timeout that still fires later.",
            "Debouncing by directly mutating a ref and forcing a re-render manually instead of using state.",
            "Triggering the search effect on query instead of debouncedQuery, defeating the whole purpose of the hook.",
        ],
        "rubric": [
            ["Correct debounce timing logic with cleanup", 55],
            ["Correct generic typing", 20],
            ["Correct consumer wiring in SearchBox", 25],
        ],
    },
    {
        "id": "RCT-11",
        "flavor": "stale-closure",
        "difficulty": "medium",
        "title": "Fix Stale Threshold in Resize Listener",
        "scenario": "A component logs a warning whenever the window is resized below a user-adjustable threshold. QA reports that after changing the threshold with the slider, the warning still uses the old threshold value indefinitely.",
        "code_reference": """function WindowWidthLogger() {
  const [width, setWidth] = useState(window.innerWidth);
  const [threshold, setThreshold] = useState(768);

  useEffect(() => {
    function handleResize() {
      if (window.innerWidth < threshold) {
        console.log("below threshold");
      }
      setWidth(window.innerWidth);
    }
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return <p>{width}</p>;
}""",
        "tasks": [
            "Explain why handleResize keeps using the threshold value from the very first render.",
            "Fix the effect so resizing always compares against the current threshold.",
        ],
        "reference_solution_code": """function WindowWidthLogger() {
  const [width, setWidth] = useState(window.innerWidth);
  const [threshold, setThreshold] = useState(768);

  useEffect(() => {
    function handleResize() {
      if (window.innerWidth < threshold) {
        console.log("below threshold");
      }
      setWidth(window.innerWidth);
    }
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [threshold]);

  return <p>{width}</p>;
}""",
        "check_points": [
            "Explanation correctly identifies that the effect's empty dependency array means handleResize is created once and closes over the threshold from that first render.",
            "Fix adds threshold to the dependency array so the listener is torn down and re-attached with a fresh closure whenever threshold changes.",
            "Cleanup (removeEventListener) is preserved so listeners don't accumulate.",
        ],
        "common_mistakes": [
            "Trying to fix it by calling setThreshold inside the effect, which doesn't address the stale-read problem at all.",
            "Adding threshold to the dependency array but forgetting that this only works because the effect also cleans up the previous listener — removing the cleanup would leak listeners.",
            "Using a ref for threshold and reading ref.current, which also works but is often introduced without explaining the simpler dependency-array fix first.",
        ],
        "rubric": [
            ["Correct root-cause explanation", 35],
            ["Correct dependency array fix", 45],
            ["Cleanup preserved / no listener leak", 20],
        ],
    },
    {
        "id": "RCT-12",
        "flavor": "forms",
        "difficulty": "medium",
        "title": "Fix Uncontrolled Input Warning",
        "scenario": "An email input field works fine while typing, but the browser console shows: 'A component is changing an uncontrolled input to be controlled.' This happens the moment the user types their first character.",
        "code_reference": """function EmailField() {
  const [email, setEmail] = useState();

  return (
    <input value={email} onChange={(e) => setEmail(e.target.value)} />
  );
}""",
        "tasks": [
            "Explain why the input starts out uncontrolled and then switches to controlled.",
            "Fix EmailField so the input is controlled from the very first render, with correct TypeScript typing for the state.",
        ],
        "reference_solution_code": """function EmailField() {
  const [email, setEmail] = useState<string>("");

  return <input value={email} onChange={(e) => setEmail(e.target.value)} />;
}""",
        "check_points": [
            "Explanation notes that useState() with no argument starts as undefined, so value={undefined} makes React treat the input as uncontrolled until the first keystroke sets a real string.",
            "Fix initializes state to an empty string \"\" instead of leaving it undefined.",
            "State is typed as string (useState<string>(\"\")) rather than left as an inferred any/undefined.",
        ],
        "common_mistakes": [
            "Switching to defaultValue instead of value, which silences the warning but makes the field uncontrolled and unable to be validated/reset programmatically.",
            "Using value={email ?? \"\"} as a band-aid at the JSX level instead of fixing the initial state.",
            "Leaving the state untyped, so TypeScript infers it as any and strict mode gains nothing.",
        ],
        "rubric": [
            ["Correct explanation of controlled/uncontrolled switch", 35],
            ["Correct initial state fix", 45],
            ["Correct typing", 20],
        ],
    },
    {
        "id": "RCT-13",
        "flavor": "list-rendering",
        "difficulty": "medium",
        "title": "Build a Filterable List Component",
        "scenario": "Build a small component that takes a flat list of string items and a search box above it. Typing in the box should filter the visible items in real time (case-insensitive substring match), and the component should show a friendly message when nothing matches.",
        "code_reference": """function FilterableList({ items }: { items: string[] }) {
  // TODO: implement search input + filtered rendering
  return null;
}""",
        "tasks": [
            "Implement a controlled search input backed by useState.",
            "Filter items case-insensitively based on the current query on every render.",
            "Render each match in a <ul> with a stable, warning-free key, and show a 'No results' message when the filtered list is empty.",
        ],
        "reference_solution_code": """function FilterableList({ items }: { items: string[] }) {
  const [query, setQuery] = useState("");
  const filtered = items.filter((item) =>
    item.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div>
      <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search..." />
      {filtered.length === 0 ? (
        <p>No results</p>
      ) : (
        <ul>
          {filtered.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}""",
        "check_points": [
            "Search input is controlled (value + onChange bound to state).",
            "Filtering is case-insensitive (both sides lower-cased) and substring-based.",
            "Keys are derived from the item content/id, not the array index.",
            "Empty-results state is handled explicitly rather than rendering an empty <ul>.",
        ],
        "common_mistakes": [
            "Using item index as the key even though items are strings that could repeat or reorder after filtering.",
            "Comparing with === instead of .includes(), only matching exact strings rather than substrings.",
            "Forgetting to lower-case one side of the comparison, making the filter case-sensitive.",
        ],
        "rubric": [
            ["Correct controlled search input", 25],
            ["Correct case-insensitive filter logic", 35],
            ["Correct keys and empty-state handling", 40],
        ],
    },
    {
        "id": "RCT-14",
        "flavor": "state-management",
        "difficulty": "medium",
        "title": "Multi Step Wizard with useReducer",
        "scenario": "Build a 3-step signup wizard. Users move forward and backward between steps, and data entered on earlier steps (name, then email) must be preserved when navigating. Model this with useReducer instead of several separate useState calls, since the step and the data update together.",
        "code_reference": """interface WizardState {
  step: number;
  data: { name: string; email: string };
}

type WizardAction =
  | { type: "NEXT" }
  | { type: "BACK" }
  | { type: "UPDATE_FIELD"; field: keyof WizardState["data"]; value: string };

// TODO: implement wizardReducer and the Wizard component""",
        "tasks": [
            "Implement wizardReducer handling NEXT (clamped at step 3), BACK (clamped at step 1), and UPDATE_FIELD (updates one field of data immutably).",
            "Implement Wizard, showing the name input on step 1, the email input on step 2, and Back/Next buttons that are disabled at the boundaries.",
        ],
        "reference_solution_code": """interface WizardState {
  step: number;
  data: { name: string; email: string };
}

type WizardAction =
  | { type: "NEXT" }
  | { type: "BACK" }
  | { type: "UPDATE_FIELD"; field: keyof WizardState["data"]; value: string };

function wizardReducer(state: WizardState, action: WizardAction): WizardState {
  switch (action.type) {
    case "NEXT":
      return { ...state, step: Math.min(state.step + 1, 3) };
    case "BACK":
      return { ...state, step: Math.max(state.step - 1, 1) };
    case "UPDATE_FIELD":
      return { ...state, data: { ...state.data, [action.field]: action.value } };
    default:
      return state;
  }
}

function Wizard() {
  const [state, dispatch] = useReducer(wizardReducer, { step: 1, data: { name: "", email: "" } });

  return (
    <div>
      <p>Step {state.step} of 3</p>
      {state.step === 1 && (
        <input
          value={state.data.name}
          onChange={(e) => dispatch({ type: "UPDATE_FIELD", field: "name", value: e.target.value })}
        />
      )}
      {state.step === 2 && (
        <input
          value={state.data.email}
          onChange={(e) => dispatch({ type: "UPDATE_FIELD", field: "email", value: e.target.value })}
        />
      )}
      <button onClick={() => dispatch({ type: "BACK" })} disabled={state.step === 1}>Back</button>
      <button onClick={() => dispatch({ type: "NEXT" })} disabled={state.step === 3}>Next</button>
    </div>
  );
}""",
        "check_points": [
            "Reducer clamps step within [1, 3] rather than allowing it to run past the boundaries.",
            "UPDATE_FIELD updates only the targeted field via immutable spread, preserving the other field's value.",
            "Data entered on step 1 is still present in state if the user goes to step 2 and back.",
            "Back/Next buttons are disabled at the respective boundary steps.",
        ],
        "common_mistakes": [
            "Using separate useState(step) and useState(data) that can get out of sync instead of one reducer-managed state object.",
            "Mutating state.data directly (state.data.name = value) inside the reducer.",
            "Forgetting to clamp NEXT/BACK, letting step go to 0 or 4 and rendering nothing.",
        ],
        "rubric": [
            ["Correct reducer logic (immutability + clamping)", 45],
            ["Correct per-step rendering", 30],
            ["Correct button disabled logic", 25],
        ],
    },
    {
        "id": "RCT-15",
        "flavor": "memoization",
        "difficulty": "medium",
        "title": "Fix Broken Memoized Button",
        "scenario": "A toolbar has an expensive Save button (memoized with React.memo, since it does costly layout work) sitting next to an unrelated click counter. Every time the counter increments, console logs show the Save button re-rendering, which shouldn't happen since neither its label nor its behavior changed.",
        "code_reference": """const ExpensiveButton = memo(function ExpensiveButton({
  onClick,
  label,
}: {
  onClick: () => void;
  label: string;
}) {
  console.log("rendering", label);
  return <button onClick={onClick}>{label}</button>;
});

function Toolbar() {
  const [count, setCount] = useState(0);

  function handleSave() {
    console.log("saved");
  }

  return (
    <div>
      <p>{count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
      <ExpensiveButton onClick={handleSave} label="Save" />
    </div>
  );
}""",
        "tasks": [
            "Explain why memo() on ExpensiveButton fails to prevent the re-render here.",
            "Fix Toolbar so ExpensiveButton only re-renders when its own props actually change.",
        ],
        "reference_solution_code": """const ExpensiveButton = memo(function ExpensiveButton({
  onClick,
  label,
}: {
  onClick: () => void;
  label: string;
}) {
  console.log("rendering", label);
  return <button onClick={onClick}>{label}</button>;
});

function Toolbar() {
  const [count, setCount] = useState(0);

  const handleSave = useCallback(() => {
    console.log("saved");
  }, []);

  return (
    <div>
      <p>{count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
      <ExpensiveButton onClick={handleSave} label="Save" />
    </div>
  );
}""",
        "check_points": [
            "Explanation notes that handleSave is a new function on every Toolbar render, so memo's shallow prop comparison sees onClick as changed.",
            "Fix wraps handleSave in useCallback with an empty dependency array (it captures no outer state).",
            "label prop remains a primitive string, so it doesn't need memoization.",
        ],
        "common_mistakes": [
            "Wrapping the whole Toolbar in memo() instead of stabilizing handleSave — Toolbar has no parent re-rendering it, so this does nothing.",
            "Moving handleSave outside the component entirely, losing access to any future component-scoped state it might need.",
            "Using useMemo instead of useCallback for a function value.",
        ],
        "rubric": [
            ["Correct explanation of prop-identity issue", 35],
            ["Correct useCallback fix", 50],
            ["No unrelated/incorrect changes", 15],
        ],
    },
    {
        "id": "RCT-16",
        "flavor": "hooks",
        "difficulty": "medium",
        "title": "Build a usePrevious Hook",
        "scenario": "A price ticker component needs to show whether the price went up, down, or stayed the same compared to its previous value. Build a generic usePrevious hook that returns whatever value a piece of state held on the previous render (undefined on the very first render).",
        "code_reference": """function usePrevious<T>(value: T): T | undefined {
  // TODO: implement
}

function PriceTracker({ price }: { price: number }) {
  const previousPrice = usePrevious(price);
  // TODO: derive direction: "up" | "down" | "same" | "initial"
  return <p>{price}</p>;
}""",
        "tasks": [
            "Implement usePrevious(value) using a ref so it returns the value from the previous render without causing an extra re-render itself.",
            "Use it in PriceTracker to compute and display whether the price moved up, down, stayed the same, or this is the initial render.",
        ],
        "reference_solution_code": """function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T | undefined>(undefined);
  useEffect(() => {
    ref.current = value;
  });
  return ref.current;
}

function PriceTracker({ price }: { price: number }) {
  const previousPrice = usePrevious(price);
  const direction =
    previousPrice === undefined
      ? "initial"
      : price > previousPrice
      ? "up"
      : price < previousPrice
      ? "down"
      : "same";

  return (
    <p>
      {price} ({direction})
    </p>
  );
}""",
        "check_points": [
            "usePrevious stores the value in a ref (not state), so updating it doesn't trigger an additional render.",
            "The ref is updated inside a useEffect with no dependency array (runs after every render) so it reflects the render that just committed, not the one currently in progress.",
            "usePrevious correctly returns undefined on the very first call.",
            "PriceTracker correctly branches on previousPrice being undefined before comparing numerically.",
        ],
        "common_mistakes": [
            "Updating ref.current directly during render (not inside an effect), which would make usePrevious return the *current* value instead of the previous one.",
            "Using useState instead of useRef, causing an unnecessary extra render every time the tracked value changes.",
            "Forgetting to special-case previousPrice === undefined, causing a wrong 'up'/'down' on the very first render.",
        ],
        "rubric": [
            ["Correct ref-based implementation with effect timing", 55],
            ["Correct generic typing", 20],
            ["Correct usage / direction logic in PriceTracker", 25],
        ],
    },
    {
        "id": "RCT-17",
        "flavor": "composition",
        "difficulty": "medium",
        "title": "Mouse Tracker Render Prop",
        "scenario": "Different parts of the app need to react to mouse position in completely different ways (one shows coordinates as text, another moves an image). Rather than building a separate component for each visualization, implement a MouseTracker component that tracks mouse position internally and hands it off via a render prop, letting each consumer decide what to render.",
        "code_reference": """interface Point {
  x: number;
  y: number;
}

function MouseTracker({ render }: { render: (point: Point) => ReactNode }) {
  // TODO: track mouse position on mousemove and call render(point)
  return null;
}""",
        "tasks": [
            "Track the current mouse position in state, updated via an onMouseMove handler on a wrapping <div>.",
            "Call the render prop with the current point and render its result.",
            "Write a small example usage that renders the coordinates as text.",
        ],
        "reference_solution_code": """import React, { useState } from "react";

interface Point {
  x: number;
  y: number;
}

function MouseTracker({ render }: { render: (point: Point) => React.ReactNode }) {
  const [point, setPoint] = useState<Point>({ x: 0, y: 0 });

  function handleMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    setPoint({ x: e.clientX, y: e.clientY });
  }

  return (
    <div onMouseMove={handleMouseMove} style={{ height: 200 }}>
      {render(point)}
    </div>
  );
}

function MouseTrackerExample() {
  return (
    <MouseTracker
      render={(point) => (
        <p>
          Mouse position: {point.x}, {point.y}
        </p>
      )}
    />
  );
}""",
        "check_points": [
            "MouseTracker holds { x, y } in its own state, updated from a mousemove handler.",
            "The render prop is called with the current point and its return value is rendered directly (not stored separately).",
            "handleMouseMove reads clientX/clientY from the event, correctly typed as a React.MouseEvent<HTMLDivElement>.",
            "Example usage demonstrates the separation between tracking logic (MouseTracker) and presentation (the render function).",
        ],
        "common_mistakes": [
            "Hardcoding what gets rendered inside MouseTracker instead of delegating to the render prop, defeating the reusability goal.",
            "Attaching the mousemove listener to window/document instead of the wrapping div without adjusting coordinates, or forgetting cleanup if window is used.",
            "Leaving the event parameter implicitly typed as any instead of React.MouseEvent<HTMLDivElement>.",
        ],
        "rubric": [
            ["Correct render-prop pattern", 40],
            ["Correct mouse-position state/handler", 35],
            ["Correct typing", 25],
        ],
    },
    {
        "id": "RCT-18",
        "flavor": "stale-closure",
        "difficulty": "medium",
        "title": "Fix a Fetch Race Condition",
        "scenario": "A user profile panel fetches user data whenever userId changes (e.g. as the user clicks through a list of teammates quickly). QA reports that if they click two different users in fast succession, the panel sometimes ends up showing the wrong person's data, because an older, slower request resolves after a newer, faster one.",
        "code_reference": """interface User {
  id: string;
  name: string;
}

declare function fetchUser(id: string): Promise<User>;

function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    fetchUser(userId).then((data) => {
      setUser(data);
    });
  }, [userId]);

  return <p>{user ? user.name : "Loading..."}</p>;
}""",
        "tasks": [
            "Explain why a stale in-flight request can overwrite fresher data here.",
            "Fix the effect so a response from an outdated request is ignored once a newer userId has been requested.",
        ],
        "reference_solution_code": """interface User {
  id: string;
  name: string;
}

declare function fetchUser(id: string): Promise<User>;

function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    let ignore = false;
    fetchUser(userId).then((data) => {
      if (!ignore) {
        setUser(data);
      }
    });
    return () => {
      ignore = true;
    };
  }, [userId]);

  return <p>{user ? user.name : "Loading..."}</p>;
}""",
        "check_points": [
            "Explanation correctly describes the race: effect for userId A fires a slow request, userId changes to B and fires a fast request that resolves first, then A's response arrives later and overwrites B's data.",
            "Fix introduces a per-effect-run flag (e.g. ignore) that is set to true in the cleanup function.",
            "setUser is only called when the flag indicates this effect run is still the latest one.",
            "Dependency array remains [userId].",
        ],
        "common_mistakes": [
            "Trying to fix it by adding a loading boolean alone, which doesn't prevent the stale response from still overwriting state.",
            "Using a single module-level or ref variable shared across all instances instead of a per-effect-closure flag, breaking if multiple UserProfile instances exist.",
            "Forgetting to actually check the flag before calling setUser, only setting it in cleanup without reading it.",
        ],
        "rubric": [
            ["Correct explanation of the race condition", 30],
            ["Correct ignore-flag / cleanup fix", 55],
            ["Dependency array and effect structure otherwise intact", 15],
        ],
    },
    {
        "id": "RCT-19",
        "flavor": "forms",
        "difficulty": "medium",
        "title": "Fix Mutated Checkbox Group State",
        "scenario": "A notification preferences form lets a user check any combination of email/sms/push. Testers report that checking or unchecking a box sometimes doesn't visually update at all, and sometimes the wrong box appears to toggle.",
        "code_reference": """function PreferencesForm() {
  const options = ["email", "sms", "push"];
  const [selected, setSelected] = useState<string[]>([]);

  function handleChange(option: string) {
    selected.push(option);
    setSelected(selected);
  }

  return (
    <div>
      {options.map((option) => (
        <label key={option}>
          <input
            type="checkbox"
            checked={selected.includes(option)}
            onChange={() => handleChange(option)}
          />
          {option}
        </label>
      ))}
    </div>
  );
}""",
        "tasks": [
            "Explain the two separate bugs in handleChange: why unchecking never works, and why React sometimes fails to re-render at all.",
            "Fix handleChange so it correctly adds an option when unchecked and removes it when checked, using immutable state updates.",
        ],
        "reference_solution_code": """function PreferencesForm() {
  const options = ["email", "sms", "push"];
  const [selected, setSelected] = useState<string[]>([]);

  function handleChange(option: string) {
    setSelected((prev) =>
      prev.includes(option) ? prev.filter((o) => o !== option) : [...prev, option]
    );
  }

  return (
    <div>
      {options.map((option) => (
        <label key={option}>
          <input
            type="checkbox"
            checked={selected.includes(option)}
            onChange={() => handleChange(option)}
          />
          {option}
        </label>
      ))}
    </div>
  );
}""",
        "check_points": [
            "Explanation identifies both the mutation (selected.push mutates the array in place) and the missing toggle-off branch (it only ever adds, never removes).",
            "Fix uses a functional state update that branches on whether the option is already selected.",
            "No direct mutation of the selected array remains anywhere in the fix.",
            "checked={selected.includes(option)} logic is left intact / still correctly derives checked state.",
        ],
        "common_mistakes": [
            "Fixing only the mutation (using [...selected, option]) but still never handling the uncheck case.",
            "Fixing only the toggle logic but keeping selected.push, still mutating the same array reference React compares against.",
            "Comparing against a stale selected captured in the outer closure instead of using the functional updater form.",
        ],
        "rubric": [
            ["Correct explanation of both bugs", 30],
            ["Correct immutable toggle logic", 50],
            ["No remaining mutation", 20],
        ],
    },
    {
        "id": "RCT-20",
        "flavor": "list-rendering",
        "difficulty": "medium",
        "title": "Fix Mutated Shopping List State",
        "scenario": "A shopping list lets users type an item and click Add. Testers report that clicking Add sometimes appears to do nothing — the item doesn't show up in the list until some unrelated re-render happens later.",
        "code_reference": """function ShoppingList() {
  const [items, setItems] = useState<string[]>(["Milk"]);
  const [text, setText] = useState("");

  function addItem() {
    items.push(text);
    setItems(items);
    setText("");
  }

  return (
    <div>
      <input value={text} onChange={(e) => setText(e.target.value)} />
      <button onClick={addItem}>Add</button>
      <ul>
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  );
}""",
        "tasks": [
            "Explain why calling setItems(items) after items.push(text) fails to trigger a re-render.",
            "Fix addItem so adding an item reliably updates the rendered list.",
        ],
        "reference_solution_code": """function ShoppingList() {
  const [items, setItems] = useState<string[]>(["Milk"]);
  const [text, setText] = useState("");

  function addItem() {
    setItems((prev) => [...prev, text]);
    setText("");
  }

  return (
    <div>
      <input value={text} onChange={(e) => setText(e.target.value)} />
      <button onClick={addItem}>Add</button>
      <ul>
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  );
}""",
        "check_points": [
            "Explanation notes that .push() mutates the existing array in place, so the reference passed to setItems is identical (===) to the previous state, and React's bailout on unchanged state skips the re-render.",
            "Fix creates a new array (e.g. via spread) instead of mutating items.",
            "text is still cleared after adding.",
        ],
        "common_mistakes": [
            "Calling setItems([...items, text]) but leaving the original items.push(text) line in place, still mutating before the copy is made (harmless here but a red flag habit).",
            "Forcing a re-render with a key change or forceUpdate-style hack instead of fixing the state update itself.",
            "Forgetting to clear text after adding, leaving stale text in the input.",
        ],
        "rubric": [
            ["Correct explanation of mutation / reference equality", 35],
            ["Correct immutable update fix", 50],
            ["Input cleared after add", 15],
        ],
    },
    {
        "id": "RCT-21",
        "flavor": "state-management",
        "difficulty": "medium",
        "title": "Theme Toggle with Context",
        "scenario": "The app needs a light/dark theme that any deeply nested component can read and toggle, without threading a theme prop through every layer of the component tree. Build a ThemeContext with a provider and a custom hook for consuming it.",
        "code_reference": """type Theme = "light" | "dark";

// TODO: implement ThemeContext, ThemeProvider, useTheme, and ThemeToggleButton""",
        "tasks": [
            "Create a ThemeContext whose value includes the current theme and a function to toggle it.",
            "Implement ThemeProvider, holding the theme in state and wrapping children with the context provider.",
            "Implement a useTheme() hook that throws if called outside ThemeProvider.",
            "Implement ThemeToggleButton, a consumer that displays the current theme and toggles it on click.",
        ],
        "reference_solution_code": """type Theme = "light" | "dark";

interface ThemeContextValue {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>("light");

  const toggleTheme = useCallback(() => {
    setTheme((t) => (t === "light" ? "dark" : "light"));
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return ctx;
}

function ThemeToggleButton() {
  const { theme, toggleTheme } = useTheme();
  return <button onClick={toggleTheme}>Current: {theme}</button>;
}""",
        "check_points": [
            "Theme state lives in ThemeProvider and is exposed via context, not global variables or prop drilling.",
            "toggleTheme correctly flips between 'light' and 'dark' using a functional update.",
            "useTheme guards against missing provider with a thrown error.",
            "ThemeToggleButton consumes context purely through useTheme, with no direct useContext(ThemeContext) call.",
        ],
        "common_mistakes": [
            "Passing theme and setTheme (the raw setter) through context instead of a semantic toggleTheme function, leaking implementation details to consumers.",
            "Forgetting the undefined guard in useTheme, causing a silent crash with a confusing error far from the real cause.",
            "Re-creating the context value object without useMemo/useCallback in a way that's fine here but would cause unnecessary re-renders in a larger provider (worth a passing mention).",
        ],
        "rubric": [
            ["Correct context + provider design", 40],
            ["Correct toggle logic", 30],
            ["Correct useTheme guard and hook design", 30],
        ],
    },
    {
        "id": "RCT-22",
        "flavor": "memoization",
        "difficulty": "medium",
        "title": "Memoize an Expensive Total",
        "scenario": "An analytics panel recomputes an order total from a large orders array. It also has an unrelated text filter input above it. Every keystroke in the filter box visibly lags because the console shows 'computing total...' logging on every single render, even though orders hasn't changed.",
        "code_reference": """interface Order {
  id: string;
  amount: number;
}

function AnalyticsPanel({ orders }: { orders: Order[] }) {
  const [filter, setFilter] = useState("");

  function computeTotal(orders: Order[]): number {
    console.log("computing total...");
    return orders.reduce((sum, o) => sum + o.amount, 0);
  }

  const total = computeTotal(orders);

  return (
    <div>
      <input value={filter} onChange={(e) => setFilter(e.target.value)} />
      <p>Total: {total}</p>
    </div>
  );
}""",
        "tasks": [
            "Explain why computeTotal runs on every keystroke even though it has nothing to do with the filter input.",
            "Fix AnalyticsPanel so the total is only recomputed when orders actually changes.",
        ],
        "reference_solution_code": """interface Order {
  id: string;
  amount: number;
}

function AnalyticsPanel({ orders }: { orders: Order[] }) {
  const [filter, setFilter] = useState("");

  const total = useMemo(() => {
    console.log("computing total...");
    return orders.reduce((sum, o) => sum + o.amount, 0);
  }, [orders]);

  return (
    <div>
      <input value={filter} onChange={(e) => setFilter(e.target.value)} />
      <p>Total: {total}</p>
    </div>
  );
}""",
        "check_points": [
            "Explanation notes that computeTotal is called unconditionally on every render of AnalyticsPanel, and typing in the filter input causes a re-render regardless of orders.",
            "Fix wraps the computation in useMemo with dependency array [orders].",
            "The console.log stays inside the memoized computation so it only logs when orders changes (a good way to verify the fix on paper).",
        ],
        "common_mistakes": [
            "Memoizing with an empty dependency array [], which stops the total from ever updating even when orders genuinely changes.",
            "Debouncing the filter input instead of addressing the actual expensive computation, treating the symptom rather than the cause.",
            "Moving computeTotal outside the component (module scope) without memoization, which avoids recreating the function but does not avoid re-running it every render.",
        ],
        "rubric": [
            ["Correct explanation of unconditional recomputation", 30],
            ["Correct useMemo fix with right dependency", 55],
            ["No regression in correctness of the total", 15],
        ],
    },
    {
        "id": "RCT-23",
        "flavor": "hooks",
        "difficulty": "medium",
        "title": "Build a useLocalStorage Hook",
        "scenario": "Several settings fields in the app (display name, preferred units, etc.) should persist to localStorage automatically and rehydrate on page load. Rather than duplicating the read/write logic in each component, build a generic useLocalStorage hook that behaves like useState but is backed by localStorage.",
        "code_reference": """function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T) => void] {
  // TODO: implement
}

function NameField() {
  const [name, setName] = useLocalStorage<string>("name", "");
  return <input value={name} onChange={(e) => setName(e.target.value)} />;
}""",
        "tasks": [
            "Implement useLocalStorage so its initial value is read from localStorage if present (falling back to initialValue, and to initialValue if parsing fails).",
            "Persist the value to localStorage whenever it changes.",
            "Match the useState-like API: [value, setValue].",
        ],
        "reference_solution_code": """function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T) => void] {
  const [value, setValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch {
      return initialValue;
    }
  });

  useEffect(() => {
    window.localStorage.setItem(key, JSON.stringify(value));
  }, [key, value]);

  return [value, setValue];
}

function NameField() {
  const [name, setName] = useLocalStorage<string>("name", "");
  return <input value={name} onChange={(e) => setName(e.target.value)} />;
}""",
        "check_points": [
            "Initial state is computed lazily (a function passed to useState) rather than reading localStorage on every render.",
            "A try/catch (or equivalent guard) prevents a JSON.parse failure from crashing the component.",
            "An effect persists value to localStorage whenever key or value changes.",
            "Returned tuple mirrors useState's shape so it's a drop-in replacement.",
        ],
        "common_mistakes": [
            "Reading localStorage.getItem directly as the useState initial argument (not wrapped in a function), causing it to run on every render instead of once.",
            "Forgetting JSON.stringify/JSON.parse, storing/reading raw strings that break for non-string T.",
            "Omitting the try/catch, so malformed existing localStorage data throws and crashes the component on mount.",
        ],
        "rubric": [
            ["Correct lazy-init + persistence logic", 50],
            ["Error handling for malformed storage data", 25],
            ["Correct generic typing / API shape", 25],
        ],
    },
    {
        "id": "RCT-24",
        "flavor": "conditional-rendering",
        "difficulty": "medium",
        "title": "Loading Error Success State Machine",
        "scenario": "A posts list currently tracks loading with two separate booleans (isLoading, isError), which has already caused a bug where both were true at once and the UI showed conflicting content. Rewrite the state as a single discriminated union so illegal states (like loading and error simultaneously) are unrepresentable.",
        "code_reference": """interface Post {
  id: string;
  title: string;
}

declare function fetchPosts(): Promise<Post[]>;

type RequestState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; error: string };

// TODO: implement PostsView using RequestState<Post[]>""",
        "tasks": [
            "Implement PostsView using a single useState<RequestState<Post[]>> instead of separate boolean flags.",
            "Kick off the fetch in an effect, transitioning through 'loading' then to 'success' or 'error'.",
            "Render distinct UI for each of the four states, narrowing the type via state.status so TypeScript knows which fields are available in each branch.",
        ],
        "reference_solution_code": """interface Post {
  id: string;
  title: string;
}

declare function fetchPosts(): Promise<Post[]>;

type RequestState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; error: string };

function PostsView() {
  const [state, setState] = useState<RequestState<Post[]>>({ status: "idle" });

  useEffect(() => {
    setState({ status: "loading" });
    fetchPosts()
      .then((data) => setState({ status: "success", data }))
      .catch((err: Error) => setState({ status: "error", error: err.message }));
  }, []);

  if (state.status === "idle" || state.status === "loading") {
    return <p>Loading...</p>;
  }
  if (state.status === "error") {
    return <p>Error: {state.error}</p>;
  }
  return (
    <ul>
      {state.data.map((post) => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  );
}""",
        "check_points": [
            "A single state variable typed as the discriminated union drives all rendering, with no separate boolean flags.",
            "Each render branch narrows on state.status before accessing state.error or state.data, relying on TypeScript's discriminated-union narrowing.",
            "The effect transitions status: idle -> loading -> success/error correctly.",
            "success state renders using state.data, error state using state.error — never mixed up.",
        ],
        "common_mistakes": [
            "Keeping a hybrid approach (union state plus a leftover isLoading boolean), reintroducing the original illegal-state problem.",
            "Accessing state.data without first narrowing status to 'success', which TypeScript strict mode should reject.",
            "Forgetting to set status to 'loading' before the fetch starts, so the idle UI flashes briefly first.",
        ],
        "rubric": [
            ["Correct discriminated-union modeling", 40],
            ["Correct state transitions in the effect", 30],
            ["Correct narrowed rendering per status", 30],
        ],
    },
    {
        "id": "RCT-25",
        "flavor": "composition",
        "difficulty": "medium",
        "title": "Compose a Card with Children",
        "scenario": "A generic Card, CardHeader, and CardBody have already been built as pure layout/slot components that just render whatever children they're given. Use composition (not new props on Card) to build a ProductCard that displays a product's title and description inside this existing layout.",
        "code_reference": """function Card({ children }: { children: ReactNode }) {
  return <div className="card">{children}</div>;
}

function CardHeader({ children }: { children: ReactNode }) {
  return <div className="card-header">{children}</div>;
}

function CardBody({ children }: { children: ReactNode }) {
  return <div className="card-body">{children}</div>;
}

// TODO: implement ProductCard({ title, description }) using Card/CardHeader/CardBody""",
        "tasks": [
            "Implement ProductCard({ title, description }) by composing Card, CardHeader, and CardBody, without modifying any of the three existing components.",
            "Make sure title renders inside the header slot and description inside the body slot.",
        ],
        "reference_solution_code": """function Card({ children }: { children: ReactNode }) {
  return <div className="card">{children}</div>;
}

function CardHeader({ children }: { children: ReactNode }) {
  return <div className="card-header">{children}</div>;
}

function CardBody({ children }: { children: ReactNode }) {
  return <div className="card-body">{children}</div>;
}

function ProductCard({ title, description }: { title: string; description: string }) {
  return (
    <Card>
      <CardHeader>{title}</CardHeader>
      <CardBody>{description}</CardBody>
    </Card>
  );
}""",
        "check_points": [
            "ProductCard uses Card/CardHeader/CardBody as-is via composition (children), without adding new props to those base components.",
            "title lands inside CardHeader and description inside CardBody, in the correct slots.",
            "ProductCard's own props (title, description) are correctly typed as strings.",
        ],
        "common_mistakes": [
            "Adding a title/description prop directly onto Card or CardHeader instead of composing via children, coupling the generic layout components to product-specific data.",
            "Skipping CardHeader/CardBody and putting both title and description as direct children of Card, losing the intended header/body separation.",
            "Duplicating the layout div/className structure inside ProductCard instead of reusing the existing components.",
        ],
        "rubric": [
            ["Correct composition using existing components", 55],
            ["Correct slot placement (header vs body)", 30],
            ["Correct typing", 15],
        ],
    },
    {
        "id": "RCT-26",
        "flavor": "stale-closure",
        "difficulty": "medium",
        "title": "Fix Missing Effect Dependency",
        "scenario": "A Greeting component receives a name prop from its parent (which changes as the user switches between team members in a dropdown elsewhere on the page). Testers notice the greeting text never updates after the very first name it was given, even though the prop clearly changes.",
        "code_reference": """function Greeting({ name }: { name: string }) {
  const [greeting, setGreeting] = useState("");

  useEffect(() => {
    setGreeting(`Hello, ${name}!`);
  }, []);

  return <p>{greeting}</p>;
}""",
        "tasks": [
            "Explain why the greeting text is frozen after the first render despite name changing.",
            "Fix the component so the greeting always reflects the current name prop.",
        ],
        "reference_solution_code": """function Greeting({ name }: { name: string }) {
  const [greeting, setGreeting] = useState("");

  useEffect(() => {
    setGreeting(`Hello, ${name}!`);
  }, [name]);

  return <p>{greeting}</p>;
}""",
        "check_points": [
            "Explanation identifies the empty dependency array as the cause: the effect runs exactly once on mount and never again when name changes.",
            "Fix adds name to the dependency array so the effect re-runs and calls setGreeting with the latest name.",
            "Bonus/ideal alternative noted or accepted: deriving greeting directly as a computed value (const greeting = `Hello, ${name}!`) instead of storing it in state at all, since it doesn't depend on anything but the prop.",
        ],
        "common_mistakes": [
            "Adding an eslint-disable comment to silence the missing-dependency warning instead of actually fixing it.",
            "Adding name to the dependency array but leaving unrelated derived state in useState when it could be computed directly during render.",
            "Believing the bug is in the JSX/rendering rather than the effect's dependency array.",
        ],
        "rubric": [
            ["Correct root-cause explanation", 35],
            ["Correct dependency array fix", 45],
            ["Recognizes the simpler derive-without-state alternative (or fix is otherwise clean)", 20],
        ],
    },
    {
        "id": "RCT-27",
        "flavor": "hooks",
        "difficulty": "medium",
        "title": "Build a useOnClickOutside Hook",
        "scenario": "A dropdown menu should close whenever the user clicks anywhere outside of it. Extract this as a reusable useOnClickOutside hook that takes a ref to the element to watch and a handler to call on an outside click, so it can be reused for dropdowns, modals, and popovers alike.",
        "code_reference": """function useOnClickOutside<T extends HTMLElement>(
  ref: RefObject<T | null>,
  handler: () => void
): void {
  // TODO: implement
}

function Dropdown() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useOnClickOutside(ref, () => setOpen(false));

  return (
    <div ref={ref}>
      <button onClick={() => setOpen((o) => !o)}>Menu</button>
      {open && <ul><li>Option 1</li></ul>}
    </div>
  );
}""",
        "tasks": [
            "Implement useOnClickOutside by attaching a document-level mousedown listener that checks whether the click target is contained within ref.current.",
            "Call handler only when the click landed outside the referenced element, and skip entirely if ref.current is null.",
            "Clean up the listener when the component unmounts or the ref/handler changes.",
        ],
        "reference_solution_code": """function useOnClickOutside<T extends HTMLElement>(
  ref: RefObject<T | null>,
  handler: () => void
): void {
  useEffect(() => {
    function listener(event: MouseEvent) {
      const el = ref.current;
      if (!el || el.contains(event.target as Node)) {
        return;
      }
      handler();
    }
    document.addEventListener("mousedown", listener);
    return () => document.removeEventListener("mousedown", listener);
  }, [ref, handler]);
}

function Dropdown() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useOnClickOutside(ref, () => setOpen(false));

  return (
    <div ref={ref}>
      <button onClick={() => setOpen((o) => !o)}>Menu</button>
      {open && (
        <ul>
          <li>Option 1</li>
        </ul>
      )}
    </div>
  );
}""",
        "check_points": [
            "Listener is attached to document (mousedown or click), not to the referenced element itself.",
            "Uses el.contains(event.target) to distinguish inside vs outside clicks, guarding against a null ref.current.",
            "Effect cleans up by removing the listener.",
            "Dropdown correctly attaches the ref to its outer wrapping element so the whole menu (button + list) counts as 'inside'.",
        ],
        "common_mistakes": [
            "Attaching the listener to the ref element itself (which would never fire for outside clicks), instead of document.",
            "Forgetting the ref.current null check, causing a crash before the element has mounted or after it has unmounted.",
            "Omitting the cleanup function, leaking one listener per mount/dropdown instance.",
        ],
        "rubric": [
            ["Correct outside-click detection logic", 45],
            ["Correct null-safety and cleanup", 30],
            ["Correct usage/typing in Dropdown", 25],
        ],
    },
    {
        "id": "RCT-28",
        "flavor": "list-rendering",
        "difficulty": "medium",
        "title": "Fix Key Bug in Contact Form",
        "scenario": "A contact editor renders one uncontrolled text input per contact (using defaultValue, since edits are only saved on a separate 'Save' action elsewhere). Testers report that after removing a contact from the middle of the list, one of the remaining inputs shows the wrong name — as if the text 'bled' from a different row.",
        "code_reference": """function ContactForm({ contacts }: { contacts: { id: string; name: string }[] }) {
  const [localContacts, setLocalContacts] = useState(contacts);

  function removeContact(id: string) {
    setLocalContacts((prev) => prev.filter((c) => c.id !== id));
  }

  return (
    <div>
      {localContacts.map((contact, index) => (
        <div key={index}>
          <input defaultValue={contact.name} />
          <button onClick={() => removeContact(contact.id)}>Remove</button>
        </div>
      ))}
    </div>
  );
}""",
        "tasks": [
            "Explain why removing a middle contact causes a remaining input to show the wrong name, specifically because these inputs are uncontrolled (defaultValue).",
            "Fix the component so removing any contact never causes another input's displayed value to change.",
        ],
        "reference_solution_code": """function ContactForm({ contacts }: { contacts: { id: string; name: string }[] }) {
  const [localContacts, setLocalContacts] = useState(contacts);

  function removeContact(id: string) {
    setLocalContacts((prev) => prev.filter((c) => c.id !== id));
  }

  return (
    <div>
      {localContacts.map((contact) => (
        <div key={contact.id}>
          <input defaultValue={contact.name} />
          <button onClick={() => removeContact(contact.id)}>Remove</button>
        </div>
      ))}
    </div>
  );
}""",
        "check_points": [
            "Explanation notes that with an index key, removing an item shifts every subsequent item's index, so React matches the existing DOM input (with its live, possibly-edited uncontrolled value) to a different contact than before, and defaultValue is not reapplied to already-mounted DOM nodes.",
            "Fix changes the key from index to contact.id, a value that doesn't shift when items are removed.",
            "No change needed to defaultValue itself — using a controlled input would also fix it but isn't required if the key is fixed.",
        ],
        "common_mistakes": [
            "Switching to a controlled input as the only fix while leaving key={index}, which happens to mask the symptom in this exact case but doesn't address the root cause and can misbehave in other scenarios (e.g. reordering).",
            "Assuming the bug is in removeContact's filter logic rather than the key/reconciliation behavior.",
            "Using key={contact.name} instead of key={contact.id}, which breaks again if two contacts share a name.",
        ],
        "rubric": [
            ["Correct explanation of uncontrolled-input + index-key interaction", 45],
            ["Correct fix using stable id key", 40],
            ["No unrelated changes", 15],
        ],
    },
    {
        "id": "RCT-29",
        "flavor": "lifting-state",
        "difficulty": "medium",
        "title": "Lift State for Search Filtering",
        "scenario": "SearchBox (a controlled input) and UserList (a filtered list display) have already been implemented as independent, reusable, 'dumb' components that don't manage their own state. Build the parent SearchableUserList that lifts the shared query state up so the two siblings stay in sync.",
        "code_reference": """interface UserItem {
  id: string;
  name: string;
}

function SearchBox({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return <input value={value} onChange={(e) => onChange(e.target.value)} placeholder="Search users..." />;
}

function UserList({ users, query }: { users: UserItem[]; query: string }) {
  const filtered = users.filter((u) => u.name.toLowerCase().includes(query.toLowerCase()));
  return (
    <ul>
      {filtered.map((u) => (
        <li key={u.id}>{u.name}</li>
      ))}
    </ul>
  );
}

// TODO: implement SearchableUserList({ users }) composing SearchBox and UserList""",
        "tasks": [
            "Implement SearchableUserList, holding the query string in state at the parent level (not inside SearchBox or UserList).",
            "Pass the query and its setter down to SearchBox and UserList as props so they stay in sync without either one owning the state itself.",
        ],
        "reference_solution_code": """interface UserItem {
  id: string;
  name: string;
}

function SearchBox({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return <input value={value} onChange={(e) => onChange(e.target.value)} placeholder="Search users..." />;
}

function UserList({ users, query }: { users: UserItem[]; query: string }) {
  const filtered = users.filter((u) => u.name.toLowerCase().includes(query.toLowerCase()));
  return (
    <ul>
      {filtered.map((u) => (
        <li key={u.id}>{u.name}</li>
      ))}
    </ul>
  );
}

function SearchableUserList({ users }: { users: UserItem[] }) {
  const [query, setQuery] = useState("");

  return (
    <div>
      <SearchBox value={query} onChange={setQuery} />
      <UserList users={users} query={query} />
    </div>
  );
}""",
        "check_points": [
            "query state lives only in SearchableUserList; SearchBox and UserList remain unmodified and stateless.",
            "SearchBox receives value and onChange (setQuery passed directly works since its signature matches).",
            "UserList receives the same query value so its filtering stays in sync with what's typed.",
            "Neither sibling talks to the other directly — all communication flows through the lifted parent state.",
        ],
        "common_mistakes": [
            "Giving SearchBox its own internal useState for the input value, causing it to fall out of sync with UserList's filter.",
            "Modifying UserList or SearchBox's props/behavior instead of composing them as given.",
            "Passing an inline wrapper like onChange={(v) => setQuery(v)} unnecessarily where onChange={setQuery} would do (not wrong, but worth noting as simplification).",
        ],
        "rubric": [
            ["Correct lifted-state placement", 50],
            ["Correct prop wiring to both siblings", 35],
            ["No modification of the reusable child components", 15],
        ],
    },
    {
        "id": "RCT-30",
        "flavor": "memoization",
        "difficulty": "medium",
        "title": "Fix Memo Object Identity Bug",
        "scenario": "A UserCard is wrapped in React.memo to avoid re-rendering when an unrelated counter elsewhere in the app updates. Console logs show it re-renders on every click anyway, even though the user data displayed never actually changes.",
        "code_reference": """const UserCard = memo(function UserCard({ user }: { user: { name: string } }) {
  console.log("rendering", user.name);
  return <p>{user.name}</p>;
});

function App() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <button onClick={() => setCount(count + 1)}>{count}</button>
      <UserCard user={{ name: "Ada" }} />
    </div>
  );
}""",
        "tasks": [
            "Explain why memo() fails to prevent UserCard from re-rendering here even though the displayed name never changes.",
            "Fix App so the user object passed to UserCard keeps the same reference across renders when its contents haven't changed.",
        ],
        "reference_solution_code": """const UserCard = memo(function UserCard({ user }: { user: { name: string } }) {
  console.log("rendering", user.name);
  return <p>{user.name}</p>;
});

const staticUser = { name: "Ada" };

function App() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <button onClick={() => setCount(count + 1)}>{count}</button>
      <UserCard user={staticUser} />
    </div>
  );
}""",
        "check_points": [
            "Explanation notes that the inline object literal { name: \"Ada\" } is a brand-new object on every App render, so memo's shallow comparison (===) always sees a changed user prop.",
            "Fix hoists the object so the same reference is reused across renders — either moved outside the component (as here, since it's static) or wrapped in useMemo if it depended on props/state.",
            "UserCard itself is left unchanged; the fix lives entirely in how App constructs the prop.",
        ],
        "common_mistakes": [
            "Adding a custom comparison function to memo() instead of fixing the underlying reference-identity problem at the source.",
            "Wrapping user in useMemo(() => ({ name: \"Ada\" }), []) inside App — functionally fine, but candidates should recognize that hoisting a truly static object outside the component entirely is simpler and avoids the hook.",
            "Removing memo() altogether instead of fixing the prop identity.",
        ],
        "rubric": [
            ["Correct explanation of object-identity issue", 35],
            ["Correct fix (hoisted or memoized stable reference)", 50],
            ["No unnecessary removal of memo", 15],
        ],
    },
]
