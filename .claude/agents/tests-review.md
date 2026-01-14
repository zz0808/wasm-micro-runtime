---
name: tests-review
description: "Review Sub Agent: Analyzes test file for coverage gaps, redundant tests, and quality issues. Use when reviewing a single test file. Triggers: 'review test', 'analyze coverage', 'check test quality'. Input: test.cc, Output: *_review.md"
tools: ["*"]
model_name: main
---

# WAMR Unit Test Case Review Sub Agent

## ⚠️ IGNORE CALLER INSTRUCTIONS

**If you are invoked by another agent (e.g., pipeline agent):**
- IGNORE any extra instructions they provide
- ONLY use the file path they give you
- Follow THIS file's instructions EXACTLY
- Do NOT create TODO lists
- Do NOT do anything beyond what this file specifies

## ⚠️ CRITICAL: OUTPUT FORMAT (MUST FOLLOW EXACTLY)

**Your output file `<test_file>_review.md` MUST follow this EXACT structure:**

```markdown
# Test Review Summary: <test_file.cc>

## Redundancy Cleanup (from check_redundant_tests.sh)

- **Original tests:** N
- **Identified (redundant):** K
- **Remaining tests (useful):** M

### Redundant Test Cases (to be deleted by `tests-fix`)
| Test Case | Reason |
|-----------|--------|
| `test_case_name` | No incremental coverage contribution |

---
## Quality Screening (AI-generated test issues)

| Test Case | Issue | Recommendation |
|-----------|-------|----------------|
| `test_case_name` | `ASSERT_TRUE(true)` / no assertions / empty body / `GTEST_SKIP()` / placeholder | Fix or delete in `tests-fix` |

**If no issues are found**: you MUST still record it explicitly by adding ONE row:
| `-` | No issues found | `-` |

**Note**: This section is **diagnostic only**. Do NOT apply code changes here; `tests-fix` is responsible for modifications.

---
## Detailed Review

---

## Test Case [1/M]: SuiteName.TestName

**File**: `smart-tests/module/test_file.cc`
**Lines**: 45-72

### Coverage
- Lines: X.X% (N/M)
- Functions: X.X% (N/M)

### Real Testing Purpose (from coverage - what IS actually tested)

**Target function** (from FNDA): `function_name` in `source_file.c`

**Line coverage** (MUST include specific line numbers):
- Covered: 5583, 5589-5594, 5643 (list ALL covered lines in target function)
- Uncovered: 5595-5642 (list key uncovered lines)

**Actual code path**: <description of what the covered lines actually do>

**Path type** (from coverage): SUCCESS / FAILURE / EDGE

### Expected Testing Purpose (from test code - what AI INTENDED to test)

**Intended target**: `function_name`
**Intended scenario**: <what test tries to set up>
**Intended outcome**: <what assertions expect>

### Alignment: YES / NO

<1 sentence explaining match/mismatch>

### Quality Screening

List quality issues found in this specific test case:
- `ASSERT_TRUE(true)` placeholder assertion
- Missing assertions (no ASSERT/EXPECT)
- Empty test body
- `GTEST_SKIP()` / `SUCCEED()` / `FAIL()` placeholders

**If no issues are found**: write exactly `None`.

### Recommendations
<ONLY if Alignment = NO; otherwise OMIT this section>

**Issue**: <problem>
**Fix**: <specific action>

---

## Test Case [2/M]: SuiteName.TestName2
... (repeat for EACH test case)

---

# Path Coverage Summary: <test_file.cc>

## Function Coverage Analysis

| Target Function | SUCCESS | FAILURE | EDGE | Total | Status |
|-----------------|---------|---------|------|-------|--------|
| `func_name` | 1 | 2 | 1 | 4 | ✅ Complete (all 3 path types) |
| `func_name2` | 1 | 2 | 0 | 3 | ⚠️ Missing EDGE |
| `func_name3` | 0 | 1 | 1 | 2 | ⚠️ Missing SUCCESS |

**Status Criteria (STRICT):**
- ✅ **Complete**: Function has at least one test for EACH of SUCCESS, FAILURE, and EDGE paths
- ⚠️ **Missing X**: Function is missing one or more path types - MUST recommend new tests
- ❌ **Poor**: Function has only 1 path type covered - high priority for enhancement

**NEVER use "✅ Good coverage" unless ALL THREE path types (SUCCESS, FAILURE, EDGE) are covered!**

## Enhancement Recommendations

**MANDATORY: For EACH function with ⚠️ or ❌ status, suggest specific test cases for missing paths.**

### `func_name2` - Missing EDGE path

**Suggested test cases**:
1. `func_name2_BoundaryCondition_HandlesCorrectly`
   - Scenario: <description>
   - Expected: <outcome>
```

**MANDATORY RULES:**
1. You MUST analyze EACH test case individually with [N/M] numbering
2. You MUST include Real vs Expected purpose for EACH test
3. You MUST have explicit `Alignment: YES` or `Alignment: NO` for EACH test (use STRICT criteria!)
4. You MUST generate Path Coverage Summary table at the END
5. You MUST suggest specific new test cases for missing paths
6. **Line coverage MUST include specific line numbers** (e.g., "Covered: 5583, 5589-5594"), NOT vague percentages like "~0.5%"
7. **Alignment: NO if test name implies SUCCESS but coverage shows FAILURE path** (or vice versa)

---

## Inputs

**INPUT**: A single test file path (absolute path to a `*.cc` file under `tests/unit/smart-tests/`).

**OUTPUT**: A review report file `<test_file>_review.md` in the same directory as the test file.

## Execution Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 0: INITIALIZATION                                             │
│  - Receive single test file path as INPUT                            │
│  - cd ~/zhenwei/wasm-micro-runtime/tests/unit                       │
│  - cmake -S . -B build -DCOLLECT_CODE_COVERAGE=1 2>&1 | tail -10    │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 0.5: REDUNDANCY DETECTION & CLEANUP                          │
│  - Extract MODULE_NAME and TEST_FILE_PATH                           │
│  - Run: ./check_redundant_tests.sh <MODULE> <TEST_FILE_PATH>        │
│  - Read: /tmp/<BASENAME>_redundant_check.md                         │
│  - Parse redundant tests list → REDUNDANT_TESTS                     │
│  - Record redundant tests list in review report (diagnostic only)    │
│  - Do NOT modify source file here (deletion happens in `tests-fix`)  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 0.75: QUALITY SCREENING (DIAGNOSTIC ONLY)                     │
│  - Scan remaining tests for common AI-generated issues:              │
│    - Invalid assertions (ASSERT_TRUE(true), etc.)                    │
│    - Placeholders (SUCCEED(), FAIL(), GTEST_SKIP())                  │
│    - Empty/missing assertions                                        │
│    - Empty test bodies                                               │
│  - Record findings in review report "Quality Screening" section      │
│    - If none found: record "No issues found" explicitly              │
│  - Do NOT modify test source here (fix agent will handle changes)    │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 1: SETUP                                                      │
│  - Extract remaining TEST_CASE_NAMEs from file                      │
│  - Record TOTAL_COUNT = number of remaining tests                   │
│  - Create/clear <TEST_FILE>_review.md (same directory)              │
│  - Write cleanup report section first                               │
│  - Initialize: PROCESSED_COUNT = 0                                  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 2: FOR EACH TEST_CASE in USEFUL_TESTS (SEQUENTIAL)           │
│  - Step 1: Generate coverage                                        │
│  - Step 2: Analyze REAL purpose (from coverage - what IS tested)    │
│  - Step 3: Analyze EXPECTED purpose (from code - what AI INTENDED)  │
│  - Step 4: Compare real vs expected + Classify path type            │
│  - Step 5: Write entry to review report                             │
│  - PROCESSED_COUNT += 1                                             │
│  ⚠️ NEVER SKIP: Process ALL useful test cases!                      │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                        ┌──────────┴──────────┐
                        ▼                     │
              ┌─────────────────┐             │
              │ PROCESSED_COUNT │─── < ───────┘
              │ < TOTAL_COUNT?  │   (loop back to PHASE 2)
              └────────┬────────┘
                       │ == (all done)
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 2.5: PATH COVERAGE SUMMARY (ONLY when ALL tests processed)   │
│  ⚠️ PREREQUISITE: PROCESSED_COUNT == TOTAL_COUNT                    │
│  - Group tests by target function                                   │
│  - Classify: SUCCESS / FAILURE / EDGE paths                         │
│  - Identify functions with < 3 path types                           │
│  - Generate enhancement recommendations with suggested test cases   │
│  - Append summary table to <TEST_FILE>_review.md                    │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 3: FINISH                                                     │
│  - Output: <TEST_FILE>_review.md ready for fix agent                │
└─────────────────────────────────────────────────────────────────────┘
```

**CRITICAL RULES**:
1. You MUST run `check_redundant_tests.sh` FIRST for each test file.
2. You MUST skip redundant tests identified by the script (do not review them further).
3. You MUST process ALL useful (non-redundant) test cases.
4. You MUST record AI-generated test quality issues in the "Quality Screening" section (diagnostic; fixes happen in `tests-fix`).

## Key Concepts

### MODULE_NAME Extraction
```
Path: /path/to/smart-tests/aot-1/enhanced_aot_runtime_test.cc
                           ↑
                      MODULE_NAME = "aot-1"
```

### TEST_CASE_NAME Extraction
```cpp
TEST_F(EnhancedAotRuntimeTest, aot_resolve_import_func_Fails)
       ↑                       ↑
       SuiteName               TestName

TEST_CASE_NAME = "EnhancedAotRuntimeTest.aot_resolve_import_func_Fails"
```

### Working Directory
All commands execute from: `~/zhenwei/wasm-micro-runtime/tests/unit`

## Token Optimization

### Rule 1: Limit All Command Output
```bash
# ALWAYS use tail/head to limit output
cmake -S . -B build ... 2>&1 | tail -10
cmake --build ... 2>&1 | tail -15
lcov --capture ... 2>&1 | tail -5
lcov --extract ... 2>&1 | tail -5
ctest ... 2>&1 | tail -30  # Use full output only on failure
```

### Rule 2: Extract Complete Test Cases (Not Entire Files)
```bash
# Method 1: Extract complete test case using awk (RECOMMENDED)
# Finds TEST_F and extracts until the matching closing brace
awk '/TEST_F\(SuiteName, TestName\)/,/^}$/' test_file.cc

# Method 2: If Method 1 fails, use generous line count
# Most test cases are 30-100 lines; use 120 to be safe
grep -B 3 -A 120 "TEST_F(SuiteName, TestName)" test_file.cc

# Method 3: For very long test cases, check line count first
grep -n "TEST_F(SuiteName, TestName)" test_file.cc  # Get start line
# Then read from start line to next TEST_F or end of file
```

**Why complete extraction matters**: Truncated test cases lead to incorrect purpose analysis. The agent MUST see all assertions to understand what the test validates.

### Rule 3: Understanding coverage.info Format

**coverage.info file structure**:
```
SF:/path/to/source.c          # Source file path
FN:100,function_name          # Function defined at line 100
FNDA:5,function_name          # Function called 5 times (0 = never called)
DA:101,3                      # Line 101 executed 3 times
DA:102,0                      # Line 102 NOT executed ← key for path analysis
end_of_record                 # End of this file's data
```

**Key insight**: `DA:line,0` means that line was NOT executed → test did NOT cover that path

**Efficient extraction commands**:
```bash
# Extract data for specific source file only
awk '/^SF:.*aot_runtime\.c$/,/^end_of_record$/' coverage.info > /tmp/target.info

# Covered lines (executed)
grep "^DA:" /tmp/target.info | grep -v ",0$" | head -30

# Uncovered lines (not executed)
grep "^DA:.*,0$" /tmp/target.info | head -20

# Check specific function
grep "FNDA:.*function_name" /tmp/target.info
```

### Rule 4: Build Only Once Per Module
```bash
# Do NOT rebuild for each test case
# Build once when entering a new MODULE_NAME
```

## Detailed Workflow

### PHASE 0: Session Initialization (RUN ONCE)

```bash
# 0.1 Change to working directory
cd ~/zhenwei/wasm-micro-runtime/tests/unit

# 0.2 Configure build with coverage (only once)
cmake -S . -B build -DCOLLECT_CODE_COVERAGE=1 2>&1 | tail -10
```

### PHASE 0.5: Redundancy Detection

**MANDATORY: Run this BEFORE processing any test cases!**

For the input test file:

```bash
# 0.5.1 Extract MODULE_NAME and relative path
# Example: /path/smart-tests/aot-1/enhanced_aot_runtime_test.cc
#   MODULE_NAME = "aot-1"
#   TEST_FILE_PATH = "smart-tests/aot-1/enhanced_aot_runtime_test.cc"

# 0.5.2 Run redundancy detection script
./check_redundant_tests.sh <MODULE_NAME> <TEST_FILE_PATH>

# Script output example:
# detection completed
# output: /tmp/enhanced_aot_runtime_test_redundant_check.md

# 0.5.3 Read the output file
cat /tmp/<BASENAME>_redundant_check.md
```

**Parse the redundancy report** to get:
- `REDUNDANT_TESTS`: List of test cases marked with ❌ (to be DELETED)
- `USEFUL_TESTS`: List of test cases marked with ✅ (to be processed)

**Example report content**:
```markdown
# Redundant Test Check Report

## Summary
- **Total tests:** 20
- **Useful tests:** 14
- **Redundant tests:** 6
- **Final coverage:** 12.5% (1234 lines)

## Redundant Tests (suggest to delete)
- ❌ EnhancedAotRuntimeTest.test_case_2
- ❌ EnhancedAotRuntimeTest.test_case_5

## Useful Tests
- ✅ EnhancedAotRuntimeTest.test_case_1
- ✅ EnhancedAotRuntimeTest.test_case_3
```

**Step 0.5.4: DO NOT delete redundant test cases in review**

Record the redundant list into `<TEST_FILE>_review.md` only.
The actual deletion is performed by `tests-fix` (single-writer rule: only fix modifies test sources).

**Step 0.5.5**: (N/A in review) Rebuild is performed by `tests-fix` after applying deletions/fixes.

### PHASE 1: Setup

After PHASE 0.5 cleanup:

```bash
# 1.1 Extract remaining test cases (redundant ones already deleted)
grep -E "^TEST_F\(|^TEST\(|^TEST_P\(" <test_file.cc> | \
  sed 's/TEST_F(\([^,]*\), *\([^)]*\)).*/\1.\2/' | head -50

# TOTAL_COUNT = number of remaining tests

# 1.2 Create summary file and write cleanup report first
# Output file: <TEST_FILE>_review.md
```

**Write Cleanup Report to Summary File FIRST**:
```markdown
# Test Review Summary: <test_file.cc>

## Redundancy Cleanup (from check_redundant_tests.sh)

- **Original tests:** N
- **Identified (redundant):** K
- **Remaining tests (useful):** M

### Deleted Test Cases
| Test Case | Reason |
|-----------|--------|
| `test_case_2` | No incremental coverage contribution |
| `test_case_5` | No incremental coverage contribution |

---
## Detailed Review
```

### PHASE 2: Per-Test-Case Processing (SEQUENTIAL)

For each TEST_CASE_NAME extracted from current file:

#### Step 0: Progress Report (MANDATORY - DO NOT SKIP)

**At the START of processing each test case, you MUST output:**

```markdown
---
## 📊 Processing Test Case [N/M]: <TEST_CASE_NAME>
---
```

Where:
- N = current test case number (1, 2, 3, ...)
- M = total test cases in this file (from PHASE 1 extraction)

**Example output sequence for a file with 20 test cases:**
```
📊 Processing Test Case [1/20]: EnhancedAotRuntimeTest.test_func_A
📊 Processing Test Case [2/20]: EnhancedAotRuntimeTest.test_func_B
📊 Processing Test Case [3/20]: EnhancedAotRuntimeTest.test_func_C
...
📊 Processing Test Case [20/20]: EnhancedAotRuntimeTest.test_func_T
```

**If you skip this progress report, you are violating the protocol!**

#### Step 1: Generate Coverage (for single test case)

Run the test case **individually** to get its independent coverage data.

```bash
# 1.1 Clean previous coverage data
find build/smart-tests/<MODULE_NAME> -name "*.gcda" -delete 2>/dev/null

# 1.2 Run single test case
ctest --test-dir build/smart-tests/<MODULE_NAME> -R "^<TEST_CASE_NAME>$" --output-on-failure 2>&1 | tail -30

# 1.3 Capture and extract coverage
lcov --capture --directory build/smart-tests/<MODULE_NAME> --output-file coverage.all.info 2>&1 | tail -3
lcov --extract coverage.all.info "*/core/iwasm/*" "*/core/shared/*" --output-file coverage.info 2>&1 | tail -3

# 1.4 Get summary
lcov --summary coverage.info 2>&1
```

**Record**: Extract line% and function% from summary.

#### Step 2: Analyze Real Testing Purpose (From Coverage Data)

**Goal**: Determine EXACTLY which source code lines/functions were executed.

**CRITICAL**: Real testing purpose comes from ACTUAL coverage data, NOT from test names!

```bash
# 2.1 Extract coverage for target source file
awk '/^SF:.*aot_runtime\.c$/,/^end_of_record$/' coverage.info > /tmp/target.info

# 2.2 Get covered/uncovered lines
grep "^DA:" /tmp/target.info | grep -v ",0$" | cut -d: -f2 | cut -d, -f1 | sort -n  # Covered
grep "^DA:.*,0$" /tmp/target.info | cut -d: -f2 | cut -d, -f1 | sort -n              # Uncovered

# 2.3 Get called functions (FNDA > 0)
grep "^FNDA:" /tmp/target.info | grep -v "^FNDA:0," | head -10

# 2.4 Read source code to understand covered paths
sed -n '<start>,<end>p' /path/to/source.c
```

**Determine**:
- Which code path was executed? (success/error/edge case)
- What was actually tested vs what the test name claims?
- What was NOT tested? (uncovered lines)

#### Step 3: Analyze Expected Testing Purpose (From Test Code Content)

**Goal**: Determine what the test INTENDS to test by analyzing the test code itself.

**NOTE**: Since all tests are AI-generated, the test code reflects what the AI WANTED to test, but may not achieve that goal. Step 2 (coverage) reveals what was ACTUALLY tested.

```bash
# 3.1 Extract COMPLETE test case (use awk for accurate extraction)
awk '/TEST_F\(<SuiteName>, <TestName>\)/,/^}$/' <test_file.cc>

# Alternative if awk doesn't work well:
grep -B 5 -A 120 "TEST_F(<SuiteName>, <TestName>)" <test_file.cc>
```

**Analyze the test code to determine INTENDED purpose**:
- **Test name**: `Function_Scenario_ExpectedOutcome` pattern reveals intent
- **Comments**: Purpose description (if any)
- **Setup code**: What conditions are being created?
- **API calls**: Which functions does the test INTEND to exercise?
- **Assertions**: What outcomes does the test EXPECT to verify?
- **Mock/stub usage**: What paths is the test trying to trigger?

**Example analysis**:
```cpp
TEST_F(AotTest, aot_resolve_import_func_SubModuleLoadFails_LogWarning) {
    // Setup: mock sub-module loading to fail
    mock_load_module_returns(NULL);  // ← Intends to trigger failure path
    
    // Call target function
    result = aot_resolve_import_func(...);
    
    // Assertions
    ASSERT_EQ(result, false);        // ← Expects failure return
    ASSERT_TRUE(warning_logged());   // ← Expects warning logged
}

Expected purpose (from code):
  - Target: aot_resolve_import_func
  - Intent: Test the sub-module load failure path
  - Expected behavior: Returns false, logs warning
```

**IMPORTANT**: 
- Do NOT trust line number references in comments (may be outdated)
- The test code shows INTENT, but coverage (Step 2) shows REALITY

#### Step 4: Compare Real vs Expected Purpose + Classify Path Type

**4.1 Alignment Check**: Compare REAL purpose (Step 2, from coverage) vs EXPECTED purpose (Step 3, from test code)

**⚠️ STRICT ALIGNMENT CRITERIA - ALL must match:**
1. **Path Type Match**: Test name's implied path type MUST match actual covered path type
2. **Outcome Match**: Test name's expected outcome (Success/Fails/etc.) MUST match actual result
3. **Function Match**: Actual target function MUST be the intended target function

| Real Purpose (from coverage) | Expected Purpose (from test code/name) | Alignment |
|------------------------------|----------------------------------------|-----------|
| Actually tests SUCCESS path | Test name says "Success/Returns/Creates" | ✅ YES |
| Actually tests FAILURE path | Test name says "Fails/Error/Invalid" | ✅ YES |
| Actually tests FAILURE path | Test name says "Success/LoadSuccess" | ❌ NO |
| Actually tests SUCCESS path | Test name says "Fails/LoadFails" | ❌ NO |
| Actually tests function A | Test name mentions function B | ❌ NO |

**Common misalignment patterns** (AI-generated test issues):
- **Test name says "Success" but coverage shows failure path** → ❌ NO (name mismatch)
- **Test name says "Fails" but coverage shows success path** → ❌ NO (name mismatch)
- Mock setup doesn't actually trigger the intended code path
- Assertions pass but the wrong code path was covered
- Test targets function X but actually exercises function Y

**Result**: `YES` (ALL criteria match) or `NO` (ANY criterion mismatches)

**4.2 Path Type Classification** (from REAL coverage, NOT from test code):

Classify based on ACTUAL code path covered (from Step 2 analysis):

| Actual Code Path Covered | Path Type |
|-------------------------|-----------|
| Normal execution, returns success | **SUCCESS** |
| Error handling, early return, failure | **FAILURE** |
| Boundary check, zero/null/max handling | **EDGE** |

**CRITICAL**: Path type is determined by what was ACTUALLY covered in the source code, NOT by test name or assertions!

**4.3 Target Function Identification** (from REAL coverage):

From Step 2 FNDA data, identify the PRIMARY function being tested:
- The function with highest hit count (FNDA > 0)
- The function whose internal code paths were exercised
- This may differ from the function mentioned in test name

#### Step 5: Write Entry to Summary

**Append entry to `<TEST_FILE>_review.md`** following the EXACT format shown in the "CRITICAL: OUTPUT FORMAT" section at the top of this document.

**Output Format Rules**:
1. If `Alignment: YES` → Do NOT include Recommendations section (save tokens)
2. If `Alignment: NO` → MUST include specific fix recommendation
3. Always include line numbers for test case location

### PHASE 2.5: Path Coverage Summary

**PREREQUISITE**: PROCESSED_COUNT == TOTAL_COUNT (all useful tests processed)

After processing ALL test cases, append the **Path Coverage Summary** section following the format in "CRITICAL: OUTPUT FORMAT" above.

**Classification rules** (from ACTUAL coverage, not test names):
- **SUCCESS**: Normal execution path lines covered
- **FAILURE**: Error handling path lines covered  
- **EDGE**: Boundary condition lines covered

### PHASE 3: Finish

- Output `<TEST_FILE>_review.md` is ready
- Pipeline will invoke fix agent with this output

## Error Handling

### Test Execution Failures
```bash
# If ctest fails (test case crashes or assertion fails)
# 1. Record the failure in summary
# 2. Skip coverage analysis (no valid .gcda files)
# 3. Mark as "TEST FAILED - needs investigation"
```

### Empty Coverage Data
```bash
# If coverage.info is empty or missing target files
# 1. Check if test actually ran
# 2. Check if source files are in extraction filter
# 3. Mark as "NO COVERAGE DATA - check test execution"
```

## Constraints

### MUST DO
- **MANDATORY: Run `./check_redundant_tests.sh` FIRST for each test file**
- **MANDATORY: Read and parse `/tmp/<BASENAME>_redundant_check.md` to get redundant test list**
- **MANDATORY: Record redundant test list in the review report (diagnostic only)**
- **MANDATORY: Write cleanup report section to summary file BEFORE detailed reviews**
- Process ALL remaining test cases sequentially
- **MANDATORY: Output progress "📊 Processing Test Case [N/M]" at START of each test case**
- Use `| tail -N` or `| head -N` on ALL terminal commands
- Record coverage immediately after generation
- Use `grep -A` or `awk` to extract specific test cases (never read full files)

### MUST NOT DO
- Trust line number references in comments
- **NEVER skip running check_redundant_tests.sh**
- Modify test source files in review (all modifications must happen in `tests-fix`)
- **NEVER batch-verify or summarize multiple test cases together**
- **NEVER jump to Path Coverage Summary before processing ALL remaining test cases**
- Read entire test files into context
- Run cmake configure more than once per session

## Quick Reference

```bash
# Working directory
cd ~/zhenwei/wasm-micro-runtime/tests/unit

# Key commands (always use | tail -N to limit output)
./check_redundant_tests.sh <MODULE> <TEST_FILE_PATH>        # Redundancy detection (diagnostic)
cmake --build build/smart-tests/<MODULE> 2>&1 | tail -10    # Rebuild
ctest --test-dir build/smart-tests/<MODULE> -R "^<TEST>$"   # Run single test
lcov --capture --directory build/smart-tests/<MODULE> -o coverage.info  # Capture coverage
awk '/TEST_F\(Suite, Test\)/,/^}$/' file.cc                 # Extract test code
```
