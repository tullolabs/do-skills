---
name: do-dns
description: DigitalOcean DNS. Use for domains and zones, A, CNAME, TXT, and MX records, and delegating nameservers to ns1, ns2, ns3.digitalocean.com.
user-invocable: true
argument-hint: "[list|add|update|delete] [domain]"
---

# DNS and Domains

> Destructive ops need operator approval. Reads are always safe.
> Auth: `doctl` is pre-authenticated. See `/do-ops` for auth contexts.

```bash
# --- Domain (zone) ---

doctl compute domain list

# Shows TTL + zone file
doctl compute domain get example.com

# Add a domain you already own (⚠️ requires approval)
doctl compute domain create example.com
# ...and seed an A record for @
doctl compute domain create example.com --ip-address <ip>   # (⚠️ requires approval)

# Remove a domain AND all its records (⚠️ requires approval — destructive)
doctl compute domain delete example.com

# --- Records ---

doctl compute domain records list example.com

# (⚠️ requires approval)
doctl compute domain records create example.com \
  --record-type A \
  --record-name @ \
  --record-data <ip>

# (⚠️ requires approval)
doctl compute domain records create example.com \
  --record-type CNAME \
  --record-name www \
  --record-data @

# Domain verification / SPF (⚠️ requires approval)
doctl compute domain records create example.com \
  --record-type TXT \
  --record-name @ \
  --record-data "v=spf1 include:_spf.google.com ~all"

# Mail routing; priority is a separate flag (⚠️ requires approval)
doctl compute domain records create example.com \
  --record-type MX \
  --record-name @ \
  --record-data aspmx.l.google.com. \
  --record-priority 1

# (⚠️ requires approval)
doctl compute domain records update example.com \
  --record-id <id> \
  --record-data <new-value>

# (⚠️ requires approval)
doctl compute domain records delete example.com <record-id>
```

## Gotchas

**DigitalOcean only serves DNS once nameservers are delegated.** Adding a domain in DO does nothing until the registrar's nameservers point to `ns1.digitalocean.com`, `ns2.digitalocean.com`, `ns3.digitalocean.com`. DO is not a registrar — domains are bought elsewhere, then delegated here.

**`records update` needs `--record-id` as a flag, while `records delete` takes the ID as a positional.** The two commands disagree on shape for the same value, so copying one into the other fails. `delete` is also variadic (`<domain> <record-id>...`), so a stray ID on the line removes a second record.
