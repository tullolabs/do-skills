---
name: do-droplets
description: Use for any DigitalOcean droplet task. List and inspect VMs, create a server with an SSH key, look up images, sizes, and regions, SSH in, read the public IP, and delete droplets.
user-invocable: true
argument-hint: "[list|create|ssh|delete] [droplet]"
---

# Droplets

> Destructive ops need operator approval. Reads are always safe.
> Auth: `doctl` is pre-authenticated. See `/do-ops` for auth contexts.

```bash
# List all
doctl compute droplet list

# Get details
doctl compute droplet get <id>

# Create (⚠️ requires approval). ubuntu-26-04-x64 is also live if you want the newer LTS.
doctl compute droplet create <name> \
  --region sgp1 \
  --size s-1vcpu-1gb \
  --image ubuntu-24-04-x64 \
  --ssh-keys <fingerprint-or-id> \
  --tag-names project-name \
  --wait

# Find inputs first
doctl compute ssh-key list
doctl compute region list
doctl compute size list
doctl compute image list-distribution --public | grep -i ubuntu

# SSH into droplet
doctl compute ssh <id>

# Get droplet IP
doctl compute droplet get <id> --format PublicIPv4 --no-header

# Delete (⚠️ requires approval)
doctl compute droplet delete <id>
```

## Gotchas

**Creating a droplet without `--ssh-keys` emails a root password.** Always pass `--ssh-keys`. Run `doctl compute ssh-key list` to find the fingerprint.
