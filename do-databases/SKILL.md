---
name: do-databases
description: Use for any DigitalOcean managed database task. List and inspect Postgres, MySQL, MongoDB, Kafka, OpenSearch, and Valkey clusters, get connection strings and CA certs, add trusted sources to the firewall, create connection pools, resize, and delete.
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
doctl databases pool create <id> <pool-name> --mode transaction --size 10 --db <dbname> --user <user>

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

## Gotchas

**A new cluster is open to the public internet,** reachable by anyone holding the credentials over TLS. Trusted sources are opt-in, not a default deny. Add them as soon as the cluster exists.

**Once rules exist, "connection timed out" is the firewall, not the credentials.** A wrong password fails fast with an auth error. A timeout means the source IP is not on the trusted list.
