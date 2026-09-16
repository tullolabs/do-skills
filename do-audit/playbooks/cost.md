# Audit: cost and waste

> **Read-only.** Run `list` and `get` only. Never create, update, delete, or start anything.
> Write `raw/cost.jsonl` and `raw/cost.md`. Touch no other file.
> Never emit a credential value. Reference a secret by name.

Pull slices of `inventory.json` rather than loading it whole; see the dispatch note in `SKILL.md`.
Use `prices.json` for the droplet size catalog, whose `sizes` map is
`slug -> [usd_mo, vcpus, memory_mb, disk_gb]`.

Prices below are DigitalOcean list prices and are the estimate, not the bill. The account's real
numbers come from `doctl invoice summary <invoice-uuid>`, and `doctl balance get` shows the
month-to-date total. Quote list prices in `usd_mo` and say in `raw/cost.md` that they are estimates.

## Checks

Ids are fixed. Use the id in this table even when the check finds nothing on this run, so two runs
diff cleanly.

| id | Finding when | Source | sev | usd_mo |
|---|---|---|---|---|
| cost-001 | `droplet_ids` is empty | `resources.volume[]` | high | `size_gigabytes` × 0.10 |
| cost-002 | no droplet is attached (`droplet` is null; the text column is `DropletID`) | `resources.floatingip[]` | med | 4.50 |
| cost-003 | `resource_id` names a droplet or volume that is gone | `resources.snapshot[]` | med | `size_gigabytes` × 0.06 |
| cost-004 | `status` is `off` | `resources.droplet[]` | high | the size's `usd_mo` |
| cost-005 | size is CPU-optimized or premium where a basic slug has the same vcpus and memory for less | `resources.droplet[]` joined to `prices.json` | low | the difference |
| cost-006 | `num_nodes` > 1 on a non-production database | `resources.dbaas[]` | low | per-node price × extra nodes |
| cost-007 | the HA control plane is on (text column `HAControlPlane`) | `kubernetes cluster get <cluster-id>` | med | 40.00 |
| cost-008 | `droplet_ids` and `tag` are both empty on a load balancer | `resources.loadbalancer[]` | high | 12.00 |
| cost-009 | autoscale pool exists but its target droplets do not | `compute droplet-autoscale list` | med | null |
| cost-010 | a private image older than 90 days that no droplet was built from | `compute image list-user` | low | `size_gigabytes` × 0.05 |
| cost-011 | `tags` is absent, empty, or null | any resource in `inventory.json` | low | null |
| cost-012 | a database's `storage_size_mib` exceeds the plan default and nothing uses the headroom | `resources.dbaas[]` | low | null |

`cost-004` is the one people do not believe. A droplet powered off from the control panel keeps its
disk and its IP reserved, so it bills at the full rate. Only a destroy stops the meter.

`cost-011` is not waste by itself. It is the reason the other numbers cannot be attributed to a
team or an environment, which is why it is worth one low finding rather than twelve. Read it with
`.get("tags")`, not `["tags"]`: on an untagged droplet the key is absent rather than `[]`, verified
against two untagged droplets on the reference account.

## Commands beyond the inventory

```bash
doctl compute droplet-autoscale list
doctl compute image list-user
doctl balance get
doctl invoice list
doctl invoice summary <invoice-uuid>
doctl kubernetes cluster get <cluster-id>
```

## Report the total honestly

Sum `usd_mo` across findings where it is a number, and put that in `raw/cost.md` as
"estimated monthly waste". Findings with `usd_mo: null` are real but unpriced. Say how many there
are rather than folding a guess into the total.
