# Audit: security and exposure

> **Read-only.** Run `list` and `get` only. Never create, update, delete, or start anything.
> Write `raw/security.jsonl` and `raw/security.md`. Touch no other file.
> Never emit a credential value. Reference a secret by name.

This is the playbook most likely to handle sensitive output, so the rule is absolute: a finding
names a resource, a port, a CIDR, or a user name. It never contains a password, a URI with
credentials in it, a token, or a private key. `inventory.json` is already redacted; anything you run
yourself is not.

**Never run these.** Their entire output is a live credential: `doctl auth token`,
`databases connection`, `databases replica connection`, `vector-databases credentials`,
`registry docker-config`, `registry kubernetes-manifest`, `kubernetes cluster kubeconfig show`,
`network attachment get-service-key`, `network attachment get-bgp-auth-key`, `secrets get --show`.
`databases user list` and `databases pool list` are also credential-bearing; if you run them, take
only the name and role fields.

## Checks

| id | Finding when | Source | sev |
|---|---|---|---|
| sec-001 | an inbound rule allows `0.0.0.0/0` on port 22 | `resources.firewall[].inbound_rules` | crit |
| sec-002 | an inbound rule allows `0.0.0.0/0` with `ports: all` | `resources.firewall[].inbound_rules` | crit |
| sec-003 | a droplet appears in no firewall's `droplet_ids` and matches no firewall tag | `resources.droplet[]` vs `resources.firewall[]` | crit |
| sec-004 | a database cluster's trusted-source list is empty | `databases firewalls list <database-id>` | crit |
| sec-005 | a certificate's `not_after` is within 30 days | `account_wide.certificate[]` | high |
| sec-006 | a certificate's `state` is not `verified` | `account_wide.certificate[]` | high |
| sec-007 | a CSPM scan reports a high or critical finding | `doctl security scans latest` | high |
| sec-008 | a Gradient agent's visibility is `VISIBILITY_PUBLIC` | `genai agent list` | high |
| sec-009 | an inbound rule allows a database port (5432, 3306, 27017, 6379, 9092, 9200) from `0.0.0.0/0` | `resources.firewall[].inbound_rules` | crit |
| sec-010 | a database user's role is not the least privilege the app needs | `databases user list <database-id>`, names and roles only | med |
| sec-011 | an app spec exposes a component with no `health_check` and a wildcard route | `resources.app[].spec` | med |
| sec-012 | a droplet has a public IPv4 but no firewall and no cloud load balancer in front | `resources.droplet[].networks` | high |
| sec-013 | a bucket appears in `inventory.spaces` | see below | med |

`sec-004` deserves the crit. A DigitalOcean managed database with no trusted sources is reachable
from any address on the internet that has the connection string. It is not firewalled by default;
the trusted-source list is the firewall.

`sec-013` is a reporting obligation, not a check. `doctl spaces` cannot list buckets or read their
ACLs at all, so every bucket in scope is an unknown. Record one finding per bucket at `med` saying
its public-read status was not determined, and repeat it in `## Not checked`.

A 403 from `security scans` or from Secrets Manager means the token lacks that scope. That is a
coverage gap for `## Not checked`, not a finding and not something to retry.

## Commands beyond the inventory

```bash
doctl databases firewalls list <database-id>
doctl databases user list <database-id>
doctl security scans latest
doctl genai agent list
doctl compute firewall get <firewall-id>
doctl compute load-balancer get <load-balancer-id>
```
