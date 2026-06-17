

## Local Project Handoff

Before starting a new work session in this repository, read `docs/project/next_session_prompt.md`.
It contains the current startup order, local Python environment notes, and the continuation prompt for this project.

## Server Process Rule

Do not start long-running servers such as `uvicorn`, `cloudflared`, or `python3 -m http.server` in hidden/background Codex sessions. When a server or tunnel is needed, use a new visible editor terminal so the user can see logs and stop the process.

## Path Rule

Use repository-relative paths in project code, docs, examples, and prompts. Do not commit machine-specific absolute paths such as `/Users/...`, `~/Desktop/...`, `/home/...`, or temporary local paths. When a command needs a working directory, say to run it from the project root or use relative paths.

## Commit Message Rule

When committing work in this repository, write commit messages in Korean and summarize the change clearly.
Prefer a concise subject plus a short body when the commit includes multiple areas such as API, data, tests, and docs.
