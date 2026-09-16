---
name: do-k8s
description: DigitalOcean Kubernetes. Use for DOKS clusters, node pools and autoscaling, kubeconfig for kubectl, version upgrades, orphaned load balancers and volumes, and container registry integration.
user-invocable: true
argument-hint: "[create|kubeconfig|upgrade|delete] [cluster]"
---

# Kubernetes

> Destructive ops need operator approval. Reads are always safe.
> Auth: `doctl` is pre-authenticated. See `/do-ops` for auth contexts.

### Clusters

DOKS keeps its own region, size, and version lists that do not match the Droplet ones, so check `options`
before every create. `--region` is marked required even though it defaults to `nyc1`. `--node-pool` is one
quoted, semicolon-separated string, incompatible with `--size` and `--count`; its keys are `name`, `size`,
`count`, `tag`, `label` as `key=value`, `taint` as `key=value:effect`, `auto-scale`, `min-nodes`, `max-nodes`.

```bash
# --- Valid inputs ---
doctl kubernetes options regions
doctl kubernetes options sizes           # valid inside a node pool
doctl kubernetes options versions        # version slugs, e.g. 1.34.1-do.0

# --- Read ---
doctl kubernetes cluster list
doctl kubernetes cluster get <cluster-id|cluster-name>

# (⚠️ requires approval). --wait defaults true, so this blocks.
doctl kubernetes cluster create my-cluster --region sgp1 --version latest --ha \
  --maintenance-window saturday=02:00 \
  --node-pool "name=default-pool;size=s-2vcpu-4gb;count=3;auto-scale=true;min-nodes=2;max-nodes=5"
# Shorthand: one default pool, no --node-pool (⚠️ requires approval)
# Pass --ha=false explicitly if you do not want a billable HA control plane, see gotchas.
doctl kubernetes cluster create my-cluster --region sgp1 --size s-2vcpu-4gb --count 3 --ha=false

# Rename with --cluster-name; there is no positional new name.
doctl kubernetes cluster update <cluster-id|cluster-name> --cluster-name new-name --auto-upgrade=true   # (⚠️ requires approval)
```

### Node pools

```bash
doctl kubernetes cluster node-pool list <cluster-id|cluster-name>
doctl kubernetes cluster node-pool get <cluster-id|cluster-name> <pool-id|pool-name>
# --name, --size, and --count are all required (⚠️ requires approval)
doctl kubernetes cluster node-pool create <cluster-id|cluster-name> --name worker-pool \
  --size s-4vcpu-8gb --count 3 --auto-scale --min-nodes 2 --max-nodes 6 --taint "workload=batch:NoSchedule"
doctl kubernetes cluster node-pool update <cluster-id|cluster-name> <pool-id|pool-name> --count 5   # (⚠️ requires approval) scale

# Recycle one node; Kubernetes drains it first unless you pass --skip-drain (⚠️ requires approval)
doctl kubernetes cluster node-pool delete-node <cluster-id|cluster-name> <pool-id|pool-name> <node-id>
# Same, but a replacement node comes up in its place — for a node stuck in a bad state
doctl kubernetes cluster node-pool replace-node <cluster-id|cluster-name> <pool-id|pool-name> <node-id>   # (⚠️ requires approval)
# Delete a pool and every node inside it (⚠️ requires approval — irreversible)
doctl kubernetes cluster node-pool delete <cluster-id|cluster-name> <pool-id|pool-name>
```

### kubeconfig and upgrades

`save` merges a context into your existing `~/.kube/config`, leaving other clusters alone; it never replaces
the file. `show` prints the YAML to stdout and writes nothing to disk.

```bash
doctl kubernetes cluster kubeconfig save <cluster-id|cluster-name>
doctl kubernetes cluster kubeconfig save <cluster-id|cluster-name> --alias my-cluster --set-current-context=false
doctl kubernetes cluster kubeconfig show <cluster-id|cluster-name>
doctl kubernetes cluster kubeconfig show <cluster-id> --type token --expiry-seconds 3600   # static token for CI
# Drop the context locally (⚠️ requires approval — local file only, `save` puts it back)
doctl kubernetes cluster kubeconfig remove <cluster-id|cluster-name>

# --- Upgrades ---
doctl kubernetes cluster get-upgrades <cluster-id|cluster-name>
doctl kubernetes cluster upgrade <cluster-id|cluster-name> --version 1.34.1-do.0   # (⚠️ requires approval)
doctl kubernetes cluster upgrade <cluster-id|cluster-name>   # (⚠️ requires approval — --version defaults to `latest`)
```

### Deleting a cluster

```bash
# Run first: the volumes, volume snapshots, and load balancers the CSI driver and service controller made
doctl kubernetes cluster list-associated-resources <cluster-id|cluster-name>
# Cluster and worker Droplets only (⚠️ requires approval)
doctl kubernetes cluster delete <cluster-id|cluster-name>
# Cluster plus all LBs, volumes, and volume snapshots (⚠️ requires approval — irreversible)
doctl kubernetes cluster delete <cluster-id|cluster-name> --dangerous
# Cluster plus only the resources you list (⚠️ requires approval — irreversible)
doctl kubernetes cluster delete-selective <cluster-id|cluster-name> \
  --load-balancers <lb-id> --volumes <volume-id> --snapshots <snapshot-id>
```

### Registry and 1-click apps

`registry add` installs DigitalOcean Container Registry pull credentials into the cluster. Both registry
subcommands accept several clusters as repeated positionals. See `/do-registry`.

```bash
doctl kubernetes cluster registry add <cluster-id|cluster-name> <cluster-id|cluster-name>   # (⚠️ requires approval)
# Revoke pull access (⚠️ requires approval — pods can no longer pull new images)
doctl kubernetes cluster registry remove <cluster-id|cluster-name>

# --- 1-click apps ---
doctl kubernetes 1-click list
doctl kubernetes 1-click install <cluster-id> --1-clicks loki,netdata   # (⚠️ requires approval)
```

## Gotchas

**Deleting a cluster leaves its load balancers and volumes behind, still billing.** Plain `doctl kubernetes cluster delete` removes only the cluster and its worker Droplets. The LBs the service controller provisioned and the volumes the CSI driver provisioned survive as orphans. Run `doctl kubernetes cluster list-associated-resources <cluster-id>` first, then either pass `--dangerous` or name them with `delete-selective`. There is no `delete-dangerous` subcommand; full teardown is the `--dangerous` flag on `delete`.

**The `delete-selective --help` example prints flags that do not exist.** It shows `--volume-list` and `--load-balancer-list`. The real flags are `--volumes`, `--load-balancers`, and `--snapshots`. Copying the example verbatim fails with `unknown flag: --volume-list`. The `1-click install` help text has the same problem: it names `--1-click`, the flag is `--1-clicks`.

**`kubeconfig save` merges, then hijacks your current context.** `--set-current-context` defaults to true, so your next bare `kubectl` command targets the cluster you just saved. Pass `--set-current-context=false` when you only want the context available.

**`node-pool update` replaces tags, labels, and taints instead of merging them.** Per `--help`, an existing tag, label, or taint is removed from the pool if the flag does not name it. Repeat the full set on every update, or pass `--taint ""` deliberately to clear them.

**Omitting `--ha` does not mean you get a cheap control plane.** Per `create --help`, when the flag is omitted the API applies a version-specific default, and that default is **true** on Kubernetes 1.36.0 and newer. Since `--version latest` tracks a version well past 1.36, the shorthand create provisions a highly-available control plane and bills for it. Pass `--ha=false` when you want the single control plane. `cluster update` also takes `--ha`, but its help text only describes enabling HA, so treat the create-time choice as the one that sticks.
