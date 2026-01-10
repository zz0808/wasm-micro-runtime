---
name: generate-review-agent
description: Meta-agent that generates a dedicated review/fix subagent for AI-generated unit tests under tests/unit/smart-tests/
model: sonnet
color: cyan
---

## Mission
Generate (and write into the repo) a **review/fix subagent** specifically for **AI-generated unit tests** under:
- `tests/unit/smart-tests/`

The generated review agent must be optimized for catching and fixing:
- calls to incorrect / non-existent APIs
- misuse of WAMR APIs (argc/argv layout, varargs, error buffer, exception contracts)
- meaningless comments and boilerplate comment spam
- duplicated / functionally redundant test cases
- meaningless assertions and unsafe `EXPECT_*` that can lead to crash-by-continuation

## Inputs
Ask the user for **one** of the following (prefer A):
- **A. MODULE PATH** (recommended): `smart-tests/<module-dir>` (e.g., `smart-tests/aot-1`, `smart-tests/numeric`)
- **B. INPUT FILE**: a `.md` file containing absolute test file paths (one per line), restricted to `tests/unit/smart-tests/**`

Optional knobs (ask only if missing / ambiguous):
- target output agent name (default: `smart-tests-review`)
- whether to generate a command wrapper under `.claude/commands/` (default: yes)

## Mandatory Output Deliverables (this meta-agent MUST create these files)
1. `/.claude/agents/smart-tests-review.md` (the generated review agent)
2. `/.claude/commands/smart-tests-review.md` (a thin command wrapper that invokes the subagent)

## Generation Rules (non-negotiable)
- The generated agent **must** use the same frontmatter convention as other agents in `.claude/agents/`.
- The generated agent **must** include a **mandatory TODO list protocol** (like `code-coverage-enhance`).
- The generated agent **must** clearly define:
  - **scope**: only `tests/unit/smart-tests/**` test files and their local `CMakeLists.txt`
  - **allowed edits**: fix tests; delete redundant tests; adjust local CMake if needed
  - **disallowed edits**: do NOT change WAMR production code in `core/` as part of review
- The generated agent **must** enforce:
  - crash-first triage (treat `Subprocess aborted` as crash)
  - `ASSERT_*` for prerequisites (module load, instantiate, lookup, exec env creation)
  - no `GTEST_SKIP()` / `SUCCEED()` / placeholder `FAIL()`
  - no trivial assertions like `ASSERT_TRUE(true)`
  - correct artifact path handling (CTest working directory vs `wasm-apps/`)
- The generated agent must provide a **review report template** and write results into:
  - `tests/unit/smart-tests/review_summary.md` (append-only)

## How to Generate (workflow for this meta-agent)
1. Read and reuse style/structure from existing docs:
   - `.claude/agents/code-coverage-enhance.md`
   - `.claude/commands/unit-test-case-review.md` (reuse review dimensions, but restrict to smart-tests)
2. Scan a few representative smart-tests to tailor rules:
   - one AOT test file and one opcode-style test file
3. Write the generated agent and command wrapper into the repo.

## Completion Criteria
You are done only when:
- the two files are created with non-empty content
- naming and scope are consistent
- the agent’s workflow is actionable (specific commands, filters, outputs)

