---
inclusion: always
---

# Dependency Management Conventions

- Do NOT use Python virtual environments (venv). Install packages globally to save space.
- All Python dependencies go in `requirements.txt` at the project root, sorted alphabetically.
- Install/update with: `pip install -U -r requirements.txt`
- When adding new dependencies, append to `requirements.txt` and re-sort alphabetically.
- Always verify installs by importing the key packages after installation.
