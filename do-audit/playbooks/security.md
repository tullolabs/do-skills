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
| sec-014 | an app env key names a credential but its `type` is not `SECRET` | `resources.app[].spec` envs | med |

`sec-004` deserves the crit. A DigitalOcean managed database with no trusted sources is reachable
from any address on the internet that has the connection string. It is not firewalled by default;
the trusted-source list is the firewall.

`sec-014` reads the env key and type only. `inventory.py` blanks every env `value`, including the
`EV[1:...]` ciphertext DigitalOcean returns for `SECRET` entries, so there is nothing to leak and
nothing to compare. Quote the key name, never a value.

Match the key name with these three rules together, not a substring search. A substring search for
`KEY` or `TOKEN` returned 19 hits on a 67-app account and every one was a false positive:
`AUTO_LOAD_SOLANA_KMS_KEYS` is a boolean, `SOLANA_DEFAULT_KEY_ALIAS` is an alias,
`NEXT_PUBLIC_BSC_BRIDGE_TOKENS` is a list of ERC-20 contracts.

- The key ends in a **singular** credential word: `KEY`, `TOKEN`, `SECRET`, `PASSWORD`, `PASSWD`,
  `MNEMONIC`, `SEED`, `DSN`, preceded by `_` or the start of the string. A plural is a list or a flag.
- Skip framework-public prefixes, which are compiled into a client bundle by design and so cannot
  be secret: `NEXT_PUBLIC_`, `VITE_`, `REACT_APP_`, `PUBLIC_`, `GATSBY_`, `EXPO_PUBLIC_`.
- Skip keys ending in `_URL`, `_URI`, `_ALIAS`, `_ID`, `_NAME`, `_ENABLED`, `_PATH`, `_HOST`,
  `_PORT`, `_REGION`, `_MODE`, or starting with `AUTO_` or `ENABLE`.

Those three rules together produced zero hits on the same 67 apps, which is the right answer for that
account. This is still a name heuristic and cannot see what a value holds, so read the key in context
before reporting it and drop it if the name is explainable.

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
