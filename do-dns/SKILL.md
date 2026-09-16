---
name: do-dns
description: DigitalOcean DNS and domain operations with doctl. Use for listing domains, adding or deleting a zone, and creating, updating, or deleting DNS records such as A, CNAME, TXT, and MX. Also covers delegating nameservers to ns1, ns2, and ns3.digitalocean.com.
user-invocable: true
argument-hint: "[list|add|update|delete] [domain]"
---

# DNS and Domains

> Destructive ops need operator approval. Reads are always safe.
> Auth: `doctl` is pre-authenticated. See `/do-ops` for auth contexts.

Managing a domain you already own. Two levels: the **domain** resource (the zone) and the **records** inside it.

```bash
# --- Domain (zone) ---

# List domains
doctl compute domain list

# Get a domain (shows TTL + zone file)
doctl compute domain get example.com

# Add a domain you already own to DO (⚠️ requires approval)
doctl compute domain create example.com
# ...optionally seed an A record for @ at the same time:
doctl compute domain create example.com --ip-address <ip>

# Remove a domain AND all its records (⚠️ requires approval — destructive)
doctl compute domain delete example.com

# --- Records ---

# List DNS records for a domain
doctl compute domain records list example.com

# Create A record (⚠️ requires approval)
doctl compute domain records create example.com \
  --record-type A \
  --record-name @ \
  --record-data <ip>

# Create CNAME (⚠️ requires approval)
doctl compute domain records create example.com \
  --record-type CNAME \
  --record-name www \
  --record-data @

# Create TXT record — domain verification / SPF (⚠️ requires approval)
doctl compute domain records create example.com \
  --record-type TXT \
  --record-name @ \
  --record-data "v=spf1 include:_spf.google.com ~all"

# Create MX record — mail routing, priority is a separate flag (⚠️ requires approval)
doctl compute domain records create example.com \
  --record-type MX \
  --record-name @ \
  --record-data aspmx.l.google.com. \
  --record-priority 1

# Update an existing record (⚠️ requires approval)
doctl compute domain records update example.com \
  --record-id <id> \
  --record-data <new-value>

# Delete record (⚠️ requires approval)
doctl compute domain records delete example.com <record-id>
```

> **DO only serves DNS once nameservers are delegated.** Adding a domain in DO does nothing until the registrar's nameservers point to `ns1.digitalocean.com`, `ns2.digitalocean.com`, `ns3.digitalocean.com`. DO is not a registrar — domains are bought elsewhere, then delegated here.
