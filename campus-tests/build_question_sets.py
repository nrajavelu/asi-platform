"""
Generates 4 additional, fully-distinct 50-question sets (Set 2-5) into
question_sets/, using the same Aptitude/Programming/Answer-Key schema as
build_initial_bank.py (which reuses its sheet-building helpers). Set 1 is
the already-verified question_bank_v1.xlsx, copied in unchanged.

Usage:
    python build_question_sets.py
"""

import shutil
from pathlib import Path

from openpyxl import Workbook

from build_initial_bank import build_answer_key_sheet, build_question_sheet

OUT_DIR = Path(__file__).parent / "question_sets"

# ---------------------------------------------------------------------------
# SET 2
# ---------------------------------------------------------------------------
SET2_APTITUDE = [
    ("APT001", "quant", "easy", "A shopkeeper buys an item for Rs. 800 and sells it for Rs. 960. Find the profit percentage.", "15%", "18%", "20%", "22%", 1, "C"),
    ("APT002", "quant", "easy", "The average of 6 numbers is 15. If one number is excluded, the average becomes 14. Find the excluded number.", "18", "20", "22", "24", 1, "B"),
    ("APT003", "quant", "medium", "A and B together can finish a job in 8 days. A alone can finish it in 20 days. How long will B alone take?", "12 days", "13.3 days", "14 days", "15 days", 1, "B"),
    ("APT004", "quant", "medium", "The ratio of two numbers is 4:7 and their sum is 121. Find the smaller number.", "40", "42", "44", "46", 1, "C"),
    ("APT005", "quant", "easy", "A car covers 240 km in 4 hours. What is its speed in m/s?", "15 m/s", "16.7 m/s", "18 m/s", "20 m/s", 1, "B"),
    ("APT006", "quant", "easy", "Find the simple interest on Rs. 5000 for 3 years at 8% p.a.", "1000", "1100", "1200", "1300", 1, "C"),
    ("APT007", "quant", "easy", "What is 25% of 480 plus 10% of 150?", "125", "130", "135", "140", 1, "C"),
    ("APT008", "quant", "medium", "Find the compound interest on Rs. 8000 for 2 years at 5% p.a. compounded annually.", "800", "820", "840", "860", 1, "B"),
    ("APT009", "logical", "medium", "Find the next term: 5, 11, 23, 47, ?", "92", "94", "95", "96", 1, "C"),
    ("APT010", "logical", "medium", "If BOOK is coded as CPPL (each letter shifted forward by 1), how is PAGE coded?", "QBHF", "QBGF", "PBHF", "QBHE", 1, "A"),
    ("APT011", "logical", "easy", "Find the odd one out: Square, Rectangle, Rhombus, Sphere", "Square", "Rectangle", "Rhombus", "Sphere", 1, "D"),
    ("APT012", "logical", "medium", "All roses are flowers. Some flowers fade quickly. Which conclusion follows?", "All roses fade quickly", "Some roses may fade quickly", "No roses fade quickly", "Cannot be determined", 1, "D"),
    ("APT013", "logical", "easy", "Find the odd one out: 36, 49, 60, 81", "36", "49", "60", "81", 1, "C"),
    ("APT014", "logical", "medium", "Pointing to a man, a woman says, 'His mother is the only daughter of my mother.' How is the woman related to the man?", "Sister", "Mother", "Aunt", "Grandmother", 1, "B"),
    ("APT015", "logical", "medium", "In a code, MOUSE is written as NPVTF (each letter shifted forward by 1). How is TIGER written?", "UJHFS", "UJHFR", "TJHFS", "UJGFS", 1, "A"),
    ("APT016", "logical", "easy", "Complete the analogy: Pen : Write :: Knife : ?", "Cut", "Sharp", "Kitchen", "Metal", 1, "A"),
    ("APT017", "verbal", "easy", "Choose the word closest in meaning to 'Candid'.", "Dishonest", "Frank", "Secretive", "Confused", 1, "B"),
    ("APT018", "verbal", "easy", "Choose the word most opposite in meaning to 'Diligent'.", "Hardworking", "Lazy", "Careful", "Sincere", 1, "B"),
    ("APT019", "verbal", "easy", "Choose the best word to complete: 'She has been working here ___ 2019.'", "since", "for", "from", "in", 1, "A"),
    ("APT020", "verbal", "easy", "Choose the correctly spelled word.", "Occurence", "Occurrence", "Ocurrence", "Occurrance", 1, "B"),
    ("APT021", "verbal", "medium", "Choose the best word to complete: 'The new policy will ___ effect from next month.'", "take", "make", "do", "give", 1, "A"),
    ("APT022", "data_interpretation", "medium", "In a survey of 150 people, 90 like tea, 70 like coffee, and 40 like both. How many like neither?", "20", "25", "30", "35", 1, "C"),
    ("APT023", "data_interpretation", "easy", "A store's sales increased from Rs. 40,000 to Rs. 52,000 in a month. What is the percentage increase?", "20%", "25%", "30%", "35%", 1, "C"),
    ("APT024", "data_interpretation", "easy", "Out of 250 applicants, 40% were shortlisted. How many were NOT shortlisted?", "130", "140", "150", "160", 1, "C"),
    ("APT025", "data_interpretation", "medium", "The ratio of men to women in a company is 7:3, and there are 210 men. How many women are there?", "80", "90", "100", "110", 1, "B"),
]

SET2_PROGRAMMING = [
    ("PROG001", "python_code_reading", "medium", "What does the following print?\n\ndef mystery(n):\n    result = []\n    for i in range(n):\n        if i % 2 == 0:\n            result.append(i * i)\n    return result\n\nprint(mystery(6))", "[0, 4, 16]", "[0, 1, 4, 9, 16, 25]", "[1, 4, 16]", "[0, 4, 16, 36]", 1, "A"),
    ("PROG002", "python_code_reading", "medium", "What does the following print?\n\nx = [1, 2, 3]\ny = x\ny.append(4)\nprint(x)", "[1, 2, 3]", "[1, 2, 3, 4]", "Error", "[4]", 1, "B"),
    ("PROG003", "python_code_reading", "hard", "What is printed by these two calls, in order?\n\ndef f(a, b=[]):\n    b.append(a)\n    return b\n\nprint(f(1))\nprint(f(2))", "[1] then [2]", "[1] then [1, 2]", "[1] then [1]", "Error", 1, "B"),
    ("PROG004", "python_debugging", "medium", "This function is supposed to return the sum of a list, but has a bug. Identify it.\n\ndef total(nums):\n    result = 0\n    for n in nums:\n        result = n\n    return result", "range(nums) should be used instead of nums", "result = n should be result += n", "return should be inside the loop", "nums should be sorted first", 1, "B"),
    ("PROG005", "python_debugging", "easy", "This code has a bug and won't even run. Identify it.\n\ndef is_even(n):\n    if n % 2 = 0:\n        return True\n    return False", "n % 2 = 0 should be n % 2 == 0", "should use n // 2", "missing else statement", "return True and return False should be swapped", 1, "A"),
    ("PROG006", "python_logic_explain", "easy", "What does the following list comprehension produce?\n\nsquares = [x**2 for x in range(5) if x % 2 != 0]", "[0, 1, 4, 9, 16]", "[1, 9]", "[1, 4, 9]", "[0, 4, 16]", 1, "B"),
    ("PROG007", "python_logic_explain", "medium", "What is the purpose of this code pattern?\n\nwith open('data.txt') as f:\n    content = f.read()", "To open the file in write mode", "To automatically close the file after the block, even if an exception occurs", "To read the file faster than normal", "To open multiple files simultaneously", 1, "B"),
    ("PROG008", "python_alt_approach", "easy", "Which of the following is functionally equivalent to this loop?\n\nresult = []\nfor x in range(10):\n    result.append(x * 2)", "result = [x * 2 for x in range(10)]", "result = {x * 2 for x in range(10)}", "result = (x * 2 in range(10))", "result = map(range(10), lambda x: x * 2)", 1, "A"),
    ("PROG009", "python_alt_approach", "easy", "Which alternative to the code below avoids manually managing an index variable?\n\ni = 0\nitems = ['a', 'b', 'c']\nwhile i < len(items):\n    print(items[i])\n    i += 1", "for item in items: print(item)", "for i in range(len(items), 0, -1): print(i)", "while True: print(items[i])", "print(items)", 1, "A"),
    ("PROG010", "python_advanced_lib", "medium", "What does collections.Counter do here?\n\nfrom collections import Counter\nc = Counter(['a', 'b', 'a', 'c', 'b', 'a'])", "It sorts the list alphabetically", "It counts the occurrences of each element, returning a dict-like object", "It removes duplicate elements", "It converts the list to a set", 1, "B"),
    ("PROG011", "python_advanced_lib", "medium", "What is the main benefit of a decorator like this one?\n\ndef timer(func):\n    def wrapper(*args, **kwargs):\n        start = time.time()\n        result = func(*args, **kwargs)\n        print(time.time() - start)\n        return result\n    return wrapper\n\n@timer\ndef slow_function():\n    ...", "It permanently modifies the original function's source code", "It wraps a function to add behavior (like timing) without changing the function's own code", "It deletes the function after it runs once", "It converts the function into a class", 1, "B"),
    ("PROG012", "typescript_applied", "medium", "You have an async function that fetches a user and may return null if not found:\n\nasync function getUser(id: string): Promise<???> { ... }\n\nWhich return type best models this?", "Promise<User>", "Promise<User | null>", "Promise<any>", "Promise<undefined>", 1, "B"),
    ("PROG013", "typescript_applied", "medium", "You need a type for a partial-update API call, where all properties of User are optional:\n\nfunction updateUser(id: string, changes: ???<User>) { ... }\n\nWhich built-in utility type fits best?", "Required<User>", "Readonly<User>", "Partial<User>", "Pick<User>", 1, "C"),
    ("PROG014", "typescript_applied", "medium", "What does TypeScript infer inside the if block?\n\nfunction printLength(value: string | string[]) {\n  if (Array.isArray(value)) {\n    console.log(value.length);\n  }\n}", "value is narrowed to string[] inside the if block", "value stays as string | string[]", "TypeScript throws a compile error", "value is narrowed to string", 1, "A"),
    ("PROG015", "git_workflow", "easy", "You've made changes to a file but want to temporarily set them aside to switch branches without committing. Which git command is most appropriate?", "git commit --amend", "git stash", "git reset --hard", "git branch -d", 1, "B"),
    ("PROG016", "git_workflow", "medium", "Two developers modified the same lines of the same file in different branches, and a merge conflict occurs. What is the correct next step?", "Delete one branch to avoid the conflict", "Manually resolve the conflicting sections in the file, then stage and commit", "Always keep only your own changes automatically", "Force push to overwrite the other branch", 1, "B"),
    ("PROG017", "llm_basics", "medium", "What does 'hallucination' mean in the context of an LLM's output?", "The model refuses to answer", "The model generates plausible-sounding but factually incorrect or fabricated information", "The model runs out of memory", "The model translates text into another language", 1, "B"),
    ("PROG018", "llm_basics", "easy", "What is 'temperature' in the context of LLM text generation?", "The physical heat generated by the server", "A parameter that controls the randomness/creativity of the model's output", "The speed of the API response", "The size of the model's context window", 1, "B"),
    ("PROG019", "claude_model_awareness", "medium", "Anthropic offers different Claude model tiers (e.g., a lighter/faster tier and a more capable/heavier tier). Why might a team choose a lighter, faster tier for a task?", "It's always more accurate than larger models", "It's typically faster and more cost-effective for simple, high-volume tasks", "It has a larger context window than any other tier", "It cannot be used via an API", 1, "B"),
    ("PROG020", "prototyping_ai", "medium", "When using an AI coding assistant to quickly prototype an idea, which approach is generally most effective?", "Write an extremely detailed formal specification before writing any code", "Describe the goal and constraints clearly, then iterate on the AI's output in small steps", "Avoid giving any context and let the AI guess everything", "Only ask for the final, production-ready version with no iteration", 1, "B"),
    ("PROG021", "vscode_ai_awareness", "easy", "What is a key benefit of using an AI coding assistant integrated directly into an editor like VS Code, compared to copy-pasting into a separate chat window?", "It can see and work with the actual project files and context directly, without manual copy-pasting", "It automatically deploys your code to production", "It replaces the need for version control", "It only works for one programming language", 1, "A"),
    ("PROG022", "token_importance", "easy", "Why does the number of tokens in a request matter when working with an AI assistant?", "Tokens have no practical effect", "Tokens affect both cost and whether the input/output fits within the model's context limit", "Tokens only matter for image inputs", "Tokens are only relevant for training, not for using the model", 1, "B"),
    ("PROG023", "md_files", "easy", "In a software project, what is a common purpose of a README.md or similar Markdown file?", "To store compiled binary code", "To document the project (setup instructions, usage, purpose) in a readable, formatted way", "To encrypt sensitive credentials", "To replace the need for source code comments entirely", 1, "B"),
    ("PROG024", "context_understanding", "medium", "When working with an AI coding assistant, why is providing relevant context (e.g., relevant files, error messages, project structure) important?", "It has no effect on the assistant's output", "It helps the assistant give more accurate and relevant responses based on your actual project", "It only matters for the first message in a conversation", "It slows down the assistant with no benefit", 1, "B"),
    ("PROG025", "prompt_engineering", "medium", "Which of the following best demonstrates good prompt engineering practice when asking an AI assistant to perform a coding task?", "\"fix it\"", "\"Fix the bug in calculate_total() where discounts above 50% cause a negative total; return 0 in that case instead\"", "\"make my code better\"", "\"do something with this file\"", 1, "B"),
]

# ---------------------------------------------------------------------------
# SET 3
# ---------------------------------------------------------------------------
SET3_APTITUDE = [
    ("APT001", "quant", "easy", "A retailer buys goods for Rs. 1200 and sells at a loss of 10%. Find the selling price.", "1000", "1050", "1080", "1100", 1, "C"),
    ("APT002", "quant", "easy", "The average of 4 numbers is 25. If a fifth number 40 is added, what is the new average?", "26", "27", "28", "29", 1, "C"),
    ("APT003", "quant", "medium", "Pipe A fills a tank in 10 hours, pipe B in 15 hours. Together, how long to fill the tank?", "5 hours", "6 hours", "7 hours", "8 hours", 1, "B"),
    ("APT004", "quant", "medium", "Two numbers are in ratio 2:3. If each is increased by 10, the ratio becomes 3:4. Find the original numbers.", "20 and 30", "15 and 25", "10 and 20", "25 and 35", 1, "A"),
    ("APT005", "quant", "medium", "A bus travels 180 km in 3 hours and then 220 km in 4 hours. Find its average speed for the whole journey (km/h).", "55", "57.1", "60", "62", 1, "B"),
    ("APT006", "quant", "easy", "Find the simple interest on Rs. 6000 for 4 years at 7.5% p.a.", "1600", "1700", "1800", "1900", 1, "C"),
    ("APT007", "quant", "easy", "What is 60% of 350 minus 20% of 100?", "180", "185", "190", "195", 1, "C"),
    ("APT008", "quant", "medium", "Find the compound interest on Rs. 15000 for 2 years at 10% p.a. compounded annually.", "3000", "3100", "3150", "3200", 1, "C"),
    ("APT009", "logical", "medium", "Find the next term: 3, 7, 15, 31, ?", "59", "61", "62", "63", 1, "D"),
    ("APT010", "logical", "medium", "If HOUSE is coded as IPVTF (each letter shifted forward by 1), how is MOUSE coded?", "NPVTF", "NPUTF", "MPVTF", "NPVTE", 1, "A"),
    ("APT011", "logical", "easy", "Find the odd one out: Chair, Table, Sofa, Wood", "Chair", "Table", "Sofa", "Wood", 1, "D"),
    ("APT012", "logical", "medium", "Statement: All doctors are educated. Ravi is educated. Conclusion: Ravi is a doctor. Is this conclusion valid?", "Valid", "Invalid", "Cannot be determined without more info", "Always true", 1, "B"),
    ("APT013", "logical", "easy", "Find the odd one out: 25, 45, 49, 81", "25", "45", "49", "81", 1, "B"),
    ("APT014", "logical", "medium", "A man said, 'This girl is the wife of my grandson.' How is the man related to the girl?", "Father", "Grandfather", "Father-in-law", "Grandfather-in-law", 1, "D"),
    ("APT015", "logical", "medium", "In a code, LIGHT is written as MJHIU (each letter shifted forward by 1). How is NIGHT written?", "OJHIU", "OJHIT", "NJHIU", "OJGIU", 1, "A"),
    ("APT016", "logical", "easy", "Complete the analogy: Key : Lock :: Password : ?", "Computer", "Account", "Screen", "Internet", 1, "B"),
    ("APT017", "verbal", "easy", "Choose the word closest in meaning to 'Ambiguous'.", "Clear", "Unclear", "Simple", "Direct", 1, "B"),
    ("APT018", "verbal", "easy", "Choose the word most opposite in meaning to 'Reluctant'.", "Hesitant", "Willing", "Unsure", "Doubtful", 1, "B"),
    ("APT019", "verbal", "easy", "Choose the best word to complete: 'He apologized ___ being late.'", "for", "of", "to", "with", 1, "A"),
    ("APT020", "verbal", "easy", "Choose the correctly spelled word.", "Necesary", "Neccessary", "Necessary", "Neccesary", 1, "C"),
    ("APT021", "verbal", "medium", "Choose the best word to complete: 'The committee ___ to postpone the meeting.'", "decide", "decides", "deciding", "decision", 1, "B"),
    ("APT022", "data_interpretation", "medium", "In a group of 100 students, 55 study Math, 45 study Physics, and 20 study both. How many study neither?", "15", "20", "25", "30", 1, "B"),
    ("APT023", "data_interpretation", "easy", "A product's price dropped from Rs. 800 to Rs. 680. What is the percentage decrease?", "10%", "12%", "15%", "18%", 1, "C"),
    ("APT024", "data_interpretation", "easy", "Of 320 employees, 25% work remotely. How many work on-site?", "220", "230", "240", "250", 1, "C"),
    ("APT025", "data_interpretation", "medium", "The ratio of savings to expenditure of a person is 2:5, and expenditure is Rs. 25000. Find the savings.", "8000", "9000", "10000", "11000", 1, "C"),
]

SET3_PROGRAMMING = [
    ("PROG001", "python_code_reading", "medium", "What does the following print?\n\ndef process(items):\n    return [x for x in items if isinstance(x, int)]\n\nprint(process([1, \"two\", 3, 4.0, 5]))", "[1, 3, 5]", "[1, 3, 4.0, 5]", "[1, \"two\", 3, 4.0, 5]", "[]", 1, "A"),
    ("PROG002", "python_code_reading", "easy", "What does the following print?\n\na = \"hello\"\nb = a.upper()\nprint(a, b)", "HELLO HELLO", "hello HELLO", "hello hello", "HELLO hello", 1, "B"),
    ("PROG003", "python_code_reading", "medium", "What does the following print?\n\ndef outer():\n    x = 10\n    def inner():\n        nonlocal x\n        x += 5\n        return x\n    return inner()\n\nprint(outer())", "10", "15", "5", "Error", 1, "B"),
    ("PROG004", "python_debugging", "medium", "This function has a bug. Identify it.\n\ndef average(nums):\n    return sum(nums) / len(num)", "sum(nums) should be sum(num)", "len(num) should be len(nums)", "should use // instead of /", "nums should be a set", 1, "B"),
    ("PROG005", "python_debugging", "easy", "Calling greet(\"Sam\") produces \"HelloSam\" instead of \"Hello Sam\". What's the bug?\n\ndef greet(name):\n    print(\"Hello\" + name)", "Missing a space: should be 'Hello ' + name", "print should be return", "name should be an integer", "The function needs a return statement to work at all", 1, "A"),
    ("PROG006", "python_logic_explain", "easy", "What does this code do?\n\nnums = [4, 2, 7, 1, 9]\nnums.sort(reverse=True)", "Sorts ascending", "Sorts descending, modifying the list in place", "Returns a new sorted list, leaving nums unchanged", "Reverses the list without sorting", 1, "B"),
    ("PROG007", "python_logic_explain", "medium", "What is the purpose of the try/except block in this code?\n\ntry:\n    value = int(user_input)\nexcept ValueError:\n    value = 0", "To make the program run faster", "To catch and handle invalid input gracefully instead of the program crashing", "To always set value to 0", "To validate that user_input is a string", 1, "B"),
    ("PROG008", "python_alt_approach", "easy", "Which is a more Pythonic/idiomatic alternative to this code?\n\nfound = False\nfor item in items:\n    if item == target:\n        found = True\n        break", "found = target in items", "found = items == target", "found = items.index(target)", "found = list(items)", 1, "A"),
    ("PROG009", "python_alt_approach", "easy", "Which alternative achieves the same result as this loop?\n\nsquares = {}\nfor n in range(5):\n    squares[n] = n ** 2", "squares = {n: n**2 for n in range(5)}", "squares = [n**2 for n in range(5)]", "squares = (n, n**2 for n in range(5))", "squares = set(n**2 for n in range(5))", 1, "A"),
    ("PROG010", "python_advanced_lib", "medium", "What does itertools.chain do in the following?\n\nfrom itertools import chain\nresult = list(chain([1, 2], [3, 4], [5]))", "It merges multiple iterables into one flat sequence", "It finds common elements between the lists", "It multiplies elements together", "It removes duplicates across the lists", 1, "A"),
    ("PROG011", "python_advanced_lib", "medium", "What is the benefit of using a `with` statement together with `contextlib.contextmanager` for a custom resource?", "It makes the code run in parallel", "It lets you define setup and cleanup logic (e.g., acquire/release a resource) that runs automatically around a block", "It automatically converts the function to async", "It disables exception handling", 1, "B"),
    ("PROG012", "typescript_applied", "medium", "You're building a function that accepts either a single User or an array of Users and always returns an array:\n\nfunction normalize(input: User | User[]): ??? { ... }\n\nWhich return type best fits?", "User[]", "User", "void", "any", 1, "A"),
    ("PROG013", "typescript_applied", "medium", "In a real app, you want a config object with all required fields present that cannot be modified after creation. Which combination is most appropriate?", "Partial<Config>", "Readonly<Required<Config>>", "any", "Config | undefined", 1, "B"),
    ("PROG014", "typescript_applied", "medium", "Given this generic function, what does TypeScript infer for `result`?\n\nfunction firstElement<T>(arr: T[]): T | undefined {\n  return arr[0];\n}\nconst result = firstElement([1, 2, 3]);", "result: number | undefined", "result: any", "result: number[]", "result: undefined", 1, "A"),
    ("PROG015", "git_workflow", "medium", "You want to combine the last 3 commits on your branch into a single commit before opening a PR. Which approach is appropriate?", "git clone", "git rebase -i (interactive rebase) to squash them", "git fetch", "git tag", 1, "B"),
    ("PROG016", "git_workflow", "medium", "What is the key difference between git merge and git rebase when integrating a feature branch into main?", "merge creates a new merge commit preserving both histories, while rebase replays commits onto main for a linear history", "They are functionally identical in every way", "rebase deletes the feature branch automatically", "merge is only for remote repos, rebase is only for local repos", 1, "A"),
    ("PROG017", "llm_basics", "medium", "What does 'grounding' mean when discussing LLM outputs?", "Powering down the model", "Basing the model's response on verifiable external information/sources rather than only its internal knowledge", "Reducing the model's temperature to zero", "Training the model from scratch", 1, "B"),
    ("PROG018", "llm_basics", "easy", "What is a 'system prompt' typically used for?", "To log errors during training", "To set the overall behavior, role, or instructions for the assistant, separate from the user's messages", "To store the model's weights", "To compress the conversation history", 1, "B"),
    ("PROG019", "claude_model_awareness", "medium", "Why might a team pair a fast/lightweight model tier for simple steps with a more capable tier for complex reasoning, in the same application?", "To reduce overall cost and latency while reserving stronger reasoning for the steps that need it", "Because lightweight models cannot be used in production", "Because this is required by every AI provider", "Because it has no effect on cost or speed", 1, "A"),
    ("PROG020", "prototyping_ai", "easy", "When rapidly prototyping a new feature with an AI assistant, what's a reasonable first step?", "Immediately optimize every function for performance", "Get a rough working version end-to-end first, then refine based on what you learn", "Write comprehensive unit tests before any code exists", "Wait until requirements are 100% finalized before writing anything", 1, "B"),
    ("PROG021", "vscode_ai_awareness", "medium", "What does it typically mean when an AI coding assistant in an editor can 'see the whole repo' or open files?", "It can use that project context to give more relevant suggestions and edits, rather than working blind", "It automatically publishes the repo publicly", "It deletes files it doesn't understand", "It only works if the repo has no more than one file", 1, "A"),
    ("PROG022", "token_importance", "medium", "If a conversation with an AI assistant grows very long, what is a likely consequence related to tokens?", "Nothing changes regardless of length", "It may approach or exceed the model's context limit and/or cost more per request", "The AI assistant becomes faster", "Tokens are automatically deleted after each message", 1, "B"),
    ("PROG023", "md_files", "medium", "Some AI coding tools look for a special Markdown file in a project to understand project-specific conventions. What is the main value of such a file?", "It has no effect on the assistant's behavior", "It gives the assistant persistent, project-specific context and guidance without repeating it in every prompt", "It replaces the need for a README", "It must contain only code, no text", 1, "B"),
    ("PROG024", "context_understanding", "medium", "Why might pasting only an isolated error message (without surrounding code or context) lead to a less useful AI response?", "It never affects the response quality", "The assistant has less information to diagnose the actual cause, so its suggestions may be generic or incorrect", "Error messages are not readable by AI models", "It always produces a better response", 1, "B"),
    ("PROG025", "prompt_engineering", "medium", "Which prompt best follows good prompt engineering practice for a code review request?", "\"review this\"", "\"Review this function for correctness and edge cases, focusing on how it handles empty input and negative numbers\"", "\"is this good\"", "\"check code\"", 1, "B"),
]

# ---------------------------------------------------------------------------
# SET 4
# ---------------------------------------------------------------------------
SET4_APTITUDE = [
    ("APT001", "quant", "medium", "An article is sold for Rs. 690 after a 8% discount on the marked price. Find the marked price.", "720", "735", "750", "765", 1, "C"),
    ("APT002", "quant", "easy", "The average age of 5 friends is 24. If a 6th friend joins and the new average is 25, find the 6th friend's age.", "26", "28", "30", "32", 1, "C"),
    ("APT003", "quant", "medium", "A can do a job in 15 days, B in 10 days. If they work together for 3 days, what fraction of the job remains?", "1/3", "1/2", "2/3", "1/4", 1, "B"),
    ("APT004", "quant", "hard", "Two numbers are in the ratio 5:6. If their LCM is 180, find the numbers.", "25 and 30", "30 and 36", "20 and 24", "35 and 42", 1, "B"),
    ("APT005", "quant", "easy", "A cyclist covers 90 km in 5 hours. What is the speed in m/s?", "4", "5", "6", "7", 1, "B"),
    ("APT006", "quant", "easy", "Find the SI on Rs. 12000 for 2.5 years at 6% p.a.", "1600", "1700", "1800", "1900", 1, "C"),
    ("APT007", "quant", "easy", "What is 35% of 200 plus 45% of 300?", "195", "200", "205", "210", 1, "C"),
    ("APT008", "quant", "medium", "Find the CI on Rs. 20000 for 2 years at 5% p.a. compounded annually.", "2000", "2050", "2100", "2150", 1, "B"),
    ("APT009", "logical", "medium", "Find the next term: 100, 90, 81, 73, ?", "64", "65", "66", "67", 1, "C"),
    ("APT010", "logical", "medium", "If GARDEN is coded as HBSEFO (each letter shifted forward by 1), how is FLOWER coded?", "GMPXFS", "GMPXFR", "FMPXFS", "GMPXES", 1, "A"),
    ("APT011", "logical", "easy", "Find the odd one out: Novel, Magazine, Newspaper, Pen", "Novel", "Magazine", "Newspaper", "Pen", 1, "D"),
    ("APT012", "logical", "medium", "Statement: All squares are rectangles. All rectangles have four sides. Conclusion: All squares have four sides. Is this valid?", "Valid", "Invalid", "Cannot be determined", "Irrelevant", 1, "A"),
    ("APT013", "logical", "easy", "Find the odd one out: 121, 144, 150, 169", "144", "150", "169", "121", 1, "B"),
    ("APT014", "logical", "hard", "Pointing to a photo, a man says 'Her father is my father's only son,' and the man is that only son. How is the woman related to the man?", "Sister", "Wife", "Daughter", "Niece", 1, "C"),
    ("APT015", "logical", "medium", "In a code, PLANT is written as QMBOU (each letter shifted forward by 1). How is CHAIR written?", "DIBJS", "DIBJR", "CIBJS", "DIBIS", 1, "A"),
    ("APT016", "logical", "easy", "Complete the analogy: Fish : Water :: Bird : ?", "Nest", "Sky", "Tree", "Feather", 1, "B"),
    ("APT017", "verbal", "easy", "Choose the word closest in meaning to 'Robust'.", "Weak", "Strong", "Fragile", "Slow", 1, "B"),
    ("APT018", "verbal", "easy", "Choose the word most opposite in meaning to 'Optimistic'.", "Hopeful", "Positive", "Pessimistic", "Cheerful", 1, "C"),
    ("APT019", "verbal", "easy", "Choose the best word to complete: 'She is good ___ solving puzzles.'", "at", "in", "on", "with", 1, "A"),
    ("APT020", "verbal", "easy", "Choose the correctly spelled word.", "Definately", "Definitely", "Definitly", "Deffinitely", 1, "B"),
    ("APT021", "verbal", "medium", "Choose the best word to complete: 'Neither of the answers ___ correct.'", "are", "is", "were", "be", 1, "B"),
    ("APT022", "data_interpretation", "medium", "Among 120 attendees, 70 registered for workshop A, 50 for workshop B, and 25 for both. How many registered for neither?", "20", "25", "30", "35", 1, "B"),
    ("APT023", "data_interpretation", "easy", "Company revenue fell from Rs. 90 lakh to Rs. 72 lakh. Find the percentage decrease.", "15%", "18%", "20%", "22%", 1, "C"),
    ("APT024", "data_interpretation", "easy", "Of 400 students, 35% failed. How many passed?", "240", "250", "260", "270", 1, "C"),
    ("APT025", "data_interpretation", "medium", "The ratio of income to savings of a person is 8:3, and savings is Rs. 9000. Find the income.", "22000", "23000", "24000", "25000", 1, "C"),
]

SET4_PROGRAMMING = [
    ("PROG001", "python_code_reading", "medium", "What does the following print?\n\ndef f(n):\n    if n <= 1:\n        return 1\n    return n * f(n - 1)\n\nprint(f(5))", "60", "100", "120", "125", 1, "C"),
    ("PROG002", "python_code_reading", "medium", "What does the following print?\n\ndata = {\"a\": 1, \"b\": 2}\ndata[\"c\"] = data.get(\"c\", 0) + 1\nprint(data)", "{'a': 1, 'b': 2}", "{'a': 1, 'b': 2, 'c': 1}", "{'a': 1, 'b': 2, 'c': 0}", "Error", 1, "B"),
    ("PROG003", "python_code_reading", "medium", "What is printed by these two calls, in order?\n\ndef add_item(item, lst=None):\n    if lst is None:\n        lst = []\n    lst.append(item)\n    return lst\n\nprint(add_item(1))\nprint(add_item(2))", "[1] then [1, 2]", "[1] then [2]", "[1, 2] then [1, 2]", "Error", 1, "B"),
    ("PROG004", "python_debugging", "medium", "This function silently has an issue for some inputs. Identify it.\n\ndef get_first(lst):\n    if lst:\n        return lst[0]", "lst[0] should be lst[1]", "When lst is empty, the function implicitly returns None with no explicit handling", "if lst: should be if not lst:", "The function needs a for loop", 1, "B"),
    ("PROG005", "python_debugging", "easy", "This code has a bug and won't run. Identify it.\n\ntotal = 0\nfor i in range(1, 10):\n    if i % 3 == 0\n        total += i\nprint(total)", "Missing colon after the if condition", "range(1, 10) should be range(0, 10)", "total should start at 1", "% should be //", 1, "A"),
    ("PROG006", "python_logic_explain", "easy", "What does this code accomplish?\n\nwords = [\"apple\", \"banana\", \"cherry\"]\nresult = sorted(words, key=len)", "Sorts words alphabetically", "Sorts words by their length, shortest first", "Reverses the list", "Removes duplicate words", 1, "B"),
    ("PROG007", "python_logic_explain", "easy", "What is the effect of *args in this function?\n\ndef total(*args):\n    return sum(args)\n\nprint(total(1, 2, 3, 4))", "It only accepts exactly one argument", "It lets the function accept a variable number of positional arguments, collected as a tuple", "It makes all arguments optional with default None", "It converts arguments to a dictionary", 1, "B"),
    ("PROG008", "python_alt_approach", "easy", "Which is a cleaner, more Pythonic alternative to this code?\n\nresult = []\nfor x in range(20):\n    if x % 3 == 0:\n        result.append(x)", "result = [x for x in range(20) if x % 3 == 0]", "result = range(20)", "result = [x for x in range(20)]", "result = filter(range(20))", 1, "A"),
    ("PROG009", "python_alt_approach", "medium", "Which alternative avoids explicitly checking 'if key in dict' before accessing it?\n\nif \"timeout\" in config:\n    value = config[\"timeout\"]\nelse:\n    value = 30", "value = config.get(\"timeout\", 30)", "value = config[\"timeout\"]", "value = config.pop(\"timeout\")", "value = config.setdefault()", 1, "A"),
    ("PROG010", "python_advanced_lib", "medium", "What does this decorator from functools do?\n\nfrom functools import lru_cache\n\n@lru_cache(maxsize=None)\ndef fib(n):\n    if n < 2:\n        return n\n    return fib(n - 1) + fib(n - 2)", "It caches results of previous calls so repeated calls with the same argument are much faster", "It limits the function to run only once", "It automatically parallelizes the function", "It converts the function to run asynchronously", 1, "A"),
    ("PROG011", "python_advanced_lib", "easy", "What does zip() do in the following code?\n\nnames = [\"Alice\", \"Bob\"]\nscores = [85, 90]\npairs = list(zip(names, scores))", "It combines corresponding elements from each iterable into tuples", "It concatenates the two lists into one", "It multiplies each element together", "It sorts both lists", 1, "A"),
    ("PROG012", "typescript_applied", "medium", "You have a discriminated union for API responses:\n\ntype ApiResponse = { status: \"success\"; data: User } | { status: \"error\"; message: string };\n\nWhat pattern safely handles both cases?", "Casting the response to any immediately", "A discriminated union check on the status field (e.g., if (response.status === \"success\"))", "Ignoring the type and accessing .data directly", "Using 'as unknown as User' unconditionally", 1, "B"),
    ("PROG013", "typescript_applied", "easy", "You want a parameter to accept exactly one of \"small\" | \"medium\" | \"large\", not any string. What should you use?", "A string literal union type: \"small\" | \"medium\" | \"large\"", "The any type", "The string type", "A plain string with a comment", 1, "A"),
    ("PROG014", "typescript_applied", "medium", "What's the benefit of enabling strict mode in a real TypeScript application's tsconfig?", "It disables all type checking", "It enables stricter type checks (like catching possible null/undefined access) that help prevent runtime bugs", "It makes the code run faster at runtime", "It automatically formats the code", 1, "B"),
    ("PROG015", "git_workflow", "medium", "You accidentally committed a file with a hardcoded secret, and haven't pushed yet. What is a reasonable first step?", "Push anyway, it's fine", "Amend the commit to remove the secret (or reset and recommit) before pushing, then rotate the secret", "Delete the entire repository", "Ignore it since git history doesn't matter", 1, "B"),
    ("PROG016", "git_workflow", "easy", "What is the purpose of a .gitignore file in a repository?", "It deletes files from the repository automatically", "It tells git which files/patterns to exclude from being tracked", "It stores commit messages", "It merges branches automatically", 1, "B"),
    ("PROG017", "llm_basics", "medium", "What does 'few-shot prompting' mean?", "Giving the model zero examples and only instructions", "Including a few examples of the desired input/output pattern in the prompt to guide the model's response", "Limiting the model to a few tokens of output", "Training the model on a small dataset from scratch", 1, "B"),
    ("PROG018", "llm_basics", "medium", "What is 'RAG' (Retrieval-Augmented Generation) generally used for?", "Making the model generate random text", "Retrieving relevant external information/documents and providing it to the model to ground its response", "Reducing the model's context window", "Compressing model weights", 1, "B"),
    ("PROG019", "claude_model_awareness", "medium", "When choosing between Claude model tiers for a production application, which factor is generally NOT a primary consideration?", "Task complexity and required reasoning depth", "Cost and latency requirements", "The candidate's personal favorite color", "Expected volume of requests", 1, "C"),
    ("PROG020", "prototyping_ai", "medium", "What is a risk of asking an AI assistant to build an entire complex application in one shot without checking intermediate results?", "There is no risk, this is always the best approach", "Errors or misunderstood requirements may compound and be harder to trace/fix later", "It always produces cleaner code", "It eliminates the need for testing", 1, "B"),
    ("PROG021", "vscode_ai_awareness", "medium", "If an AI coding assistant in your editor proposes a multi-file change, what is good practice before accepting it?", "Accept it blindly without review", "Review the proposed diff/changes to confirm they match intent and don't introduce issues", "Always reject any multi-file change", "Delete the project and start over", 1, "B"),
    ("PROG022", "token_importance", "medium", "Why might an application deliberately trim or summarize old conversation history before sending it to an LLM?", "To keep the request within token/context limits and control cost, while preserving relevant information", "Because trimming has no effect on anything", "Because the model requires exactly one message per request", "Because older messages are automatically deleted by the API", 1, "A"),
    ("PROG023", "md_files", "easy", "Why might a team maintain documentation in Markdown (.md) files inside the repository rather than only in an external wiki?", "Markdown files cannot be version-controlled", "Keeping docs alongside the code lets them be versioned, reviewed, and updated together with code changes", "Markdown is only readable by AI tools", "It has no advantages over external tools", 1, "B"),
    ("PROG024", "context_understanding", "medium", "In an AI coding assistant, why might providing the relevant error stack trace improve the quality of help you receive?", "It gives no additional information", "It shows exactly where and why the failure occurred, helping the assistant pinpoint the root cause", "Stack traces are ignored by AI assistants", "It always makes responses slower with no benefit", 1, "B"),
    ("PROG025", "prompt_engineering", "medium", "Which prompt best applies a 'role, context, task, constraints, format' structure for an AI coding assistant?", "\"write code\"", "\"As a senior Python developer, given this existing utils.py file, refactor the parse_date function to handle ISO 8601 strings, without changing its public signature, and return only the updated function\"", "\"make it work please\"", "\"fix\"", 1, "B"),
]

# ---------------------------------------------------------------------------
# SET 5
# ---------------------------------------------------------------------------
SET5_APTITUDE = [
    ("APT001", "quant", "medium", "A trader marks goods 40% above cost price and allows a discount of 10%. Find the profit percentage.", "24%", "26%", "28%", "30%", 1, "B"),
    ("APT002", "quant", "easy", "The average of 7 numbers is 18. If one number is removed, the average of the remaining 6 becomes 17. Find the removed number.", "22", "23", "24", "25", 1, "C"),
    ("APT003", "quant", "hard", "A can complete a task in 24 days, B in 16 days. A works alone for 4 days, then both work together. How many more days are needed to finish?", "6", "7", "8", "9", 1, "C"),
    ("APT004", "quant", "medium", "Two numbers are in ratio 7:9, and their difference is 30. Find the larger number.", "125", "130", "135", "140", 1, "C"),
    ("APT005", "quant", "easy", "A motorbike covers 108 km in 3 hours. Find its speed in m/s.", "8", "9", "10", "11", 1, "C"),
    ("APT006", "quant", "easy", "Find the SI on Rs. 9000 for 3.5 years at 8% p.a.", "2400", "2460", "2520", "2580", 1, "C"),
    ("APT007", "quant", "easy", "What is 45% of 400 minus 25% of 240?", "110", "115", "120", "125", 1, "C"),
    ("APT008", "quant", "medium", "Find the CI on Rs. 25000 for 2 years at 4% p.a. compounded annually.", "2000", "2020", "2040", "2060", 1, "C"),
    ("APT009", "logical", "easy", "Find the next term: 1, 4, 9, 16, 25, ?", "30", "32", "34", "36", 1, "D"),
    ("APT010", "logical", "medium", "If STONE is coded as TUPOF (each letter shifted forward by 1), how is CLOUD coded?", "DMPVE", "DMPVD", "CMPVE", "DMOVE", 1, "A"),
    ("APT011", "logical", "easy", "Find the odd one out: Guitar, Violin, Piano, Drumstick", "Guitar", "Violin", "Piano", "Drumstick", 1, "D"),
    ("APT012", "logical", "medium", "Statement: No fish can fly. All sharks are fish. Conclusion: No sharks can fly. Is this valid?", "Valid", "Invalid", "Cannot be determined", "Irrelevant", 1, "A"),
    ("APT013", "logical", "easy", "Find the odd one out: 216, 512, 600, 729", "216", "512", "600", "729", 1, "C"),
    ("APT014", "logical", "medium", "A woman with no sisters says, 'This boy is the son of my father's only daughter.' How is she related to the boy?", "Aunt", "Mother", "Sister", "Cousin", 1, "B"),
    ("APT015", "logical", "medium", "In a code, WATER is written as XBUFS (each letter shifted forward by 1). How is EARTH written?", "FBSUI", "FBSUH", "EBSUI", "FBRUI", 1, "A"),
    ("APT016", "logical", "easy", "Complete the analogy: Author : Book :: Composer : ?", "Instrument", "Music", "Concert", "Orchestra", 1, "B"),
    ("APT017", "verbal", "easy", "Choose the word closest in meaning to 'Vigilant'.", "Careless", "Watchful", "Sleepy", "Relaxed", 1, "B"),
    ("APT018", "verbal", "easy", "Choose the word most opposite in meaning to 'Generous'.", "Kind", "Giving", "Stingy", "Charitable", 1, "C"),
    ("APT019", "verbal", "easy", "Choose the best word to complete: 'He is responsible ___ managing the team.'", "for", "of", "to", "at", 1, "A"),
    ("APT020", "verbal", "easy", "Choose the correctly spelled word.", "Accomodate", "Acommodate", "Accommodate", "Accommadate", 1, "C"),
    ("APT021", "verbal", "medium", "Choose the best word to complete: 'The jury ___ divided in its opinion.'", "is", "are", "be", "being", 1, "A"),
    ("APT022", "data_interpretation", "medium", "In a class of 90 students, 50 play cricket, 40 play basketball, and 15 play both. How many play neither?", "10", "15", "20", "25", 1, "B"),
    ("APT023", "data_interpretation", "easy", "A startup's users grew from 2,000 to 2,600 in a quarter. What is the percentage growth?", "25%", "28%", "30%", "32%", 1, "C"),
    ("APT024", "data_interpretation", "easy", "Out of 500 votes cast, 44% were invalid. How many valid votes were there?", "260", "270", "280", "290", 1, "C"),
    ("APT025", "data_interpretation", "medium", "The ratio of tea drinkers to coffee drinkers in an office is 3:7, and there are 84 coffee drinkers. How many tea drinkers are there?", "30", "33", "36", "39", 1, "C"),
]

SET5_PROGRAMMING = [
    ("PROG001", "python_code_reading", "easy", "What does the following print?\n\ndef f(lst):\n    return lst[::-1]\n\nprint(f([1, 2, 3, 4]))", "[1, 2, 3, 4]", "[4, 3, 2, 1]", "[4, 1, 2, 3]", "Error", 1, "B"),
    ("PROG002", "python_code_reading", "medium", "What does the following print?\n\nx = 5\ndef change():\n    x = 10\n    return x\n\nprint(change(), x)", "10 10", "5 5", "10 5", "5 10", 1, "C"),
    ("PROG003", "python_code_reading", "hard", "What does the following print?\n\ndef make_multiplier(n):\n    def multiplier(x):\n        return x * n\n    return multiplier\n\ndouble = make_multiplier(2)\nprint(double(7))", "9", "12", "14", "21", 1, "C"),
    ("PROG004", "python_debugging", "medium", "This code will raise an error for certain inputs. What is the best fix?\n\ndef divide(a, b):\n    return a / b\n\nprint(divide(10, 0))", "a / b should be a // b, which avoids the error", "The function should check for b == 0 and handle it explicitly instead of letting it crash unexpectedly", "10 should be changed to 1", "There is no issue, this code is correct as-is", 1, "B"),
    ("PROG005", "python_debugging", "hard", "This function is supposed to count vowels but returns wrong results. Identify the bug.\n\ndef count_vowels(word):\n    count = 0\n    for letter in word:\n        if letter in \"aeiou\":\n            count =+ 1\n    return count", "'aeiou' should include uppercase vowels too", "count =+ 1 should be count += 1", "letter in word should be word in letter", "count should start at 1, not 0", 1, "B"),
    ("PROG006", "python_logic_explain", "medium", "What does this code do?\n\nseen = set()\nunique = []\nfor item in [1, 2, 2, 3, 1, 4]:\n    if item not in seen:\n        seen.add(item)\n        unique.append(item)\nprint(unique)", "[1, 2, 2, 3, 1, 4]", "[1, 2, 3, 4]", "[4, 3, 2, 1]", "[1, 2, 3, 1, 4]", 1, "B"),
    ("PROG007", "python_logic_explain", "easy", "What is the purpose of __init__ in this class?\n\nclass Point:\n    def __init__(self, x, y):\n        self.x = x\n        self.y = y", "It's called automatically when a new object is created, to initialize its attributes", "It deletes the object when no longer needed", "It converts the object to a string", "It is only used for class methods, not instances", 1, "A"),
    ("PROG008", "python_alt_approach", "medium", "Which is a more concise, Pythonic alternative to this code for summing only positive numbers?\n\ntotal = 0\nfor n in numbers:\n    if n > 0:\n        total += n", "total = sum(n for n in numbers if n > 0)", "total = sum(numbers)", "total = len([n for n in numbers if n > 0])", "total = max(numbers)", 1, "A"),
    ("PROG009", "python_alt_approach", "easy", "Which alternative more concisely expresses this conditional assignment?\n\nif score >= 60:\n    result = \"pass\"\nelse:\n    result = \"fail\"", "result = \"pass\" if score >= 60 else \"fail\"", "result = (score >= 60)", "result = score >= 60 ? \"pass\" : \"fail\"", "result = \"pass\" or \"fail\"", 1, "A"),
    ("PROG010", "python_advanced_lib", "medium", "What does this use of defaultdict avoid having to do manually?\n\nfrom collections import defaultdict\ngroups = defaultdict(list)\nfor word in [\"cat\", \"car\", \"dog\", \"do\"]:\n    groups[word[0]].append(word)", "Checking if the key exists and initializing it with an empty list before appending", "Sorting the words alphabetically", "Removing duplicate words", "Converting words to uppercase", 1, "A"),
    ("PROG011", "python_advanced_lib", "easy", "What does enumerate provide here that a plain 'for item in items' loop does not?\n\nfor index, item in enumerate(items):\n    print(index, item)", "It provides the index of each item alongside the item itself, without manually tracking a counter", "It reverses the list", "It removes the need for a loop entirely", "It sorts the items by index", 1, "A"),
    ("PROG012", "typescript_applied", "medium", "You're writing a function that should accept objects with at least id and name, but may have other properties too. What's the most appropriate approach?", "Define an interface with id and name as required properties; extra properties are allowed structurally", "Use the any type", "Require the object to have exactly id and name and nothing else", "Use never as the parameter type", 1, "A"),
    ("PROG013", "typescript_applied", "medium", "You have an async function that may throw during an API call:\n\nasync function fetchData() {\n  const res = await fetch(url);\n  ...\n}\n\nWhat's the idiomatic way to handle errors?", "Wrap the await call in a try/catch block to handle rejected promises/errors gracefully", "Ignore errors, they resolve themselves", "Only use .then() chains, never async/await", "Errors in async functions cannot be caught", 1, "A"),
    ("PROG014", "typescript_applied", "medium", "Why might an app prefer a type alias like type Status = \"idle\" | \"loading\" | \"success\" | \"error\" over plain strings everywhere?", "It provides compile-time checking that only valid status values are used, catching typos and invalid states early", "It has no practical benefit over plain strings", "It makes the code run faster at runtime", "It is required by JavaScript", 1, "A"),
    ("PROG015", "git_workflow", "medium", "You need to find which commit introduced a specific bug in a file's history. Which approach is designed for this kind of investigation?", "git bisect (or reviewing git log/git blame on the file)", "git clone", "git init", "git remote", 1, "A"),
    ("PROG016", "git_workflow", "medium", "What does git pull do, in terms of the underlying operations it combines?", "It only stages changes, nothing else", "It fetches changes from the remote and then merges (or rebases) them into your current branch", "It permanently deletes your local changes", "It only works on the main branch", 1, "B"),
    ("PROG017", "llm_basics", "easy", "What is 'zero-shot prompting'?", "Asking the model to perform a task with no examples given, relying only on instructions", "Giving the model thousands of training examples", "Disabling the model's output entirely", "Running the model with temperature set to zero", 1, "A"),
    ("PROG018", "llm_basics", "medium", "Why might an LLM give a different answer to the same prompt on two separate occasions?", "The model is broken", "Sampling randomness (e.g., non-zero temperature) can lead to different token choices during generation", "LLMs always give identical answers to identical prompts, this cannot happen", "The model remembers previous unrelated conversations", 1, "B"),
    ("PROG019", "claude_model_awareness", "medium", "What is a reasonable way to decide which Claude model tier to use for a new feature?", "Always use the cheapest tier for everything, regardless of task difficulty", "Evaluate the task's complexity/accuracy needs against cost and latency requirements, and test candidate tiers on representative examples", "Always use the most expensive tier for everything, regardless of task", "Model choice never matters", 1, "B"),
    ("PROG020", "prototyping_ai", "medium", "What's a practical benefit of using an AI assistant to generate a first draft of boilerplate code during prototyping?", "It eliminates the need to ever read or understand the code", "It saves time on repetitive setup so you can focus effort on the unique/complex parts of the feature", "It guarantees the code is production-ready with no review", "It replaces the need for a design/plan entirely", 1, "B"),
    ("PROG021", "vscode_ai_awareness", "medium", "If an AI coding assistant in VS Code suggests a change that conflicts with your team's coding conventions, what is the appropriate response?", "Always accept AI suggestions without question", "Review and adjust/reject the suggestion to align with your team's standards, just as with a human contributor's code", "Disable the linter instead", "Stop using version control", 1, "B"),
    ("PROG022", "token_importance", "medium", "In an API that charges based on token usage, why might sending a large, mostly-irrelevant document as context for a simple question be wasteful?", "It has no cost or performance impact", "It increases token usage (and thus cost/latency) without necessarily improving the answer to a simple, unrelated question", "It always improves accuracy regardless of relevance", "Tokens are free for document uploads", 1, "B"),
    ("PROG023", "md_files", "medium", "What is a benefit of writing clear commit messages and .md documentation together with code changes, from an AI-assistant-usage perspective?", "It has no relationship to AI tools", "It gives both humans and AI assistants better context for understanding why changes were made, improving future assistance", "It slows down every future AI interaction", "AI tools cannot read Markdown", 1, "B"),
    ("PROG024", "context_understanding", "medium", "Why does an AI assistant sometimes ask clarifying questions instead of immediately generating code?", "It is malfunctioning", "Insufficient context/ambiguity in the request can lead to a wrong solution, so clarifying first improves the chance of a correct result", "It is stalling for no reason", "It is incapable of writing code", 1, "B"),
    ("PROG025", "prompt_engineering", "medium", "Which of these best demonstrates specifying a clear constraint in a prompt to an AI coding assistant?", "\"write some code\"", "\"Implement this without adding any new external dependencies, and keep the function under 20 lines\"", "\"make it good\"", "\"just do it\"", 1, "B"),
]

SETS = {
    2: (SET2_APTITUDE, SET2_PROGRAMMING),
    3: (SET3_APTITUDE, SET3_PROGRAMMING),
    4: (SET4_APTITUDE, SET4_PROGRAMMING),
    5: (SET5_APTITUDE, SET5_PROGRAMMING),
}


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)

    set1_src = Path(__file__).parent / "question_bank_v1.xlsx"
    set1_dst = OUT_DIR / "question_set_1.xlsx"
    if set1_src.exists():
        shutil.copy(set1_src, set1_dst)
        print(f"Copied {set1_src.name} -> {set1_dst}")
    else:
        print(f"Warning: {set1_src} not found, skipping Set 1")

    for n, (aptitude, programming) in SETS.items():
        wb = Workbook()
        wb.remove(wb.active)
        build_question_sheet(wb, "Aptitude", aptitude)
        build_question_sheet(wb, "Programming", programming)
        build_answer_key_sheet(wb, aptitude + programming)

        out_path = OUT_DIR / f"question_set_{n}.xlsx"
        wb.save(out_path)
        print(f"Wrote {out_path}: {len(aptitude)} aptitude + {len(programming)} programming questions")


if __name__ == "__main__":
    main()
