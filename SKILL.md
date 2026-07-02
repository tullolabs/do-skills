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
# Verify doctl auth
doctl account get

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

All Spaces config comes from `.env` — bucket name, endpoint, and CDN URL are all environment-specific.

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

CDN URL = `$DO_SPACES_CDN` + `/` + path within bucket. Never use the raw Spaces endpoint URL in app code — always use CDN.

### CDN Cache Flush

After uploading or updating files, flush the CDN cache or changes won't be visible:

```bash
source ~/.env

# Flush entire CDN cache
doctl compute cdn flush $DO_SPACES_CDN_ID --files "*"

# Flush specific path only
doctl compute cdn flush $DO_SPACES_CDN_ID --files "project-name/images/file.jpg"

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
  --image ubuntu-22-04-x64 \
  --tag-names project-name

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

App Platform serves static sites from their build directory root with no path rewriting. Attempting to host a static site under a sub-path (e.g. `/docs`) will break asset loading or client-side routing regardless of `baseUrl` or `preserve_path_prefix` settings — the ingress can route traffic to a component but cannot remap `/docs/assets/...` → `/assets/...` at the file-serve level.

**The fix:** Give each static site its own domain or subdomain.
- Point a CNAME to the App Platform ingress
- Set `baseUrl: '/'` so all assets resolve from root
- The static site serves correctly with no routing gymnastics

Sub-path routing works for **dynamic backends** (services), not static sites.

```bash
# List all apps
doctl apps list

# Get app details (includes ID, URL, status)
doctl apps get <id>

# Logs
doctl apps logs <id> --type run        # runtime logs
doctl apps logs <id> --type build      # build logs
doctl apps logs <id> --type deploy     # deploy logs
doctl apps logs <id> --no-follow | tail -50  # recent only

# Deploy from spec (⚠️ requires approval — only for new apps)
doctl apps create --spec app.yaml

# Trigger re-deploy manually (⚠️ requires approval — rarely needed, prefer git push)
doctl apps create-deployment <id>

# Delete (⚠️ requires approval)
doctl apps delete <id>
```

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

# Delete (⚠️ requires approval)
doctl databases delete <id>
```

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
doctl registry repository list
doctl registry repository list-tags <repo-name>
```

---

## Spaces Metadata (via doctl)

```bash
doctl spaces list
doctl spaces get <bucket-name>
```

---

## Gotchas

**AWS CLI region must be `us-east-1`** even if the bucket is in another region (e.g. SGP1). This is a Spaces quirk — always use `us-east-1`.

**Never configure `~/.aws/credentials`** — pass credentials inline. Multiple agents share this machine.

**`doctl` vs AWS CLI are separate auth systems.** `doctl` auth doesn't give Spaces access. Spaces needs `DO_SPACES_KEY`/`DO_SPACES_SECRET`, not `DO_TOKEN`.

**Always source `.env` before Spaces commands.** `$DO_SPACES_BUCKET`, `$DO_SPACES_ENDPOINT`, and `$DO_SPACES_CDN` won't exist otherwise — commands will silently fail or write to wrong paths.

**CDN URLs, not raw Spaces URLs.** The raw endpoint bypasses CDN. Always construct URLs from `$DO_SPACES_CDN`.

**`--acl public-read` is required for public files.** Files uploaded without it are private by default.

**Tag resources with project name** for cost tracking:
```bash
doctl compute droplet create <name> --tag-names my-project
```

**App IDs are UUIDs, not names.** Use `doctl apps list` to find the ID before running any app command.
