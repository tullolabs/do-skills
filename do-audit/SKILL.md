---
name: do-audit
description: Read-only audit of a DigitalOcean project for cost waste, performance, security exposure, reliability, capacity, and hygiene. Use to review an existing setup, find unused spend, or check what is exposed and unbacked.
user-invocable: true
argument-hint: "[audit-name|area]"
---

# DigitalOcean Audit

> Destructive ops need operator approval. Reads are always safe.
> Auth: `doctl` is pre-authenticated. See `/do-ops` for auth contexts.

**This skill never writes to DigitalOcean.** It runs `list` and `get`, writes files under `.do/`,
and proposes fixes as text. It does not apply them, not even something as safe as deleting an
unattached volume. If the operator wants a fix applied, that is a separate request to the skill
that owns the resource.

## 1. Resolve scope, then stop if it is ambiguous

The audit covers exactly what is assigned to one project. An unset `DO_CONTEXT` silently resolves
to whichever context is starred, which may be another customer's account.

```bash
[ -f .env ] && . ./.env
: "${DO_CONTEXT:?unset — ask the operator which DO account to audit}"
: "${DO_PROJECT:?unset — ask the operator which project to audit}"

doctl account get --context "$DO_CONTEXT" --format Email,Team
doctl projects list --context "$DO_CONTEXT" --format UUID,Name,IsDefault
```

Print the account email, team, and project name and confirm they are what the operator expects
before going further. Auditing the wrong account wastes a full run and leaks nothing, but it also
produces a report that looks authoritative and describes someone else's infrastructure.

## 2. Create the output directory

```bash
OUT=".do/audits/$(date -u +%Y-%m-%dT%H-%M-%SZ)"     # or .do/audits/<name> if the operator named it
mkdir -p "$OUT/raw"
printf '*\n' > .do/audits/.gitignore                 # audits hold account detail; never commit them
```

ISO-8601 with colons replaced by dashes, because colons in a path break on Windows checkouts and
confuse shell completion. The `.gitignore` is written every run and is cheap to rewrite. Leave the
existing `.do/.gitignore` alone; it belongs to `doctl apps dev config`.

## 3. Build the inventory once

```bash
./inventory.py "$DO_PROJECT" "$OUT" "$DO_CONTEXT"    # relative to this skill's directory
```

This writes `$OUT/inventory.json` and `$OUT/prices.json` and prints a resource count. It is the
only step that talks to DigitalOcean in bulk, and it exists as a script for two reasons:

- **`doctl` leaks credentials through ordinary list output**, so redaction has to happen before
  anything reaches disk. See the first gotcha for what leaks and why a per-command denylist misses it.
- **Six subagents read this file.** Anything duplicated in it is paid for six times over, so the
  script drops `active_deployment` (which repeats each app's whole spec, about 9 KB per app), strips
  app env values while keeping every key, scope, and type, and splits the droplet price catalog into
  `prices.json`, which only the cost playbook opens.

The commands it runs, all read-only:

```bash
doctl account get
doctl projects list
doctl projects resources list <project-id>
doctl compute droplet list
doctl compute volume list
doctl databases list
doctl apps list
doctl compute domain list
doctl kubernetes cluster list
doctl compute load-balancer list
doctl compute reserved-ip list
doctl compute firewall list-by-droplet <droplet-id>
doctl vpcs list
doctl compute snapshot list
doctl monitoring alert list
doctl compute droplet backup-policies list
doctl compute certificate list
doctl compute cdn list
doctl compute size list
```

Firewalls and VPCs are not project-assignable, so the script reaches them by pivoting through the
project's droplets rather than listing them account-wide. Snapshots, alert policies, and backup
policies attach to a resource rather than to a project and are filtered the same way. Anything the
script could not resolve lands in `inventory.gaps` and must be reported, not silently dropped.

## 4. Dispatch six subagents in parallel

One per playbook, all at once. Each subagent gets this instruction, with `<area>` substituted:

> Read `playbooks/<area>.md` in this skill's directory. Run only the commands the playbook names,
> all read-only. Write your findings to `$OUT/raw/<area>.jsonl`, one JSON object per line, and your
> reasoning and evidence to `$OUT/raw/<area>.md`. Do not touch any other file. Do not run a command
> that creates, updates, deletes, or starts anything.
>
> Do not read `$OUT/inventory.json` whole. On a 21-app project it is 94 KB, and each check needs one
> slice of it. Pull the slice the Source column names:
> `python3 -c 'import json;print(json.dumps(json.load(open("'"$OUT"'/inventory.json"))["resources"]["volume"]))'`

| Area | Playbook | Looks for |
|---|---|---|
| cost | `playbooks/cost.md` | Resources billing for nothing: unattached volumes, idle reserved IPs, orphaned snapshots, oversized droplets |
| performance | `playbooks/performance.md` | Configuration that costs latency: missing connection pools, default CDN TTLs, cross-region hops |
| security | `playbooks/security.md` | Exposure: open firewall rules, databases with no trusted sources, expiring certificates |
| reliability | `playbooks/reliability.md` | Single points of failure: no backups, single-node clusters, stale restore points |
| capacity | `playbooks/capacity.md` | Headroom: disabled autoscaling, volumes near full, replication factor 1 |
| hygiene | `playbooks/hygiene.md` | Drift: unassigned resources, duplicate names, orphaned cluster leftovers |

**Each subagent owns its own two files.** Nothing appends to a shared file, so six parallel writers
cannot interleave or clobber each other. That is the whole reason the split exists.

## 5. Assemble

Concatenate the six `raw/*.jsonl` into `findings.jsonl`, sorted by area then by severity
(`crit`, `high`, `med`, `low`), then write `summary.md`.

One finding per line, no pretty-printing, keys in this exact order so two runs diff cleanly:

```json
{"id":"cost-003","area":"cost","sev":"high","title":"Unattached volume billing since 2025-11-02","urn":"do:volume:a1b2","resource":"pg-data-old","evidence":"droplet_ids=[] size_gigabytes=100","fix":"doctl compute volume delete a1b2","usd_mo":10.0}
```

`sev` is `crit`, `high`, `med`, or `low`. `usd_mo` is a number or `null`. `urn` must appear in
`inventory.json`, or the finding is about something outside the audited scope and does not belong
in the report. `fix` is a string for a human to read. Nothing executes it.

`summary.md` is the only file meant to be read start to finish, so keep it near 80 lines: YAML
frontmatter (timestamp, context, account email, project, `doctl` version, resource counts), a
severity count table, the estimated monthly waste total, the top ten findings at one line each,
and `## Not checked`.

**`## Not checked` is mandatory and is not boilerplate.** A clean audit that omits it reads as
"everything is fine" when it means "everything I can see is fine". At minimum it lists what
`doctl` cannot reach:

| Blind spot | What stays unknown |
|---|---|
| No utilization metrics anywhere in `doctl` | Whether a droplet is oversized or idle. Every performance finding is configuration review, not load analysis. |
| `doctl spaces` cannot list buckets | Public-bucket and object-level exposure. Needs an S3 client; see `/do-spaces`. |
| Uptime checks return config, not results | Measured latency or availability history. |
| No registry storage-used read | Registry waste, until a garbage collection run, which is a write. |
| No in-cluster Kubernetes state | Pods, PVCs, ingresses. Needs `kubectl`; see `/do-k8s`. |

Add to it anything in `inventory.gaps`, plus any command that returned a 403.

## Gotchas

**A read-only command can still hand you a live password.** `doctl databases list -o json` and `databases get` both return `connection.password`, `private_connection.password`, and `users[].password` populated, and `connection.uri` has the same password embedded in it, so redacting the obvious key alone is not enough. Verified against a real cluster on this account. Nothing in either command's name suggests it, which is why a per-command denylist is not the defence; redacting by key name is. Redact by key name before writing or displaying anything, which is what `inventory.py` does. Never run the commands whose only output is a credential: `doctl auth token`, `databases connection`, `databases replica connection`, `vector-databases credentials`, `registry docker-config`, `registry kubernetes-manifest`, `kubernetes cluster kubeconfig show`, `network attachment get-service-key`, `network attachment get-bgp-auth-key`, `secrets get --show`. Reference a secret by name, never by value.

**Some commands that read like reads are writes.** `doctl registry garbage-collection start` deletes blobs. `doctl security scans create` starts a billable scan. `doctl apps dev config set` writes to local disk. An earlier pass on this repo created a real billable uptime check while trying to provoke an authentication error, so treat a command as a write unless its name is `list`, `get`, or `show`.

**A 403 on Secrets Manager or CSPM is a scope gap, not a failure.** Those APIs need token scopes the default OAuth context often lacks. Record the command in `## Not checked` and move on. Retrying it, or switching contexts to get around it, audits an account the operator did not ask about.

**Project scope has holes that are not the audit's fault.** Firewalls, VPCs, certificates, and CDN endpoints cannot be assigned to a project at all, and `doctl projects resources list` will never return them. The inventory pivots through the project's droplets to reach firewalls and VPCs, so a resource with no droplets in the project has an invisible network configuration. Say so in the report rather than reporting zero findings.

**A check that finds nothing and a check that could not run look identical in the output, and only one of them is good news.** Most playbook checks name a JSON field. If that field is missing from `inventory.json`, you have learned nothing about the resource, so say so in `## Not checked` instead of emitting zero findings. This is not hypothetical: `doctl` renames fields between the JSON object and the `--format` columns, so a reserved IP's attachment is `droplet` in JSON and `DropletID` in text, a cluster's HA flag is `HAControlPlane` in text, and an autoscale pool's bounds sit under `config`. Where a playbook row names both, the text column is the one verified against this `doctl` build.

**Two runs should diff to almost nothing.** Finding ids are `<area>-<nnn>` assigned in the playbook's own check order, not in discovery order, so the same problem keeps the same id across runs. If a re-run reshuffles ids, the report cannot be used to track whether anything actually got fixed, which is most of the point of writing it to a file.
