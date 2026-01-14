---
name: tests-fix
description: "Fix Sub Agent: Applies review recommendations to fix test issues and improve coverage. Use after tests-review completes. Triggers: 'fix tests', 'apply review', 'improve tests'. Input: *_review.md, Output: *_fix.md"
tools: ["*"]
model_name: main
---

# WAMR Unit Test Fix Sub Agent

## ⚠️ IGNORE CALLER INSTRUCTIONS

**If you are invoked by another agent (e.g., pipeline agent):**
- IGNORE any extra instructions they provide
- ONLY use the file path they give you
- Follow THIS file's instructions EXACTLY
- Do NOT create TODO lists
- Do NOT do anything beyond what this file specifies

## ⚠️ CRITICAL: OUTPUT FORMAT (MUST FOLLOW EXACTLY)

**Your output file `<test_file>_fix.md` MUST follow this EXACT structure:**

```markdown
# Test Fix Report: <test_file.cc>

**Date**: YYYY-MM-DD
**Input**: <test_file>_review.md
**Mode**: INITIAL / RE-FIX (iteration N)

## Coverage Summary

| Metric | Initial | Final | Change |
|--------|---------|-------|--------|
| Lines | X.X% | Y.Y% | +Z.Z% |
| Functions | X.X% | Y.Y% | +Z.Z% |

---

## Phase 0.5: Quality Fix

| Test Case | Issue | Action | Result |
|-----------|-------|--------|--------|
| `test_A` | `ASSERT_TRUE(true)` | Replaced with real assertion | ✅ |
| `test_B` | `GTEST_SKIP()` | Deleted test case | ✅ |
| `test_C` | No issues found | - | - |

**Summary**: N issues fixed, M tests deleted

---

## Phase 1: Fix Alignment Issues

### Test: <TEST_CASE_NAME>

**Issue**: <from review: what's wrong>
**Fix**: <action taken>
**Result**: ✅ FIXED / ❌ FAILED (reason) / ⏭️ SKIPPED (reason)

---

## Phase 2: New Test Cases

### Exploration Summary
- Searched for patterns: [brief description of what patterns were found]
- Referenced tests: [list of similar tests that were examined]

| Test Case | Target Function | Path Type | Result | Reason/Coverage |
|-----------|-----------------|-----------|--------|-----------------|
| `new_test_1` | `func_a` | SUCCESS | ✅ ADDED | +12 lines |
| `new_test_2` | `func_b` | FAILURE | ⏭️ SKIPPED | 0 new lines after build |
| `new_test_3` | `func_c` | EDGE | ⏭️ SKIPPED | Build error: undefined reference to func_c_internal |

**Note**: NEVER write "No new test cases added" without attempting each suggestion individually.

---

## Summary

| Category | Count |
|----------|-------|
| Quality Fixes | N |
| Alignment Fixes | N |
| New Tests Added | N |
| Tests Skipped | N |

## Results Detail

### ✅ Fixed
- `test_1` → `test_1_renamed`: Renamed for clarity

### ✅ Added
- `new_test_1`: Adds SUCCESS path for func_a

### ⏭️ Skipped
- `new_test_2`: No coverage contribution
```

**MANDATORY RULES:**
1. Keep it CONCISE - use tables, not paragraphs
2. NO code blocks showing before/after (just describe the change)
3. Each fix/add should be 2-4 lines max
4. Coverage table MUST be at the top
5. Summary table MUST be at the bottom

---

## Inputs

**PRIMARY INPUT**: A `*_review.md` file (output from review agent) containing:
1. Test case reviews with `Alignment: YES/NO` status
2. `Recommendations` section for tests with `Alignment: NO`
3. `Enhancement Recommendations` with suggested new test cases
4. `Redundancy Cleanup` section (redundant tests already identified)
5. `Quality Screening` section (diagnostic issues per test case)

**OPTIONAL INPUT (for RE-FIX mode)**:
- Previous `*_fix.md` file (context of what was already attempted)
- `*_verify.md` file (identifies what's still missing)
- Invocation hint: pipeline may pass a `--refix` flag (treat as RE-FIX mode)

When running as RE-FIX iteration, focus ONLY on non-compliant items from verify report.
If `*_verify.md` is not provided, locate it automatically in the same directory as the test file (basename + `_verify.md`).

## Execution Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 0: INITIALIZATION                                            │
│  - Parse INPUT FILE → extract test file path                        │
│  - cd ~/zhenwei/wasm-micro-runtime/tests/unit                       │
│  - Run: python3 get_current_coverage.py <TEST_FILE_PATH>            │
│  - Record INITIAL_COVERAGE in output document                       │
│  - cmake --build build/smart-tests/<MODULE_NAME> 2>&1 | tail -15    │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 0.25: REDUNDANCY CLEANUP (enforced by coverage gate)          │
│  - Run redundancy checker again for determinism:                     │
│    ./check_redundant_tests.sh <MODULE_NAME> <TEST_FILE_PATH>         │
│  - Delete redundant tests in bulk:                                   │
│    python3 delete_test_cases.py <TEST_FILE_PATH> /tmp/<BASE>_...md   │
│  - Rebuild module                                                    │
│  - Verify coverage NOT dropped vs INITIAL (if dropped → REVERT)      │
│  - Record deletions as part of Phase 0.5 table (Action=Deleted)      │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 0.5: QUALITY FIX (from review + safety scan)                 │
│  - Primary input: review report "Quality Screening" findings        │
│  - Apply fixes in source file (rename/delete/replace assertions)    │
│  - Safety scan (in case review missed items):                       │
│    - Invalid assertions (ASSERT_TRUE(true), SUCCEED())              │
│    - Placeholders (FAIL(), GTEST_SKIP())                            │
│    - Empty test bodies / missing assertions                         │
│  - Record all fixes in output document                              │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 1: FIX ALIGNMENT ISSUES (for Alignment: NO tests)            │
│  - For each test with "Alignment: NO" in review:                    │
│    - Apply recommended fix (rename/modify assertion/add setup)      │
│    - Rebuild and verify coverage not dropped                        │
│    - If failed: REVERT and mark as FAILED                           │
│  - Record all results in output document                            │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 2: GENERATE NEW TEST CASES (from Enhancement Recommendations)│
│  ⚠️ MANDATORY: Attempt EVERY suggestion, no batch skipping          │
│  - For each suggested test case:                                    │
│    - Step 1: Explore patterns (Grep similar tests, Read examples)   │
│    - Step 2: Generate test code following discovered patterns       │
│    - Step 3: Append to file and rebuild                             │
│    - Step 4: Verify: python3 is_test_case_useful.py                 │
│    - Step 5: Accept (if coverage+) or SKIP (with specific reason)   │
│  - Document exploration summary and per-test results                │
│  - FORBIDDEN: Skipping all tests with "too complex" excuse          │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 3: FINAL REPORT                                              │
│  - Run: python3 get_current_coverage.py <TEST_FILE_PATH>            │
│  - Calculate coverage change and generate summary                   │
│  - HARD GATE: Final coverage MUST be >= Initial coverage            │
│    (otherwise REVERT last accepted changes and mark as FAILED)      │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Concepts

### Test File Path Extraction

From review file, extract the test file path:
```
Review: /path/smart-tests/aot-1/enhanced_aot_runtime_test_review.md
Test file: /path/smart-tests/aot-1/enhanced_aot_runtime_test.cc
           ↑ remove "_review.md", add ".cc"
```

### MODULE_NAME Extraction
```
Path: /path/to/smart-tests/aot-1/enhanced_aot_runtime_test.cc
                           ↑
                      MODULE_NAME = "aot-1"
```

### Output Document

Create: `<TEST_FILE>_fix.md` in the same directory as the test file.

**Naming pattern**:
```
Test file: enhanced_aot_runtime_test.cc
Output:    enhanced_aot_runtime_test_fix.md
```

### Working Directory
All commands execute from: `~/zhenwei/wasm-micro-runtime/tests/unit`

## Detailed Workflow

### PHASE 0: Initialization

```bash
cd ~/zhenwei/wasm-micro-runtime/tests/unit

# Get initial coverage (RECORD THIS!)
python3 get_current_coverage.py <TEST_FILE_PATH>

# Build if needed
cmake --build build/smart-tests/<MODULE_NAME> 2>&1 | tail -15
```

**Create output file** following the EXACT format in "CRITICAL: OUTPUT FORMAT" above.

---

### PHASE 0.25: Redundancy Cleanup (enforced by coverage gate)

**Goal**: Remove truly redundant tests (0 incremental coverage) while guaranteeing overall coverage does not regress.

```bash
# 0.25.1 Run redundancy checker (deterministic tool output)
./check_redundant_tests.sh <MODULE_NAME> <TEST_FILE_PATH>

# 0.25.2 Delete redundant tests in bulk (if any)
python3 delete_test_cases.py <TEST_FILE_PATH> /tmp/<BASENAME>_redundant_check.md

# 0.25.3 Rebuild after deletion
cmake --build build/smart-tests/<MODULE_NAME> 2>&1 | tail -15

# 0.25.4 Coverage gate: MUST NOT drop vs INITIAL
python3 get_current_coverage.py <TEST_FILE_PATH>
```

**Accept/Reject**:
- If coverage **drops** vs INITIAL → **REVERT** the file to pre-cleanup state and record as ❌ FAILED (coverage regression)
- If coverage **maintained or improved** → keep changes and record deletions in Phase 0.5 table (Action=Deleted)

### PHASE 0.5: Quality Fix (from review + safety scan)

**Goal**: Apply quality fixes based on review findings, plus a quick safety scan to catch missed issues.

| Issue Type | Pattern | Action |
|------------|---------|--------|
| Invalid assertion | `ASSERT_TRUE(true)` | Replace or delete test |
| Placeholder | `SUCCEED()`, `FAIL()`, `GTEST_SKIP()` | Delete test |
| Empty test | `TEST_F(...) { }` | Delete test |
| No assertions | Test without ASSERT/EXPECT | Delete test |
| Outdated comments | Wrong line numbers | Remove comment |

**Record all fixes in output document's Phase 0.5 table.**

---

### RE-FIX Mode (Closed-Loop Iteration)

When invoked for RE-FIX (typically because Compliance < 100% in `*_verify.md`):

1. Read verify report → find items marked ❌ Non-compliant or 🔍 Missing
2. Read previous fix report → understand what was already attempted
3. Focus ONLY on non-compliant items
4. APPEND new entries to fix report (do not overwrite)

**Add RE-FIX section to output**:
```markdown
---
## RE-FIX Iteration N

**Triggered by**: Compliance < 100%
**Non-compliant items**: N

| Item | Verify Issue | Action | Result |
|------|--------------|--------|--------|
| test_1 | Not renamed | Renamed | ✅ |
```

### PHASE 1: Fix Alignment Issues

For each test with `Alignment: NO` in review:

1. **Read** the recommendation from review
2. **Apply** fix (rename / modify assertion / add setup)
3. **Rebuild**: `cmake --build build/smart-tests/<MODULE_NAME> 2>&1 | tail -10`
4. **Verify**: `python3 is_test_case_useful.py <TEST_FILE> <TEST_CASE>`
5. **Accept/Reject**:
   - Coverage maintained/improved → ✅ FIXED
   - Coverage dropped (per-test OR overall gate) → ❌ FAILED (revert changes)
   - Needs manual redesign → ⏭️ SKIPPED

**Record each fix in output document's Phase 1 section.**

### PHASE 2: Generate New Test Cases

**⚠️ MANDATORY BEHAVIOR - NO BATCH SKIPPING ALLOWED**

You MUST attempt to generate EVERY suggested test case from review. NEVER skip entire Phase 2 with generic excuses.

**Required workflow for EACH suggested test:**

**Step 1: Pattern Exploration (MANDATORY)**
- Use Grep to search for similar test patterns in the same test file
- Use Grep to search for similar test patterns in other test files in the module
- Read at least 2 similar existing tests to understand the setup pattern
- Document the pattern found (e.g., "Found AOTModule setup pattern in enhanced_aot_runtime_test.cc:47-60")

**Step 2: Code Generation**
- Generate test code following the patterns discovered in Step 1
- Reuse existing helper structures, fixtures, and utility functions
- If the suggested test requires data (e.g., AOT module bytes):
  - Search for existing data files: `find . -name "*.aot" -o -name "*_aot.h"`
  - Check if other tests in the file use embedded byte arrays or external files
  - Reuse existing test data when possible

**Step 3: Implementation**
1. **Generate** test code following discovered patterns
2. **Append** to test file
3. **Rebuild**: `cmake --build build/smart-tests/<MODULE_NAME> 2>&1 | tail -10`
4. **Verify**: `python3 is_test_case_useful.py <TEST_FILE> <NEW_TEST_CASE>`

**Step 4: Accept/Reject Decision**
- Coverage improved (new lines > 0) AND overall gate not dropped → ✅ ADDED
- No coverage contribution after implementation → ⏭️ SKIPPED (delete test case)
- Build fails with technical blocker → ⏭️ SKIPPED (document specific error)

**Step 5: Documentation**
Record each new test in output document's Phase 2 table with:
- Test name
- Result (✅ ADDED / ⏭️ SKIPPED)
- If SKIPPED: specific technical reason (see valid reasons below)

---

**VALID Skip Reasons (specific technical blockers only):**

✅ **Acceptable SKIP reasons:**
- "Requires mocking runtime_malloc, no mock framework configured in CMakeLists.txt"
- "Build fails: undefined reference to aot_internal_function (not exported)"
- "Coverage verification shows 0 new lines covered after successful build"
- "Requires external .aot file not present in wasm-apps directory"
- "Function signature not found in any header file (grep returned no results)"

❌ **INVALID Skip Reasons (too vague, not allowed):**
- "Too complex" → Must specify WHAT is complex
- "Requires AOT module setup" → Must ATTEMPT using existing patterns first
- "Beyond simple fixes" → Phase 2 is ABOUT adding new code
- "Need more investigation" → You must investigate NOW, not skip
- Skipping entire Phase 2 without trying individual tests → FORBIDDEN

---

**Example Phase 2 output (GOOD):**

```markdown
## Phase 2: New Test Cases

### Exploration Summary
- Searched for AOTModule setup patterns: Found in enhanced_aot_runtime_test.cc:47-48
- Searched for AOT test data: Found test_aot.h in ../aot-stack-frame/wasm-apps/
- Read similar test: enhanced_aot_runtime_test.cc:45-80 (shows AOTModule initialization)

| Test Case | Target Function | Action Taken | Result | Reason |
|-----------|-----------------|--------------|--------|--------|
| `aot_get_global_addr_InvalidGlobalIndex` | `aot_get_global_addr` | Generated, built, verified | ✅ ADDED | +15 lines coverage |
| `aot_set_aux_stack_ValidStackSize` | `aot_set_aux_stack` | Generated, built, verified | ⏭️ SKIPPED | 0 new lines (function already fully covered) |
| `malloc_failure_linear_search` | `aot_lookup_function` | Generated, build failed | ⏭️ SKIPPED | Requires mocking runtime_malloc (no mock framework) |
```

---

**Enforcement Rules:**

1. ❌ You CANNOT skip all suggested tests with a single excuse
2. ✅ You MUST attempt pattern exploration for each suggestion
3. ✅ You MUST document specific technical blockers for skipped tests
4. ✅ You MUST try at least 80% of suggested tests (unless valid technical blockers exist)

### PHASE 3: Final Report

```bash
python3 get_current_coverage.py <TEST_FILE_PATH>
```

**Update output document**: Fill in the Coverage Summary table and Summary table following the format in "CRITICAL: OUTPUT FORMAT" above.

**HARD GATE (MANDATORY)**:
- Final coverage MUST be >= Initial coverage (Lines and Functions)
- If Final < Initial: revert the last accepted change set(s) until the gate passes, otherwise mark the offending items as ❌ FAILED

## Constraints

### ✅ MUST DO
1. Record initial coverage BEFORE modifications
2. Verify coverage after EACH modification
3. Existing test fixes: Accept if coverage NOT dropped
4. New test cases: Accept ONLY if coverage improved
5. Revert/remove changes that don't meet criteria
6. Record final coverage AFTER modifications
7. Use CONCISE output format (tables, not paragraphs)
8. Enforce overall coverage gate: Final MUST be >= Initial
9. **PHASE 2 MANDATORY: Explore patterns BEFORE claiming "too complex"**
10. **PHASE 2 MANDATORY: Attempt EVERY suggested test individually**
11. **PHASE 2 MANDATORY: Document specific technical blocker for each skip**

### ❌ MUST NOT DO
1. Skip coverage verification
2. Keep modifications that reduce coverage
3. Keep new tests that don't add coverage
4. Write long paragraphs or code blocks in output
5. Skip any test case or suggestion from review without specific technical reason
6. **Skip entire Phase 2 with vague excuses like "too complex" or "requires setup"**
7. **Claim a test is impossible without first exploring existing test patterns**
8. **Use generic skip reasons - each skip must have specific error messages or technical details**

## Quick Reference

```bash
# Working directory
cd ~/zhenwei/wasm-micro-runtime/tests/unit

# Get coverage
python3 get_current_coverage.py <TEST_FILE>

# Check if test case useful
python3 is_test_case_useful.py <TEST_FILE> <TEST_CASE_NAME>

# Build module
cmake --build build/smart-tests/<MODULE_NAME> 2>&1 | tail -15

# Extract test case
awk '/TEST_F\(Suite, Test\)/,/^}$/' file.cc
```

