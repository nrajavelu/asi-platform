# Mock Sets — Dry-Run Content Only

Same structure as **SIT Master** (same question counts, same round
durations, same file formats and loading mechanics) so you can rehearse
the exact platform flow end-to-end — but the content itself is generic,
basic-level, and deliberately unrelated to the real SIT Master
question topics, so nothing about the actual test leaks from a dry run.

## What's here

| Folder | Sets | Content |
|---|---|---|
| `Aptitude/` | 5 sets, 20Q/30min each | Basic arithmetic, generic logic puzzles, everyday scenarios - no business/AI framing |
| `Programming/` | 5 sets, 30Q/60min each | General computer-literacy trivia (CPU/RAM/file types) + basic logic - **not** Git/REST/AI-LLM/prompt-engineering content |
| `Coding/` | 5 sets (`mock_set1/` ... `mock_set5/`), 15Q/90min each | Trivial Python problems (add two numbers, reverse a string) - no API-handling, prompt-assembly, or SQL/vector problems |

## Loading

Identical mechanics to SIT Master:
```
python load_questions.py "Mock Sets/Aptitude/mock_set1.xlsx"
python load_questions.py "Mock Sets/Programming/mock_set1.xlsx"
python load_coding_questions.py --replace "Mock Sets/Coding/mock_set1/"
```
(The `--replace` flag matters here too - see the note in `SIT Master/README.md`.)

## What's deliberately different from SIT Master

- Different topic tags entirely for Programming/Coding (`general_computing`,
  `basic_logic`, `mock_basic` instead of `programming_dsa`, `ai_llm_concepts`,
  etc.) - so even the topic labels give no hint about the real breakdown.
- No AI/LLM, prompt-engineering, Git, REST, or vector-DB content anywhere.
- All content difficulty is uniformly "easy" - mocks aren't for calibrating
  a real difficulty curve, only for testing that the platform mechanics
  (timer, question count, submission flow, scoring) work as expected.

## One honest caveat

Given the much lower stakes of dry-run content, a handful of basic items
repeat across different mock sets (via intentional wraparound reuse in the
generator) - this was a deliberate scope tradeoff, unlike SIT Master where
zero repeats across all 7 real sets was verified as a hard requirement.
