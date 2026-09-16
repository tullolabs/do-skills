# do-skills

DigitalOcean operations skills for AI agents. Fifteen skills, one per product area, so
an agent working on app logs doesn't load 180 lines of Spaces file operations it will
never read.

Coverage is the whole `doctl` command tree: 505 of its 511 commands are documented, and
the six that aren't are shell-completion plumbing named in `validate.py`. That's a checked
claim, not a boast. Gate 2 of the validator walks the live command tree and fails if
anything is missing.

Every command was verified against `doctl --help` before being written, and the factual
claims were checked against the DigitalOcean docs. Where the docs and the CLI disagree,
the skill says which one to believe. That work turned up six places where doctl's own
help examples are uncopyable — `databases firewalls replace` advertises `--rules` when the
flag is `--rule`, `apps update-alert-destinations` advertises `--alert-destinations` when
it is `--app-alert-destinations`, and so on. Each one is called out in the skill that
owns it.

## The skills

| Skill | Covers |
|---|---|
| `/do-ops` | Start here. Auth, team contexts, billing, direct API calls, and which skill to pick. |
| `/do-droplets` | VMs. Power, resize, rebuild, snapshots, backups, SSH keys, autoscale pools. |
| `/do-network` | VPCs and peering, cloud firewalls, load balancers, certificates, reserved IPs, NAT gateways, BYOIP. |
| `/do-storage` | Block storage volumes, snapshots, images and transfer, network file storage. |
| `/do-k8s` | Kubernetes clusters, node pools, kubeconfig, upgrades, registry integration. |
| `/do-apps` | App Platform. Logs, specs, deploys, static site hosting. |
| `/do-functions` | Serverless functions, namespaces, deploys, activations. |
| `/do-databases` | Managed clusters, connection pools, trusted sources. |
| `/do-spaces` | Buckets, file operations, CDN URLs and cache flush, access keys. |
| `/do-registry` | Container registry and garbage collection. |
| `/do-dns` | Domains, records, nameserver delegation. |
| `/do-ai` | Gradient agents and knowledge bases, vector databases, serverless and dedicated inference. |
| `/do-monitoring` | Metric alert policies and uptime checks. |
| `/do-projects` | Projects, resource assignment, tags. |
| `/do-secrets` | Secrets Manager and CSPM security scans. |

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

## Contributing

Read `CLAUDE.md` first. The short version: verify every command against `doctl --help`
before writing it, and run `./validate.py` before committing.
