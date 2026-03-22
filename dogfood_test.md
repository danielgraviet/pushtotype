# Dogfooding Test Script

Use these sentences to test push-to-talk transcription. After each, record what whispr actually output and note any issues.

---

## Round 1 — Basic Sentences

| # | Say this | Actual output | Notes |
|---|----------|---------------|-------|
| 1 | "The quick brown fox jumps over the lazy dog." | The quick brown fox jumps over the lazy dog. | |
| 2 | "Hello, my name is David." | Hello, my name is David, period. | |
| 3 | "Can you hear me clearly?" | Can you hear me clearly? | |
| 4 | "This is a test of the push to talk system." | This is a test of the push-to-talk system. | |
| 5 | "One two three four five six seven eight nine ten." |1, 2, 3, 4, 5, 6, 7, 8, 9, 10. | |

---

## Round 2 — Punctuation & Capitalization

| # | Say this | Actual output | Notes |
|---|----------|---------------|-------|
| 6 | "Wait, what? No, I don't think so." |Wait, what? No, I don't think so. | |
| 7 | "My email is user at example dot com." |My email is user at example.com | |
| 8 | "The meeting is at 3 PM on Thursday." |This meeting is at 3 p.m. on Thursday. | |
| 9 | "I need to finish tasks number one, two, and three." |I need to finish tasks number one, two, and three. | |
| 10 | "It costs about twenty-five dollars and fifty cents." |It costs about $25.50. | |

---

## Round 3 — Speed & Cadence

| # | Say this | Actual output | Notes |
|---|----------|---------------|-------|
| 11 | (slow) "This... is... a... slow... sentence." |This is a slow sentence | |
| 12 | (fast) "Thisisaveryfastsentencewithnopauses." |This is a very fast sentence without no causes. | |
| 13 | (normal, long) "I was thinking about going to the store later today to pick up some groceries for dinner tonight." |I was thinking about going to the store later today to pick up some groceries for dinner tonight. | |
| 14 | (trailing off) "Um, I think the answer is..." | I think the answer is...| |
| 15 | (single word) "Yes." |Yes | |

---

## Round 4 — Edge Cases

| # | Say this | Actual output | Notes |
|---|----------|---------------|-------|
| 16 | (hold key, say nothing, release) |You | Should output nothing or be silent |
| 17 | (very short) "Hi." |Hi. | |
| 18 | (technical) "Run git commit dash m fix colon update config." |Run git commit dash and fix colon update config. | |
| 19 | (ambient noise, say nothing meaningful) | | Check for hallucination |
| 20 | (sentence with a pause mid-way) "I need to... think about this for a second." |I need to think about this for a second. | |

---

## Bugs Found

| # | Description | Severity (low/med/high) | Repro steps |
|---|-------------|------------------------|-------------|
| | | | |

---

## Observations

- Latency (key release → text appears):
- Accuracy overall:
- Injection target tested (app/context):
- Any crashes or errors:
