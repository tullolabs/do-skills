---
name: do-ops
description: DigitalOcean operations cheatsheet for AI agents. Covers auth, Spaces file ops, Droplets, App Platform, Databases, DNS, and common gotchas. Use when working with any DigitalOcean resource.
---

# DigitalOcean Ops

Quick reference for agents working with DigitalOcean infrastructure. `doctl` is pre-authenticated on this machine.

> **Destructive actions (delete, destroy, reset, create) require operator approval. Read-only ops (list, get, logs) are always safe.**

---

## Auth Setup

Two separate auth systems — don't mix them up:

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
# Provides: DO_TOKEN, DO_SPACES_KEY, DO_SPACES_SECRET,
#           DO_SPACES_ENDPOINT, DO_SPACES_BUCKET, DO_SPACES_CDN
```

Direct API calls when `doctl` doesn't cover something:
```bash
source ~/.env
curl -X GET "https://api.digitalocean.com/v2/<resource>" \
  -H "Authorization: Bearer $DO_TOKEN" \
  -H "Content-Type: application/json"
```

---

## Spaces (Object Storage)

All Spaces config comes from `.env`. Bucket name, endpoint, and CDN URL are environment-specific.

`doctl` cannot read or write Spaces objects. It only manages access keys (`doctl spaces keys`) and the CDN.
File operations need a separate S3 client. Check one is present before you promise an upload:

```bash
command -v aws || brew install awscli    # or: pipx install s3cmd
```

### Bucket Structure

```
$DO_SPACES_BUCKET/
├── project-name/
│   ├── images/        ← static images, brand assets
│   ├── videos/        ← video files
│   ├── docs/          ← PDFs, documents
│   └── uploads/
│       └── <user-id>/ ← user-generated content, scoped per user
└── another-project/
    └── ...
```

Rules:
- Top-level folder = project name (match repo/project name)
- Never write to bucket root
- Never write outside your project's folder
- User content goes under `uploads/<user-id>/`

### File Operations

Always `source ~/.env` first. Pass credentials inline — do not configure `~/.aws/credentials`.

```bash
source ~/.env

# Upload (public)
AWS_ACCESS_KEY_ID=$DO_SPACES_KEY \
AWS_SECRET_ACCESS_KEY=$DO_SPACES_SECRET \
AWS_DEFAULT_REGION=us-east-1 \
aws s3 cp ./file.jpg s3://$DO_SPACES_BUCKET/project-name/images/file.jpg \
  --endpoint-url $DO_SPACES_ENDPOINT \
  --acl public-read

# Upload (private)
AWS_ACCESS_KEY_ID=$DO_SPACES_KEY \
AWS_SECRET_ACCESS_KEY=$DO_SPACES_SECRET \
AWS_DEFAULT_REGION=us-east-1 \
aws s3 cp ./file.pdf s3://$DO_SPACES_BUCKET/project-name/docs/file.pdf \
  --endpoint-url $DO_SPACES_ENDPOINT

# List folder
AWS_ACCESS_KEY_ID=$DO_SPACES_KEY \
AWS_SECRET_ACCESS_KEY=$DO_SPACES_SECRET \
AWS_DEFAULT_REGION=us-east-1 \
aws s3 ls s3://$DO_SPACES_BUCKET/project-name/ \
  --endpoint-url $DO_SPACES_ENDPOINT

# Sync local dir to Spaces
AWS_ACCESS_KEY_ID=$DO_SPACES_KEY \
AWS_SECRET_ACCESS_KEY=$DO_SPACES_SECRET \
AWS_DEFAULT_REGION=us-east-1 \
aws s3 sync ./dist s3://$DO_SPACES_BUCKET/project-name/assets/ \
  --endpoint-url $DO_SPACES_ENDPOINT \
  --acl public-read

# Delete a file (⚠️ requires approval)
AWS_ACCESS_KEY_ID=$DO_SPACES_KEY \
AWS_SECRET_ACCESS_KEY=$DO_SPACES_SECRET \
AWS_DEFAULT_REGION=us-east-1 \
aws s3 rm s3://$DO_SPACES_BUCKET/project-name/images/file.jpg \
  --endpoint-url $DO_SPACES_ENDPOINT
```

### CDN URL Format

```
$DO_SPACES_CDN/project-name/images/file.jpg
```

CDN URL = `$DO_SPACES_CDN` + `/` + path within bucket. Never use the raw Spaces endpoint URL in app code, always use CDN.

Spaces supports exactly two canned ACLs: `private` and `public-read`. Anything else (`authenticated-read`,
`bucket-owner-full-control`) returns an error. For rules finer than that, use a bucket policy via
`aws s3api put-bucket-policy`, which the control panel cannot show or edit.

### CDN Cache Flush

After uploading or updating files, flush the CDN cache or changes won't be visible:

```bash
source ~/.env

# Flush entire CDN cache
doctl compute cdn flush $DO_SPACES_CDN_ID --files "*"

# Flush specific path (leading slash, wildcard for a whole directory)
doctl compute cdn flush $DO_SPACES_CDN_ID --files /project-name/images/file.jpg
doctl compute cdn flush $DO_SPACES_CDN_ID --files "/project-name/images/*"

# Get CDN ID if you don't have it
doctl compute cdn list
```

> **Always flush after upload if the file was previously cached.** New files don't need a flush, but updates to existing files do.

---

## Droplets

```bash
# List all
doctl compute droplet list

# Get details
doctl compute droplet get <id>

# Create (⚠️ requires approval)
doctl compute droplet create <name> \
  --region sgp1 \
  --size s-1vcpu-1gb \
  --image ubuntu-24-04-x64 \
  --ssh-keys <fingerprint-or-id> \
  --tag-names project-name \
  --wait

# Find inputs first
doctl compute ssh-key list
doctl compute region list
doctl compute size list
doctl compute image list-distribution --public | grep -i ubuntu

# SSH into droplet
doctl compute ssh <id>

# Get droplet IP
doctl compute droplet get <id> --format PublicIPv4 --no-header

# Delete (⚠️ requires approval)
doctl compute droplet delete <id>
```

---

## App Platform

> **Deployment workflow:** App Platform is connected to GitHub. Push to the linked branch and report back immediately. Do **not** poll deployment status, wait for builds, or trigger deploys manually. Push → done.

### Static Sites on App Platform

**Static sites must run at `/` — never under a sub-path.**

Ingress rules can match and rewrite a path prefix, so `/docs` does reach the component. The breakage happens
one layer down. The built HTML asks for `/assets/app.js`, that request never matches the `/docs` rule, and the
ingress hands it to whatever owns `/`. Getting it right means the build's base path, the ingress match, and
`preserve_path_prefix` all agree, and any one of them drifting gives a white page with 404s in the console.

**The fix:** Give each static site its own domain or subdomain.
- Point a CNAME to the App Platform ingress
- Set `baseUrl: '/'` so all assets resolve from root
- No routing to keep in sync

Sub-path routing is worth the effort for **dynamic backends** (services), where an API prefix is one rule and
there are no relative asset URLs to break.

Two spec fields to know:
- `catchall_document: index.html` is what makes client-side routing work. Without it a deep link 404s.
- Component-level `routes:` is deprecated. Use the top-level `ingress:` block for new specs.

```bash
# List all apps
doctl apps list

# Get app details (includes ID, URL, status)
doctl apps get <id>

# Logs (these do NOT follow by default; there is no --no-follow flag)
doctl apps logs <id> --type run          # runtime logs (default type)
doctl apps logs <id> --type build        # build logs
doctl apps logs <id> --type deploy       # deploy logs
doctl apps logs <id> --type run_restarted  # logs from before a crash-restart
doctl apps logs <id> --tail 50           # last 50 lines
doctl apps logs <id> <component> -f      # follow one component

# Why is it broken
doctl apps list-deployments <id>
doctl apps get-deployment <id> <deployment-id>
doctl apps list-events <id>              # surfaces build/deploy failures with reasons

# Read the live spec (do this before editing anything)
doctl apps spec get <id> > app.yaml
doctl apps propose --spec app.yaml       # dry-run validate, no changes made

# Apply a spec change (⚠️ requires approval)
doctl apps update <id> --spec app.yaml

# Deploy from spec (⚠️ requires approval — only for new apps)
doctl apps create --spec app.yaml

# Trigger re-deploy manually (⚠️ requires approval — rarely needed, prefer git push)
doctl apps create-deployment <id>

# Shell into a running component (⚠️ requires approval)
doctl apps console <id> <component>

# Delete (⚠️ requires approval)
doctl apps delete <id>
```

`doctl apps propose` validates a spec without applying it. Run it before every `update`.

---

## Databases

```bash
# List clusters
doctl databases list

# Get cluster details
doctl databases get <id>

# Connection string
doctl databases connection <id>

# List DBs within a cluster
doctl databases db list <id>

# List users
doctl databases user list <id>

# CA cert — required for sslmode=verify-full clients
doctl databases get-ca <id>

# Trusted sources (the firewall). A new cluster rejects everything until you add one.
doctl databases firewalls list <id>
doctl databases firewalls append <id> --rule ip_addr:<ip>       # (⚠️ requires approval)
doctl databases firewalls append <id> --rule app:<app-uuid>     # (⚠️ requires approval)
doctl databases firewalls append <id> --rule droplet:<id>       # (⚠️ requires approval)

# Connection pooling (PostgreSQL — use this instead of raising max connections)
doctl databases pool list <id>
doctl databases pool create <id> <pool-name> --mode transaction --size 10 --db <dbname> --user <user>

# Resize / autoscale storage (⚠️ requires approval)
doctl databases resize <id> --size <slug> --num-nodes <n>
doctl databases storage-autoscale get <id>

# Delete (⚠️ requires approval)
doctl databases delete <id>
```

Engine slugs for `doctl databases create --engine`: `pg`, `mysql`, `mongodb`, `kafka`, `opensearch`, `valkey`.
Redis is gone. It is `valkey` now, and the old `redis` slug fails.

---

## DNS / Domains

Managing a domain you already own. Two levels: the **domain** resource (the zone) and the **records** inside it.

```bash
# --- Domain (zone) ---

# List domains
doctl compute domain list

# Get a domain (shows TTL + zone file)
doctl compute domain get example.com

# Add a domain you already own to DO (⚠️ requires approval)
doctl compute domain create example.com
# ...optionally seed an A record for @ at the same time:
doctl compute domain create example.com --ip-address <ip>

# Remove a domain AND all its records (⚠️ requires approval — destructive)
doctl compute domain delete example.com

# --- Records ---

# List DNS records for a domain
doctl compute domain records list example.com

# Create A record (⚠️ requires approval)
doctl compute domain records create example.com \
  --record-type A \
  --record-name @ \
  --record-data <ip>

# Create CNAME (⚠️ requires approval)
doctl compute domain records create example.com \
  --record-type CNAME \
  --record-name www \
  --record-data @

# Create TXT record — domain verification / SPF (⚠️ requires approval)
doctl compute domain records create example.com \
  --record-type TXT \
  --record-name @ \
  --record-data "v=spf1 include:_spf.google.com ~all"

# Update an existing record (⚠️ requires approval)
doctl compute domain records update example.com \
  --record-id <id> \
  --record-data <new-value>

# Delete record (⚠️ requires approval)
doctl compute domain records delete example.com <record-id>
```

> **DO only serves DNS once nameservers are delegated.** Adding a domain in DO does nothing until the registrar's nameservers point to `ns1.digitalocean.com`, `ns2.digitalocean.com`, `ns3.digitalocean.com`. DO is not a registrar — domains are bought elsewhere, then delegated here.

---

## Container Registry

```bash
doctl registry get
doctl registry repository list-v2                    # `list` was removed; v2 is the only lister
doctl registry repository list-tags <repo-name>
doctl registry repository list-manifests <repo-name>

doctl registry login                                 # auth local docker
doctl registry garbage-collection start              # (⚠️ requires approval) reclaims untagged layers

# Delete an image (⚠️ requires approval)
doctl registry repository delete-tag <repo-name> <tag>
```

Deleting tags does not free quota. Storage only drops after garbage collection runs.

---

## Spaces Access Keys (via doctl)

`doctl spaces` only manages keys. There is no `doctl spaces list`/`get` for buckets; use `aws s3 ls` or the API.

```bash
doctl spaces keys list
doctl spaces keys create <name> --grants "bucket=my-bucket;permission=readwrite"
doctl spaces keys delete <key-id>          # (⚠️ requires approval)
```

Scoped ("limited") keys are the right default for an app that touches one bucket. Caveat: a limited key
cannot call `PutBucketPolicy`. Use a full-access key for policy changes.

---

## Gotchas

**`doctl` has multiple auth contexts and no confirmation prompt.** Run `doctl auth list` first. The current context is the team every command hits, so a `delete` against the wrong context destroys another team's resources. Pass `--context <name>` when in doubt.

**AWS CLI region must be `us-east-1`** even if the bucket is in another region (e.g. SGP1). This is a Spaces quirk, always use `us-east-1`.

**`doctl spaces` does not list buckets.** It only manages access keys. Bucket and object listing goes through an S3 client or the API.

**Creating a droplet without `--ssh-keys` emails a root password.** Always pass `--ssh-keys`. Run `doctl compute ssh-key list` to find the fingerprint.

**Never configure `~/.aws/credentials`** — pass credentials inline. Multiple agents share this machine.

**`doctl` vs AWS CLI are separate auth systems.** `doctl` auth doesn't give Spaces access. Spaces needs `DO_SPACES_KEY`/`DO_SPACES_SECRET`, not `DO_TOKEN`.

**Always source `.env` before Spaces commands.** `$DO_SPACES_BUCKET`, `$DO_SPACES_ENDPOINT`, and `$DO_SPACES_CDN` won't exist otherwise — commands will silently fail or write to wrong paths.

**CDN URLs, not raw Spaces URLs.** The raw endpoint bypasses CDN. Always construct URLs from `$DO_SPACES_CDN`.

**`--acl public-read` is required for public files.** Files uploaded without it are private by default.

**Tag resources with project name** for cost tracking:
```bash
doctl compute droplet create <name> --tag-names my-project
```

**App IDs are UUIDs, not names.** Use `doctl apps list` to find the ID before running any app command. Most `doctl apps` subcommands also accept the app name.

**A new database cluster blocks every connection** until a trusted source is added. "Connection timed out" against a fresh cluster is the firewall, not the credentials.

**Container registry deletes don't free quota.** Tags and manifests disappear immediately; storage only drops after `doctl registry garbage-collection start`.

**`doctl` self-reports when it is stale.** If a documented flag is missing, check `doctl version` against the release it prints and run `brew upgrade doctl`.
