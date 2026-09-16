# Audit: performance and latency

> **Read-only.** Run `list` and `get` only. Never create, update, delete, or start anything.
> Write `raw/performance.jsonl` and `raw/performance.md`. Touch no other file.
> Never emit a credential value. Reference a secret by name.

**Say this in `raw/performance.md` before anything else: `doctl` exposes no utilization metrics.**
There is no CPU percentage, no request latency, no connection count, no query time anywhere in the
CLI. Everything below is configuration review. A finding here means "this is configured in a way
that costs latency", never "this is measurably slow". Presenting it as measured would be a lie the
report's own shape makes easy to tell.

## Checks

| id | Finding when | Source | sev |
|---|---|---|---|
| perf-001 | a Postgres or MySQL cluster has no connection pool | `databases pool list <database-id>` | high |
| perf-002 | a droplet and the database it talks to are in different regions | `resources.droplet[].region`, `resources.dbaas[].region` | high |
| perf-003 | an app and its database are in different regions | `resources.app[].region`, `resources.dbaas[].region` | high |
| perf-004 | a CDN endpoint's `ttl` is still 3600 | `account_wide.cdn[]` | med |
| perf-005 | a droplet reaches a database over the public network rather than the VPC | `resources.dbaas[].private_network_uuid` vs `resources.droplet[].vpc_uuid` | high |
| perf-006 | a load balancer's `check_interval_seconds` is above 10 | `compute load-balancer get <load-balancer-id>` | low |
| perf-007 | a stored spec or template still sets a load balancer `algorithm` | the operator's own config, not `doctl` | low |
| perf-008 | an app component runs a single instance | `resources.app[].spec` | med |
| perf-009 | a database engine version is more than one major behind the latest available | `databases options engines` | med |
| perf-010 | a droplet uses a non-SSD or older size family where a current one costs the same | `prices.json` | low |
| perf-011 | an OpenSearch cluster has no index defined | `databases indexes list <database-id>` | low |
| perf-012 | a Kafka topic has one partition | `databases topics list <database-id>` | med |
| perf-013 | a static site is served from an app rather than Spaces with CDN | `resources.app[].spec` | low |

`perf-007` cannot be answered from `doctl` and is here so you do not go looking. The flag's own help
text reads "This field has been deprecated. You can no longer specify an algorithm for load
balancers", and `compute load-balancer get --help` does not offer `Algorithm` as a column at all, so
a live load balancer will never report one. Raise it only if the operator's own Terraform or app spec
still sets it, where it describes routing that is not happening. Otherwise put it in `## Not checked`.

`perf-005` is the one worth chasing first. A database reached over its public hostname pays an extra
network hop and TLS termination on every connection, and the fix is a connection string change with
no downtime. The tell is a cluster with `private_network_uuid` set that nothing is using.

`perf-002` and `perf-003` need the operator's answer about where users actually are. Record the
region mismatch as fact, and put the "far from users" judgement in `raw/performance.md` as a
question rather than inventing a user base.

## Commands beyond the inventory

```bash
doctl databases pool list <database-id>
doctl databases options engines
doctl databases indexes list <database-id>
doctl databases topics list <database-id>
doctl compute load-balancer get <load-balancer-id>
doctl compute cdn get <cdn-id>
doctl apps spec get <app-id>
```
