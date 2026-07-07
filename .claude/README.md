# Claude Code Workflow Infrastructure

This directory contains reusable multi-agent workflow infrastructure for Claude Code. Copy it to any new project to enable structured development workflows.

## Contents

| Directory | Purpose |
|-----------|---------|
| `agents/` | 11 specialized sub-agent definitions (developer, code-analyst, software-architect, etc.) |
| `commands/` | 3 slash commands: `/bug-fix`, `/feature-dev`, `/code-submit` |
| `workflows/` | Workflow scripts orchestrating multi-phase development processes |
| `hooks/` | PreToolUse hooks enforcing main-agent write restrictions |
| `settings.json` | Permissions and hook configuration |

## New Project Setup

1. Copy `.claude/` to the new project root
2. Run `/init` to generate the project-specific `CLAUDE.md`
3. Ensure `.gitignore` includes these patterns:

```gitignore
# Claude Code workflow state files (internal artifacts)
docs/**/.phase*.json
```

Workflow phase state files (`.phase*.json`) are internal cross-phase persistence artifacts. Only human-readable `.md` process documents belong in version control.
