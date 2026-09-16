---
name: do-ops
description: Index and auth for DigitalOcean work. Start here to pick the right DO skill, verify which team doctl is pointed at, and call the v2 API directly. Routes to do-spaces, do-apps, do-dns, do-databases, do-droplets, do-registry. Use for any DigitalOcean task, or when unsure which one applies.
user-invocable: true
argument-hint: "[auth|context|api]"
---

# DigitalOcean Ops

Quick reference for agents working with DigitalOcean infrastructure. `doctl` is pre-authenticated on this machine.

> **Destructive actions (delete, destroy, reset, create) require operator approval. Read-only ops (list, get, logs) are always safe.**

## Which skill

| Task | Skill |
|------|-------|
| Files, buckets, uploads, CDN | `/do-spaces` |
| App Platform deploys, logs, specs, static sites | `/do-apps` |
| Domains, DNS records, nameservers | `/do-dns` |
| Managed Postgres, MySQL, Valkey, pools | `/do-databases` |
| VMs, SSH, images, sizes | `/do-droplets` |
| Container images, tags, garbage collection | `/do-registry` |

Each one is standalone. Read this skill first only when you need auth, contexts, or the raw API.

---

## Auth Setup

Two separate auth systems. Don't mix them up:

| Tool | Auth | Used For |
|------|------|----------|
| `doctl` | OAuth token, pre-configured | Infrastructure (droplets, apps, DNS, DBs) |
| AWS CLI | Spaces key/secret from `.env` | Spaces file operations |

```bash
# Verify doctl auth AND which team you are pointed at
doctl account get
doctl auth list          # the starred/current context is the one every command hits

# Switch teams before touching anything
doctl auth switch --context <name>
doctl compute droplet list --context <name>   # or override per-command

# Load Spaces credentials before any aws s3 command
source ~/.env
# Provides: DO_TOKEN, DO_SPACES_KEY, DO_SPACES_SECRET, DO_SPACES_ENDPOINT,
#           DO_SPACES_BUCKET, DO_SPACES_CDN (hostname), DO_SPACES_CDN_ID (uuid)
```

Direct API calls when `doctl` doesn't cover something:
```bash
source ~/.env
curl -X GET "https://api.digitalocean.com/v2/<resource>" \
  -H "Authorization: Bearer $DO_TOKEN" \
  -H "Content-Type: application/json"
```

---

## Gotchas

These apply everywhere. Product-specific gotchas live in their own skill.

**`doctl` has multiple auth contexts and no confirmation prompt.** Run `doctl auth list` first. The current context is the team every command hits, so a `delete` against the wrong context destroys another team's resources. Pass `--context <name>` when in doubt.

**`doctl` vs AWS CLI are separate auth systems.** `doctl` auth doesn't give Spaces access. Spaces needs `DO_SPACES_KEY`/`DO_SPACES_SECRET`, not `DO_TOKEN`.

**Tag resources with project name** for cost tracking:
```bash
doctl compute droplet create <name> --tag-names my-project
```

**`doctl` self-reports when it is stale.** If a documented flag is missing, check `doctl version` against the release it prints and run `brew upgrade doctl`.
