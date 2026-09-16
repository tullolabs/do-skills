---
name: do-databases
description: Use for any DigitalOcean managed database task. Create, fork, migrate, resize, and delete Postgres, MySQL, MongoDB, Kafka, OpenSearch, and Valkey clusters, manage databases, users, connection pools, trusted-source firewalls, replicas, topics, indexes, and backups.
user-invocable: true
argument-hint: "[list|connect|pool|firewall] [cluster]"
---

# Databases

> Destructive ops need operator approval. Reads are always safe.
> Auth: `doctl` is pre-authenticated. See `/do-ops` for auth contexts.

```bash
# List clusters
doctl databases list

# Get cluster details
doctl databases get <id>

# Connection string
doctl databases connection <id>

# List DBs within a cluster
doctl databases db list <id>

# List users
doctl databases user list <id>

# CA cert — required for sslmode=verify-full clients
doctl databases get-ca <id>

# Trusted sources (the firewall). Empty list means open to the internet. Add rules on day one.
doctl databases firewalls list <id>
doctl databases firewalls append <id> --rule ip_addr:<ip>       # (⚠️ requires approval)
doctl databases firewalls append <id> --rule app:<app-uuid>     # (⚠️ requires approval)
doctl databases firewalls append <id> --rule droplet:<id>       # (⚠️ requires approval)

# Connection pooling (PostgreSQL — use this instead of raising max connections)
doctl databases pool list <id>
doctl databases pool create <id> <pool-name> --mode transaction --size 10 --db <dbname> --user <user>   # (⚠️ requires approval)

# Resize / autoscale storage (⚠️ requires approval)
doctl databases resize <id> --size <slug> --num-nodes <n>
doctl databases storage-autoscale get <id>

# Delete (⚠️ requires approval)
doctl databases delete <id>
```

Engine slugs the API currently offers: `pg`, `advanced_pg`, `mysql`, `advanced_mysql`, `mongodb`, `kafka`, `opensearch`, `valkey`.
Use `valkey` for anything new. `redis` is still a live slug for reading and managing existing Caching clusters,
but DO stopped accepting Caching cluster creates on 2025-04-30, so `create --engine redis` fails even though
the help text still lists it. `doctl databases options engines` reflects what you can actually create.

### Cluster lifecycle

`create` and `fork` take the new cluster's name as a positional; every other input is a flag. `fork` requires
`--restore-from-cluster-id` and `migrate` requires `--region`. Check size and version with `options` first.

```bash
# --- Lookups (read-only) ---
doctl databases options engines
doctl databases options versions --engine pg
doctl databases options slugs --engine pg       # --engine is required on slugs
doctl databases options regions --engine pg

# --- Lifecycle ---
# Create a cluster (⚠️ requires approval)
doctl databases create my-cluster --engine pg --version <version> --region nyc1 --size db-s-1vcpu-1gb --num-nodes 1 --wait

# Restore into a new cluster from another cluster's backup (⚠️ requires approval)
doctl databases create my-cluster --restore-from-cluster-name <cluster-name> --restore-from-timestamp "2006-01-02 15:04:05 +0000 UTC"

# Fork an existing cluster, referenced by ID, into a new one (⚠️ requires approval)
doctl databases fork my-fork --restore-from-cluster-id <id> --wait
# Move a cluster to another region (⚠️ requires approval)
doctl databases migrate <id> --region sfo2 --wait
```

With no flags, `create` gives you a single-node `db-s-1vcpu-1gb` PostgreSQL cluster in `nyc1`. Both
restore paths use the most recent backup when `--restore-from-timestamp` is omitted.

### Databases and users

```bash
# --- Databases inside a cluster ---
doctl databases db get <id> <database-name>
doctl databases db create <id> <database-name>          # (⚠️ requires approval)
doctl databases db delete <id> <database-name>          # (⚠️ requires approval — drops the database and its data)

# --- Users ---
doctl databases user get <id> <user-name> --format Name,Role,Password   # create generates the password; this reads it
doctl databases user create <id> <user-name>                                       # (⚠️ requires approval)
doctl databases user create <id> <user-name> --acl <topic>:<permission>            # (⚠️ requires approval) Kafka ACLs
doctl databases user create <id> <user-name> --opensearch-acl <index>:<permission> # (⚠️ requires approval) OpenSearch ACLs
doctl databases user create <id> <user-name> --mysql-auth-plugin caching_sha2_password   # (⚠️ requires approval)
# Rotate credentials. The third positional is the auth mode and is not optional. (⚠️ requires approval)
doctl databases user reset <id> <user-name> mysql_native_password
# Usage says <user-id> but it takes the user name (⚠️ requires approval)
doctl databases user delete <id> <user-name>
```

### Connection pools

```bash
doctl databases pool get <id> <pool-name> --format Name,URI
doctl databases pool update <id> <pool-name> --size 20 --mode session   # (⚠️ requires approval)
doctl databases pool delete <id> <pool-name>                            # (⚠️ requires approval)
```

`--db` and `--size` are required on `pool create`; omitting `--user` points the pool at the inbound user
instead of failing. `--mode` takes `session`, `transaction`, or `statement` and defaults to `transaction`,
not to the `--mode session` the help renders.

### Firewall rules (trusted sources)

Every rule is a `<type>:<value>` pair. Valid types are `droplet`, `k8s`, `ip_addr`, `tag`, and `app`.
`append` adds one rule, `remove` takes a rule UUID from `firewalls list`, `replace` overwrites the whole set.

```bash
doctl databases firewalls append <id> --rule tag:example-tag    # (⚠️ requires approval)
doctl databases firewalls remove <id> --uuid <rule-uuid>        # (⚠️ requires approval)
# Comma-separated, and it is --rule singular even when you pass several (⚠️ requires approval — discards every rule not listed)
doctl databases firewalls replace <id> --rule ip_addr:<ip>,droplet:<droplet-id>,tag:example-tag
```

### Read-only replicas

```bash
# Replicas are addressed by name, always through the primary cluster's ID
doctl databases replica list <id>
doctl databases replica get <id> <replica-name>
doctl databases replica connection <id> <replica-name>
# --size must be at least as large as the primary (⚠️ requires approval)
doctl databases replica create <id> <replica-name> --size db-s-1vcpu-1gb --region nyc3
doctl databases replica promote <id> <replica-name>   # (⚠️ requires approval — replication stops for good)
doctl databases replica delete <id> <replica-name>    # (⚠️ requires approval)
```

### Kafka topics and partitions

```bash
doctl databases topics list <id>
doctl databases topics get <id> <topic-name>
doctl databases topics partitions <id> <topic-name>   # per-partition size, in-sync replicas, earliest offset
# Defaults are 1 partition and a replication factor of 2 (⚠️ requires approval)
doctl databases topics create <id> <topic-name> --partition-count 4 --replication-factor 2
# create and update share ~25 broker-config flags: --cleanup-policy, --compression-type, --segment-bytes (⚠️ requires approval)
doctl databases topics update <id> <topic-name> --retention-ms 604800000
doctl databases topics delete <id> <topic-name>   # (⚠️ requires approval — the topic's messages go with it)
```

### OpenSearch indexes

```bash
doctl databases indexes list <id>
doctl databases indexes delete <id> <index-name>   # (⚠️ requires approval — the documents go with it)
```

### Configuration, SQL modes, and maintenance

`configuration` needs `-e/--engine` on both subcommands. The update is a PATCH, so a partial `--config-json`
object leaves every unnamed setting alone.

```bash
doctl databases configuration get <id> --engine pg
doctl databases configuration update <id> --engine mysql --config-json '{"default_time_zone":"Africa/Maputo"}'   # (⚠️ requires approval)

# MySQL only. The set is replaced wholesale, so repeat the modes you want to keep.
doctl databases sql-mode get <id>
doctl databases sql-mode set <id> NO_ZERO_DATE NO_ZERO_IN_DATE STRICT_ALL_TABLES ALLOW_INVALID_DATES   # (⚠️ requires approval)

doctl databases maintenance-window get <id>
doctl databases maintenance-window update <id> --day tuesday --hour 16:00   # (⚠️ requires approval)
doctl databases maintenance-window install <id>   # (⚠️ requires approval — runs pending updates now instead of at the window)
```

### Storage autoscaling, backups, and events

```bash
# --enabled is required and must be true or false. Omit the other two for the defaults of 80% and 10 GiB.
doctl databases storage-autoscale update <id> --enabled true --threshold-percent 80 --increment-gib 10   # (⚠️ requires approval)
doctl databases storage-autoscale update <id> --enabled false                                            # (⚠️ requires approval)

doctl databases backups <id>       # size and creation time of every retained backup
doctl databases events list <id>   # cluster-level events: resizes, migrations, maintenance
```

## Gotchas

**A new cluster is open to the public internet,** reachable by anyone holding the credentials over TLS. Trusted sources are opt-in, not a default deny. Add them as soon as the cluster exists.

**Once rules exist, "connection timed out" is the firewall, not the credentials.** A wrong password fails fast with an auth error. A timeout means the source IP is not on the trusted list.

**The flag on `firewalls replace` is `--rule`, not `--rules`.** Both the `Usage:` line and the built-in example print `--rules`, and both are wrong — `doctl` answers with `Error: unknown flag: --rules`. The same command silently discards every rule you leave out of the comma-separated list, so read `firewalls list` first and re-pass what you want to keep.

**`topics create` documents its own flags with underscores that do not exist.** The example reads `--replication_factor 2 --partition_count 4`; the registered flags are `--replication-factor` and `--partition-count`. Underscores fail with `Error: unknown flag: --replication_factor`.

**`backups` has no `list` subcommand.** It is `doctl databases backups <id>`, with the cluster ID as the only positional. `doctl databases backups list <id>` reads `list` as the cluster ID and looks up a cluster that does not exist.
