---
name: do-spaces
description: Use for any DigitalOcean Spaces, bucket, S3, or CDN task. Upload, list, sync, and delete objects with the AWS CLI, build CDN URLs, flush the CDN cache, and manage Spaces access keys with doctl.
user-invocable: true
argument-hint: "[upload|list|delete|flush] [path]"
---

# Spaces

> Destructive ops (delete, overwrite) need operator approval. Reads are always safe.
> Auth: `source ~/.env` for Spaces keys. See `/do-ops` for doctl contexts.

All Spaces config comes from `.env`. Bucket name, endpoint, and CDN URL are environment-specific.

`doctl` cannot read or write Spaces objects. It only manages access keys (`doctl spaces keys`) and the CDN.
Writes, listings, and deletes need a separate S3 client. Check one is present before you promise an upload:

```bash
command -v aws || brew install awscli    # or: pipx install s3cmd
```

**Reading a public file needs none of this.** A `public-read` object is a plain GET on its CDN URL, so no
credentials, no S3 client, no `.env`. Only reach for the AWS CLI when you need to write, list, or delete.

```bash
curl -sSL -o local.jpg $DO_SPACES_CDN/project-name/images/file.jpg
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

Spaces supports exactly two canned ACLs: `private` and `public-read`. Don't count on `authenticated-read` or
`bucket-owner-full-control` doing anything useful. For rules finer than that, use a bucket policy via
`aws s3api put-bucket-policy`, which the control panel cannot show or edit.

### CDN Cache Flush

Edge cache TTL defaults to one hour, so an updated file does refresh on its own. Flush when you need it now:

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

### Access Keys

`doctl spaces` only manages keys. There is no `doctl spaces list`/`get` for buckets; use `aws s3 ls` or the API.

```bash
doctl spaces keys list
doctl spaces keys create <name> --grants "bucket=my-bucket;permission=readwrite"
doctl spaces keys delete <key-id>          # (⚠️ requires approval)
```

Scoped ("limited") keys are the right default for an app that touches one bucket. Caveat: a limited key
cannot call `PutBucketPolicy`. Use a full-access key for policy changes.

## Gotchas

**The endpoint URL picks the datacenter, not the region flag.** `--endpoint-url` is what routes the request. `us-east-1` is the safe placeholder every DO example uses, and non-Python SDKs actually require it for bucket creation. Setting it while the bucket lives in SGP1 costs nothing.

**`doctl spaces` does not list buckets.** It only manages access keys. Bucket and object listing goes through an S3 client or the API.

**Never configure `~/.aws/credentials`** — pass credentials inline. Multiple agents share this machine.

**Always source `.env` before Spaces commands.** `$DO_SPACES_BUCKET`, `$DO_SPACES_ENDPOINT`, and `$DO_SPACES_CDN` won't exist otherwise — commands will silently fail or write to wrong paths.

**CDN URLs, not raw Spaces URLs.** The raw endpoint bypasses CDN. Always construct URLs from `$DO_SPACES_CDN`.

**`--acl public-read` is required for public files.** Files uploaded without it are private by default.
