# Audit: capacity and scaling

> **Read-only.** Run `list` and `get` only. Never create, update, delete, or start anything.
> Write `raw/capacity.jsonl` and `raw/capacity.md`. Touch no other file.
> Never emit a credential value. Reference a secret by name.

Headroom, not load. Without utilization metrics the question is never "is this at 90%", it is "when
this fills up or spikes, does anything grow, and does anyone find out". A resource that cannot
scale and has no alert on it is the finding.

## Checks

| id | Finding when | Source | sev |
|---|---|---|---|
| cap-001 | an autoscale pool has `min_instances` equal to `max_instances` | `compute droplet-autoscale get <autoscale-pool-id>` | med |
| cap-002 | a Kubernetes node pool has `auto_scale: false` | `kubernetes cluster node-pool list <cluster-id>` | med |
| cap-003 | a Kubernetes pool has `auto_scale: true` but `min_nodes` equals `max_nodes` | `kubernetes cluster node-pool list <cluster-id>` | med |
| cap-004 | a database cluster has storage autoscale disabled | `databases storage-autoscale get <database-id>` | high |
| cap-005 | a volume is the same size as when created and its droplet has grown | `resources.volume[]` | low |
| cap-006 | a Kafka topic has `replication_factor: 1` | `databases topics list <database-id>` | high |
| cap-007 | an app component has no `autoscaling` block and a fixed `instance_count` | `resources.app[].spec` | med |
| cap-008 | no alert policy of type `disk_utilization` or `memory_utilization` covers a droplet | `resources.alert[]` | high |
| cap-009 | a droplet's size is the smallest in its family and it is not a bastion or toy | `prices.json` | low |
| cap-010 | a Kubernetes cluster has upgrades available | `kubernetes cluster get-upgrades <cluster-id>` | med |
| cap-011 | a database's `storage_size_mib` is at the plan minimum on a cluster older than 90 days | `resources.dbaas[]` | low |
| cap-012 | a reserved IP count or droplet count is near an account limit | `doctl account get` | low |

`cap-004` earns the high. A managed database that fills its disk goes read-only, and storage
autoscale is off by default on most plans. It is the cheapest single setting in this whole audit.

`cap-008` matters more than it reads. Every other check here is about whether something can grow.
This one is about whether anyone will know it needs to, and an unmonitored resource that cannot
autoscale is the pager at 3am.

`cap-005`, `cap-009`, and `cap-011` are judgement calls with no metric behind them. Write them as
questions in `raw/capacity.md` and only emit a finding if the evidence is concrete, for example a
90 GiB volume on a droplet whose own disk is 25 GiB.

## Commands beyond the inventory

```bash
doctl compute droplet-autoscale list
doctl compute droplet-autoscale get <autoscale-pool-id>
doctl compute droplet-autoscale list-members <autoscale-pool-id>
doctl kubernetes cluster node-pool list <cluster-id>
doctl kubernetes cluster get-upgrades <cluster-id>
doctl databases storage-autoscale get <database-id>
doctl databases topics list <database-id>
doctl account get
```
