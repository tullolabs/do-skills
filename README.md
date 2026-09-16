# do-skills

DigitalOcean operations skills for AI agents. Sixteen skills, one per product area, so
an agent working on app logs doesn't load 180 lines of Spaces file operations it will
never read.

Coverage is the whole `doctl` command tree: 505 of its 511 commands are documented. The
six left out are `help`, `version`, and the four shell-completion generators, each named
with a reason in `validate.py`. That's a checked claim, not a boast. Gate 2 of the
validator walks the live command tree and fails if anything is missing.

Every command was verified against `doctl --help` before being written, and the factual
claims were checked against the DigitalOcean docs. Where the docs and the CLI disagree,
the skill says which one to believe. That work turned up ten commands whose own `--help`
prints something that does not run — `databases firewalls replace` advertises `--rules`
when the flag is `--rule`, `apps update-alert-destinations` advertises
`--alert-destinations` when it is `--app-alert-destinations`, `monitoring uptime create`
omits a required positional, and so on. Each one is called out in the skill that owns it,
so an agent that copies from DigitalOcean's docs knows why the copy failed.

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
| `/do-audit` | Read-only audit of a project: cost waste, exposure, backups, capacity, hygiene. |

## Install

All sixteen, for every project on the machine:

```bash
curl -fsSL https://raw.githubusercontent.com/tullolabs/do-skills/main/install.sh | bash
```

Or one project only:

```bash
git clone --depth 1 https://github.com/tullolabs/do-skills /tmp/do-skills
cp -r /tmp/do-skills/do-* .claude/skills/
rm -rf /tmp/do-skills
```

## Examples

Starting prompts in `examples/`. They're short on purpose: each one names the target,
the constraints, and which skills to lean on, and the skills supply the actual commands.

| File | Does |
|---|---|
| `project-setup.md` | Run once per repo. Pick the account and project, write them to `.env`. |
| `droplet-docker.md` | A $6/mo droplet running a Docker Compose stack. |
| `app-platform.md` | Deploy a repo to App Platform from a validated spec. |
| `static-site.md` | Static files to Spaces with the CDN in front. |
| `deployment-check.md` | Read-only health check of an existing deployment. One line when clean. |

Start with `project-setup.md`. The rest assume `DO_CONTEXT` and `DO_PROJECT` already exist.

## What it assumes

`doctl` authenticated, which it does from its own config. Nothing here sets a doctl
token, and it would be ignored if it tried; see the auth gotcha in `/do-ops`.

Spaces is the only part that needs environment variables, because it does not go
through `doctl` at all. Seven names, `DO_TOKEN` for raw v2 API calls plus
`DO_SPACES_KEY`, `DO_SPACES_SECRET`, `DO_SPACES_ENDPOINT`, `DO_SPACES_BUCKET`,
`DO_SPACES_CDN`, and `DO_SPACES_CDN_ID`. The names are the contract; how they reach
the environment is yours to pick. direnv, a secrets manager, and CI all already
export them. Absent that, the skills fall back to `~/.env` with a guarded
`[ -n "$DO_SPACES_KEY" ] || source ~/.env`, so an existing export always wins.

Per-project settings are separate and optional, and live in the project's own `.env` rather than `~/.env`,
since one machine works across accounts. `DO_CONTEXT` names the auth context to deploy to, `DO_PROJECT` the
project new resources belong to, `DO_APP_REPO` the `owner/repo` for App Platform. When they are absent the
skills tell the agent to ask rather than guess, because an unset context silently resolves to whichever
account was last switched to.

Spaces object operations need an S3 client, usually the `aws` CLI. That isn't a choice
we made. DigitalOcean's v2 API has no object endpoints at all, so `doctl spaces` can
only manage keys. Reading one public-read file is the exception, that's a plain `curl`.
An application talking to Spaces would use an S3 SDK rather than the CLI, and wiring
that up is out of scope here.

## The rule that matters

Destructive actions (delete, destroy, reset, create) need operator approval. Reads
are always safe. Every skill repeats this at the top, because an agent that loads
only `/do-droplets` still needs to know it.

## validate.py

The repo checks itself. `validate.py` takes no dependencies and runs two gates against a
real `doctl` binary:

```bash
./validate.py              # whichever doctl is on PATH
./validate.py /tmp/doctl   # or a specific build
```

```
gate 1  commands written: 510   flag pairs: 263   problems: 0
gate 2  leaf commands: 511   excluded: 6   undocumented: 0

PASS
```

Gate 1 pulls every `doctl ...` invocation out of all sixteen skills and the audit
playbooks they bundle, joins `\` continuations, and asserts the command path and each flag
actually appear in that command's `--help`. It exists because a flag that doesn't exist
reads exactly like a flag that does.

Gate 2 stays on the skills alone. A command documented only inside a playbook would
otherwise count as covered and hide a missing product skill.

Gate 2 walks the whole command tree and asserts every leaf is documented somewhere or
sits in the `EXCLUDED` dict with a written reason. This is the one that matters when
DigitalOcean ships a product: the gate fails, and nobody has to notice by hand.

Run both before any commit that touches a command.

## Contributing

Read `AGENTS.md` first. The short version: this is a live account so use `--help` only,
verify every command against it before writing, and run `./validate.py` before committing.
