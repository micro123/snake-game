# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Classic Snake game built with Pygame. Single-player, keyboard-controlled, grid-based movement.

## Commands

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

## Architecture

```
main.py          # Entry point — initializes pygame, runs main loop
requirements.txt # Python dependencies
```

- **Pygame**: Graphics rendering, event handling (keyboard input, window events)
- **Grid-based movement**: Snake moves on a fixed cell-size grid
- **Fixed window**: 800×600 pixels, non-resizable
- **Virtual env**: `venv/` (gitignored) for isolated package management

## Claude Code Workflow System

This repo uses a structured, multi-agent development workflow. The **main agent orchestrates** — it does NOT directly write source code, run `git add`, `git push`, `git commit --amend`, `git reset --hard`, or execute Node.js inline code with write effects. All code modifications are delegated to the **developer** sub-agent.

### Available Commands (Slash Commands)

- **`/bug-fix`** — 3-phase bug fix workflow: Bug Analysis → Solution Design & Evaluation → Implementation. Usage: `phase:1 bugId:<id> bugDescription:<desc>`. Each phase stops for user review before proceeding.
- **`/feature-dev`** — 5-phase feature development workflow: Requirements Analysis → High-Level Design → Detailed Design → Evaluation & Scheduling → Implementation. Usage: `phase:1 featureName:<name> featureDescription:<desc>`.
- **`/code-submit`** — Single-phase commit workflow: generates a commit message from staged changes. The main agent then handles confirmation via AskUserQuestion and executes `git commit` (no push). Usage: `phase:1 [type:feat|fix|refactor|docs|chore|perf|test|style] [scope:...]`.

### Sub-Agent Roles

| Agent | Role | Has Write Access |
|---|---|---|
| `developer` | Code implementation, testing, `git add` staging | Yes (only role with write permission) |
| `code-analyst` | Trace bug root causes through code exploration | Read-only |
| `bug-triage-engineer` | Convert raw bug reports into structured bug reports | `.claude/` config only |
| `requirements-analyst` | Convert vague user needs into structured requirements | `.claude/` config only |
| `requirements-engineer` | Write formal requirement specs from requirements definitions | `.claude/` config only |
| `software-architect` | System architecture design, technology selection | `.claude/` config only |
| `senior-developer` | Detailed design: class structure, API endpoints, data models | `.claude/` config only |
| `solution-designer` | Design fix plans and test plans based on root cause analysis | `.claude/` config only |
| `project-manager` | Break designs into ordered dev tasks, define milestones | `.claude/` config only |
| `tech-lead` | Evaluate difficulty/risk/priority, effort estimation | `.claude/` config only |
| `code-submitter` | Read staged changes and process docs, generate commit messages | Read-only |

### Hooks in Place

- **`block-main-writes.js`** (PreToolUse on Write/Edit/NotebookEdit): Main agent can only write to `.claude/` config paths. All other file writes must go through the developer sub-agent.
- **`block-node-writes.js`** (PreToolUse on Bash): Blocks `node -e` inline code containing write-effect APIs (writeFile, mkdir, exec, etc.). Main agent can only run read-only Node.js one-liners.

### Git Safety Rules

The main agent is denied: `git push`, `git reset --hard`, `git commit --amend`, `git clean -fd`, `git checkout --`. Commit workflow: developer stages changes → `/code-submit` generates message → main agent confirms with user → main agent runs `git commit` (no push).

### Workflow Scripts

Workflow implementations live in `.claude/workflows/`:
- `bug-fix.workflow.js`
- `feature-dev.workflow.js`
- `code-submit.workflow.js`

Each workflow runs via `Workflow({scriptPath: "..."})` and orchestrates multiple sub-agents in sequence with deterministic control flow.
