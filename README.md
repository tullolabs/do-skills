# do-skills

DigitalOcean operations skills for AI agents. Seven skills, one per product, so an
agent working on app logs doesn't load 145 lines of Spaces file operations it will
never read.

Every command here was run against `doctl` 1.167 and checked against the DigitalOcean
docs. Where the docs and the CLI disagree, the skill says which one to believe.

## The skills

| Skill | Covers |
|---|---|
| `/do-ops` | Start here. Auth, team contexts, direct API calls, and which skill to pick. |
| `/do-spaces` | Buckets, file operations, CDN URLs and cache flush, access keys. |
| `/do-apps` | App Platform. Logs, specs, deploys, static site hosting. |
| `/do-dns` | Domains, records, nameserver delegation. |
| `/do-databases` | Clusters, connection pools, trusted sources. |
| `/do-droplets` | Compute and SSH. |
| `/do-registry` | Container registry and garbage collection. |

## Install

All seven, for every project on the machine:

```bash
curl -fsSL https://raw.githubusercontent.com/tullolabs/do-skills/main/install.sh | bash
```

Or one project only:

```bash
git clone --depth 1 https://github.com/tullolabs/do-skills /tmp/do-skills
cp -r /tmp/do-skills/do-* .claude/skills/
rm -rf /tmp/do-skills
```

## What it assumes

`doctl` authenticated, and a `~/.env` holding `DO_TOKEN`, `DO_SPACES_KEY`,
`DO_SPACES_SECRET`, `DO_SPACES_ENDPOINT`, `DO_SPACES_BUCKET`, `DO_SPACES_CDN`,
`DO_SPACES_CDN_ID`.

Spaces object operations need an S3 client, usually `aws`. That isn't a choice we
made. DigitalOcean's v2 API has no object endpoints at all, so `doctl spaces` can
only manage keys. Reading one public-read file is the exception, that's a plain `curl`.

## The rule that matters

Destructive actions (delete, destroy, reset, create) need operator approval. Reads
are always safe. Every skill repeats this at the top, because an agent that loads
only `/do-droplets` still needs to know it.
