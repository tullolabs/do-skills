# Audit: reliability and backups

> **Read-only.** Run `list` and `get` only. Never create, update, delete, or start anything.
> Write `raw/reliability.jsonl` and `raw/reliability.md`. Touch no other file.
> Never emit a credential value. Reference a secret by name.

The question this playbook answers is "what happens when one thing dies". Every finding should name
what is lost and how far back the restore point goes.

## Checks

| id | Finding when | Source | sev |
|---|---|---|---|
| rel-001 | a droplet has no entry in `resources.backup_policy` | `resources.droplet[]` | high |
| rel-002 | a droplet's backup policy exists but its newest backup is older than 8 days | `compute droplet backups <droplet-id>` | high |
| rel-003 | a droplet has no snapshot and no backup at all | `resources.snapshot[]`, `resources.backup_policy` | crit |
| rel-004 | a database cluster has `num_nodes: 1` | `resources.dbaas[]` | high |
| rel-005 | a database cluster's newest backup is older than 24 hours | `databases backups <database-id>` | crit |
| rel-006 | a database has no read replica and serves production traffic | `databases replica list <database-id>` | med |
| rel-007 | a Kubernetes node pool has `count: 1` | `kubernetes cluster node-pool list <cluster-id>` | high |
| rel-008 | a load balancer's health check path is `/` | `compute load-balancer get <load-balancer-id>` | med |
| rel-009 | a load balancer has fewer than two droplets or a tag matching fewer than two | `resources.loadbalancer[]` | high |
| rel-010 | a droplet has no alert policy in `resources.alert` | `resources.alert[]` | med |
| rel-011 | no uptime check targets a live app URL or load balancer IP | `monitoring uptime list`, `resources.app[].live_url` | med |
| rel-012 | a maintenance window falls inside the service's busy hours | `databases maintenance-window get <database-id>` | low |
| rel-013 | an app component has no `health_check` block | `resources.app[].spec` | med |

`rel-008` looks pedantic and is not. A health check on `/` passes whenever the web server is up,
including when the app behind it cannot reach its database. The load balancer then keeps routing to
a droplet that returns 500 to every request.

`rel-005` is the crit because it is the only one where the damage is already done. A cluster whose
most recent restore point is two days old has silently lost two days of recoverability, and nothing
surfaces that until someone needs it.

## Commands beyond the inventory

```bash
doctl compute droplet backups <droplet-id>
doctl databases backups <database-id>
doctl databases replica list <database-id>
doctl databases maintenance-window get <database-id>
doctl kubernetes cluster node-pool list <cluster-id>
doctl compute load-balancer get <load-balancer-id>
doctl monitoring uptime list
doctl monitoring uptime alert list <uptime-check-id>
```
