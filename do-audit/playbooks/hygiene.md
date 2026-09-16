# Audit: hygiene and organization

> **Read-only.** Run `list` and `get` only. Never create, update, delete, or start anything.
> Write `raw/hygiene.jsonl` and `raw/hygiene.md`. Touch no other file.
> Never emit a credential value. Reference a secret by name.

This is the only playbook that deliberately looks outside the project, because "assigned to no
project" is invisible from inside one. Compare the account-wide listers against
`inventory.json` and report the difference. Do not audit other projects' resources; a resource that
belongs to a different project is correctly placed and is not a finding.

## Checks

| id | Finding when | Source | sev |
|---|---|---|---|
| hyg-001 | a resource is in the default project and the default project is a catch-all | `doctl projects list`, `IsDefault` | med |
| hyg-002 | two resources of the same type share a name | `inventory.json` | high |
| hyg-003 | a tag exists that no resource in scope carries | `compute tag list` | low |
| hyg-004 | a Kubernetes cluster has orphaned load balancers or volumes | `kubernetes cluster list-associated-resources <cluster-id>` | high |
| hyg-005 | a domain in scope has no A, AAAA, or CNAME record pointing at a resource in scope | `doctl compute domain records list <domain>` | med |
| hyg-006 | an app's `spec.name` does not match its deployed name or repo | `resources.app[].spec` | low |
| hyg-007 | `inventory.unresolved_urns` is non-empty | `inventory.json` | med |
| hyg-008 | `inventory.gaps` is non-empty | `inventory.json` | high |
| hyg-009 | a snapshot is older than 180 days | `resources.snapshot[]` | low |
| hyg-010 | a firewall has no droplets and no tags attached | `resources.firewall[]` | med |
| hyg-011 | a VPC in scope contains no resources from this project | `resources.vpc[]` | low |
| hyg-012 | a project has no `environment` or `purpose` set | `inventory.project` | low |
| hyg-013 | a serverless namespace exists with no functions deployed | `serverless namespaces list` | low |

`hyg-002` is a `high` and looks like a `low`. DigitalOcean does not enforce unique names, and most
`doctl` commands that accept a name act on whichever one the API returns first. Two droplets called
`web-01` means every future command against `web-01` is a coin flip, including the destructive ones.

`hyg-003` produces wrong numbers if you read the text output. `doctl compute tag get <tag-name>`
offers exactly two columns, `Name` and `DropletCount`, so a tag applied only to volumes or databases
prints 0 and looks unused. The `-o json` form does carry the full breakdown, a `resources` object
with a `count` plus separate `droplets`, `images`, `volumes`, `volume_snapshots`, and `databases`
entries. Use the JSON, or count membership from `inventory.json`.

`hyg-008` is `high` on purpose. A gap means part of the audit did not run, and a report that looks
clean because a lister failed is worse than no report.

## Commands beyond the inventory

```bash
doctl compute tag list
doctl kubernetes cluster list-associated-resources <cluster-id>
doctl compute domain records list <domain>
doctl serverless namespaces list
doctl projects list
```
