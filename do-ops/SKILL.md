---
name: do-ops
description: DigitalOcean index, auth, and billing. Start here to pick the right DO skill, check which team doctl targets, read account balance and invoices, and call the v2 API directly. Use when unsure which do skill applies.
user-invocable: true
argument-hint: "[auth|context|billing|api]"
---

# DigitalOcean Ops

`doctl` is pre-authenticated on this machine.

> **Destructive actions (delete, destroy, reset, create) require operator approval. Read-only ops (list, get, logs) are always safe.**

## Which skill

| Task | Skill |
|------|-------|
| Files, buckets, uploads, CDN | `/do-spaces` |
| App Platform deploys, logs, specs, static sites | `/do-apps` |
| Domains, DNS records, nameservers | `/do-dns` |
| Managed Postgres, MySQL, Valkey, Kafka, OpenSearch, pools | `/do-databases` |
| VMs, SSH, power, resize, snapshots, autoscale | `/do-droplets` |
| Container images, tags, garbage collection | `/do-registry` |
| Kubernetes clusters, node pools, kubeconfig | `/do-k8s` |
| VPCs, firewalls, load balancers, certs, reserved IPs | `/do-network` |
| Block storage volumes, snapshots, images, NFS | `/do-storage` |
| Serverless functions, namespaces, activations | `/do-functions` |
| Metric alerts and uptime checks | `/do-monitoring` |
| Projects, resource assignment, tags | `/do-projects` |
| Gradient agents, knowledge bases, vector DBs, inference | `/do-ai` |
| Secrets Manager and CSPM security scans | `/do-secrets` |
| Auditing an existing setup for cost, exposure, or missing backups | `/do-audit` |

Each one is standalone. Read this skill first only when you need auth, contexts, billing, or the raw API.

---

## Auth Setup

Two separate auth systems. `doctl` auth grants no Spaces access, and Spaces needs the key pair, never `DO_TOKEN`.

| Tool | Auth | Used For |
|------|------|----------|
| `doctl` | OAuth token, pre-configured | Infrastructure (droplets, apps, DNS, DBs) |
| AWS CLI | Spaces key/secret from `.env` | Spaces file operations |

```bash
# Verify doctl auth AND which team you are pointed at
doctl account get
doctl auth list          # the starred/current context is the one every command hits

# Project-scoped settings from the project's own .env, never ~/.env. All optional,
# none secret. Ask the operator for any that are missing before the first write.
#   DO_CONTEXT    auth context this project deploys to
#   DO_PROJECT    project new resources should be assigned to
#   DO_APP_REPO   owner/repo, App Platform projects only
[ -f .env ] && . ./.env

# Confirm the account before any write. Unset, this silently resolves to whichever
# context is starred, which may be another customer.
: "${DO_CONTEXT:?unset — ask the operator which DO account this project deploys to}"
doctl account get --context "$DO_CONTEXT" --format Email,Status

# Switch teams before touching anything
doctl auth switch --context <name>
doctl compute droplet list --context <name>   # or override per-command

# Manage contexts
doctl auth init --context <name>     # add an account, prompts for a token
doctl auth token                     # print the current context's token
doctl auth remove --context <name>   # (⚠️ requires approval)

# Are we being rate limited
doctl account ratelimit

# Load Spaces credentials before any aws s3 command, without clobbering an existing export
[ -n "$DO_SPACES_KEY" ] || source ~/.env
# Provides: DO_TOKEN, DO_SPACES_KEY, DO_SPACES_SECRET, DO_SPACES_ENDPOINT,
#           DO_SPACES_BUCKET, DO_SPACES_CDN (hostname), DO_SPACES_CDN_ID (uuid)
# DO_TOKEN is this repo's name for the curl block below. doctl does not read it.
```

Direct API calls when `doctl` doesn't cover something. `DO_TOKEN` is only for this; `doctl` gets its
token from its own config, not from the environment:
```bash
[ -n "$DO_TOKEN" ] || source ~/.env
curl -X GET "https://api.digitalocean.com/v2/<resource>" \
  -H "Authorization: Bearer $DO_TOKEN" \
  -H "Content-Type: application/json"
```

---

## Billing

```bash
doctl balance get                    # current account balance
doctl billing-history list           # charges, payments, refunds
doctl invoice list                   # every invoice UUID
doctl invoice summary <invoice-uuid> # totals for one invoice
doctl invoice get <invoice-uuid>     # line items
doctl invoice pdf <invoice-uuid> invoice.pdf
doctl invoice csv <invoice-uuid> invoice.csv
```

`invoice pdf` and `invoice csv` take the output filename as a second positional, not a flag.
They write the file rather than printing to stdout.

```bash
doctl 1-click list                   # Marketplace one-click apps, all types
doctl 1-click list --type kubernetes # or droplet
```

---

## Gotchas

These apply everywhere. Product-specific gotchas live in their own skill.

**Only `--context` reroutes a command. `--access-token` and `DIGITALOCEAN_ACCESS_TOKEN` are silently ignored.** doctl inverts the precedence every other CLI uses: the stored config token beats both the flag and the environment variable, with no warning. Verified on 1.168, `doctl account get --access-token bogus-not-real` returns the real account, while the same bogus value against an empty `--config` correctly 401s. The danger is believing a junk token disarmed a call. An agent here passed `--access-token fake-token-xxxx` to `monitoring uptime create` expecting a 401 it could document, and created a real billable uptime check. To test an auth failure, point `--config` at an empty file. To change account, `doctl auth switch --context <name>`.

**An empty `--context` is not an error, and there is no confirmation prompt.** `--context ""` falls through to the starred context and runs, so `--context "$DO_CONTEXT"` with the variable unset targets whatever account was last switched to, where a `delete` destroys another team's resources. Run `doctl auth list` to see which context is starred, and guard with `: "${DO_CONTEXT:?}"`. Quote the expansion too: unquoted in bash, a name like `tullo labs` splits into two arguments and fails with `access token is required`, which sends you debugging auth when the bug is quoting.

**Tag resources with project name** for cost tracking:
```bash
doctl compute droplet create <name> --tag-names my-project   # (⚠️ requires approval)
```

**`doctl` self-reports when it is stale.** If a documented flag is missing, check `doctl version` against the release it prints and run `brew upgrade doctl`.

**Cost lives on the team, not the project.** `doctl balance get` and `doctl invoice` report only the team the current context points at, and each team bills separately unless it belongs to an organization. Run them once per context for the full picture. To attribute spend, tag resources and use projects. See `/do-projects`.
