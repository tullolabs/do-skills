# do-ops

A DigitalOcean operations cheatsheet skill for AI agents (OpenClaw-compatible).

Covers auth, Spaces file ops, Droplets, App Platform, Databases, DNS, and common gotchas that cause agents to hit debugging loops.

## Install

```bash
cp -r . ~/.agents/skills/do-ops/
```

## What's inside

- `doctl` + AWS CLI auth setup
- Spaces file operations with exact inline commands
- Bucket structure conventions
- Droplets, App Platform, Databases, DNS — practical commands
- Common gotchas (wrong region, separate auth systems, CDN vs raw URLs, wrong `doctl` auth context, etc.)

Verified against `doctl` 1.167 and the DigitalOcean docs as of September 2026.
