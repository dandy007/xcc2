# Agent Guidelines (`AGENTS.md`)

This repository is configured for collaboration between human developers and AI coding agents. All agents working in this repository should adhere to the following principles and conventions.

---

## 1. Project Overview
- **Project Name:** `xcc2`
- **Description:** [TBD: Describe project purpose and scope]
- **Tech Stack:** [TBD: Define primary languages, frameworks, and runtime]

---

## 2. General Principles & Behavioral Guidelines
- **Verification First:** Never declare a task complete without executing verification steps (tests, builds, linter checks).
- **Minimal & Focused Diffs:** Keep changes scoped strictly to the user request. Do not reformat or refactor unrelated code.
- **Documentation & Comments:** Preserve existing comments and docstrings unless explicitly asked to modify them. Update documentation when behavior changes.
- **Safe Execution:** Do not bypass security boundaries, suppress errors without clear cause, or make destructive modifications without user confirmation.

---

## 3. Workflow
1. **Analyze:** Understand existing code structure, requirements, and constraints.
2. **Plan:** For non-trivial modifications, outline the approach before editing.
3. **Implement:** Write idiomatic, clean, and well-typed code.
4. **Verify:** Run available tests, lint checks, and compiler/build steps.
5. **Report:** Provide concise summaries of what was done and what (if anything) requires user attention.

---

## 4. Code & Git Conventions
- **Code Style:** Follow language-specific idiomatic conventions and existing repository patterns.
- **Commit Messages:** Follow [Conventional Commits](https://www.conventionalcommits.org/):
  - `feat:` New features
  - `fix:` Bug fixes
  - `refactor:` Code refactoring without changing behavior
  - `test:` Adding or updating tests
  - `docs:` Documentation changes
  - `chore:` Maintenance and build configuration
- **Language Policy:**
  - Code, identifiers, comments, and commit messages in **English**.
  - Direct communication with the user in their preferred language (e.g., **Czech**).

---

## 5. Build, Test & Lint Commands
*(Update this section once project tooling is set up)*

- **Install dependencies:** `TBD`
- **Build / Compile:** `TBD`
- **Run tests:** `TBD`
- **Lint / Format:** `TBD`
