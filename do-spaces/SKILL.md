---
name: do-spaces
description: DigitalOcean Spaces, buckets, S3, and CDN. Use for uploading, listing, syncing, and deleting objects with the AWS CLI, CDN endpoints and cache flush, and Spaces access keys and grants.
user-invocable: true
argument-hint: "[upload|list|delete|flush] [path]"
---

# Spaces

> Destructive ops (delete, overwrite) need operator approval. Reads are always safe.
> Auth: the six `DO_SPACES_*` vars must be in the environment. See `/do-ops` for doctl contexts.

Bucket name, endpoint, and CDN URL are environment-specific, so nothing is hardcoded here. `~/.env` is the
fallback when those vars are not already exported, which is why every block below starts with the same
guarded line.

`doctl` cannot read or write Spaces objects. It only manages access keys (`doctl spaces keys`) and the CDN.
Writes, listings, and deletes need a separate S3 client.

```bash
command -v aws || brew install awscli    # or: pipx install s3cmd
```

**Reading a public file needs none of this.** A `public-read` object is a plain GET on its CDN URL, so no
credentials, no S3 client, no `.env`. Use the AWS CLI only to write, list, or delete.

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

```bash
[ -n "$DO_SPACES_KEY" ] || source ~/.env

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

AWS_ACCESS_KEY_ID=$DO_SPACES_KEY \
AWS_SECRET_ACCESS_KEY=$DO_SPACES_SECRET \
AWS_DEFAULT_REGION=us-east-1 \
aws s3 ls s3://$DO_SPACES_BUCKET/project-name/ \
  --endpoint-url $DO_SPACES_ENDPOINT

AWS_ACCESS_KEY_ID=$DO_SPACES_KEY \
AWS_SECRET_ACCESS_KEY=$DO_SPACES_SECRET \
AWS_DEFAULT_REGION=us-east-1 \
aws s3 sync ./dist s3://$DO_SPACES_BUCKET/project-name/assets/ \
  --endpoint-url $DO_SPACES_ENDPOINT \
  --acl public-read

# (⚠️ requires approval)
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

CDN URL = `$DO_SPACES_CDN` + `/` + path within bucket.

Spaces supports exactly two canned ACLs: `private` and `public-read`. Don't count on `authenticated-read` or
`bucket-owner-full-control` doing anything useful. For rules finer than that, use a bucket policy via
`aws s3api put-bucket-policy`, which the control panel cannot show or edit.

### CDN endpoints

A CDN endpoint is its own resource created over a bucket. `doctl compute cdn create` takes the bucket's full
Spaces hostname as its positional origin — `<bucket>.<region>.digitaloceanspaces.com`, never the bare bucket
name — and returns the endpoint plus the CDN ID that `$DO_SPACES_CDN_ID` holds. A custom subdomain needs a
DigitalOcean-managed certificate; see `/do-network` for issuing one.

```bash
[ -n "$DO_SPACES_KEY" ] || source ~/.env

doctl compute cdn list --format ID,Origin,Endpoint,TTL,CustomDomain,CertificateID

# TTL defaults to 3600 seconds
doctl compute cdn create $DO_SPACES_BUCKET.<region>.digitaloceanspaces.com   # (⚠️ requires approval)

# --certificate-id is mandatory whenever --domain is set
# (⚠️ requires approval)
doctl compute cdn create $DO_SPACES_BUCKET.<region>.digitaloceanspaces.com \
  --domain cdn.example.com \
  --certificate-id <certificate-id>

doctl compute cdn get <cdn-id> --format ID,Origin,Endpoint,TTL,CustomDomain,CertificateID

doctl compute cdn update <cdn-id> --ttl 600   # (⚠️ requires approval)

# The certificate must already cover that FQDN
doctl compute cdn update <cdn-id> --domain cdn.example.com --certificate-id <certificate-id>   # (⚠️ requires approval)

# Delete the endpoint (⚠️ requires approval — CDN URLs stop resolving, bucket objects are untouched)
doctl compute cdn delete <cdn-id>
```

`update` sends only the flags you pass, so `--ttl 600` leaves an existing custom domain alone; with no flags
at all it stops at `Nothing to update.`. Get the certificate ID from `doctl compute certificate list`.

### CDN Cache Flush

Edge cache TTL defaults to one hour, so an updated file refreshes on its own. Flush when you need it now:

```bash
[ -n "$DO_SPACES_KEY" ] || source ~/.env

doctl compute cdn flush $DO_SPACES_CDN_ID --files "*"   # (⚠️ requires approval)

# Leading slash; wildcard for a whole directory
doctl compute cdn flush $DO_SPACES_CDN_ID --files /project-name/images/file.jpg   # (⚠️ requires approval)
doctl compute cdn flush $DO_SPACES_CDN_ID --files "/project-name/images/*"   # (⚠️ requires approval)

# Get the CDN ID
doctl compute cdn list
```

> **Always flush after upload if the file was previously cached.** New files don't need it.

### Access Keys

`doctl spaces` only manages keys. There is no bucket list or get; use `aws s3 ls` or the API.

```bash
doctl spaces keys list
doctl spaces keys get <access-key-id> --format Name,Grants
doctl spaces keys create <name> --grants "bucket=my-bucket;permission=readwrite"   # (⚠️ requires approval)

# Rename and re-grant (⚠️ requires approval — replaces the whole grant list, both flags required)
doctl spaces keys update <access-key-id> --name new-key \
  --grants "bucket=my-bucket;permission=readwrite,bucket=my-other-bucket;permission=read"

doctl spaces keys delete <key-id>          # (⚠️ requires approval)
```

Scoped ("limited") keys are the right default for an app that touches one bucket, but a limited key cannot
call `PutBucketPolicy`. Use a full-access key for policy changes.

## Gotchas

**The endpoint URL picks the datacenter, not the region flag.** `--endpoint-url` is what routes the request. `us-east-1` is the safe placeholder every DO example uses, and non-Python SDKs require it for bucket creation. Setting it while the bucket lives in SGP1 costs nothing.

**`doctl spaces` does not list buckets.** It only manages access keys. Bucket and object listing goes through an S3 client or the API.

**`doctl spaces keys update` replaces the entire grant list.** It PUTs exactly what `--grants` contains, so any bucket you leave off the line loses access the moment the command returns, with no warning and no diff in the output. Run `doctl spaces keys get <access-key-id> --format Grants` first and re-send every grant you intend to keep. `--name` is required too, so there is no way to change grants without also restating the name.

**Never configure `~/.aws/credentials`** — pass credentials inline. Multiple agents share this machine.

**Check the `DO_SPACES_*` vars are set before any Spaces command.** Unset, `$DO_SPACES_BUCKET` and `$DO_SPACES_ENDPOINT` expand to empty strings rather than erroring, so `aws s3 cp ./file.jpg s3://$DO_SPACES_BUCKET/images/file.jpg` becomes a write to `s3:///images/file.jpg` and either fails confusingly or lands somewhere you did not mean. Use `[ -n "$DO_SPACES_KEY" ] || source ~/.env` rather than a bare `source`: an unconditional source overwrites values that direnv, a secrets manager, or CI already put in the environment, so a deliberate override silently loses to the file.

**CDN URLs, not raw Spaces URLs.** The raw endpoint bypasses CDN. Always construct URLs from `$DO_SPACES_CDN`.

**`--acl public-read` is required for public files.** Files uploaded without it are private by default.
