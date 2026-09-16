---
name: do-droplets
description: DigitalOcean droplets. Use for creating VMs, power cycling, reboot, resize, rebuild, rename, snapshots and restore, backups, SSH keys, SSH access, autoscale pools, and deletion.
user-invocable: true
argument-hint: "[list|create|ssh|power|resize|delete] [droplet]"
---

# Droplets

> Destructive ops need operator approval. Reads are always safe.
> Auth: `doctl` is pre-authenticated. See `/do-ops` for auth contexts.

### Lifecycle

```bash
# The optional GLOB filters on name
doctl compute droplet list
doctl compute droplet list "web-*"
doctl compute droplet list --tag-name project-name
doctl compute droplet list --region sgp1
doctl compute droplet list --gpus                    # GPU droplets only

doctl compute droplet get <droplet-id|droplet-name>
doctl compute droplet get <id> --format PublicIPv4 --no-header    # just the IP

# (⚠️ requires approval). ubuntu-26-04-x64 is also live if you want the newer LTS.
doctl compute droplet create <name> \
  --region sgp1 \
  --size s-1vcpu-1gb \
  --image ubuntu-24-04-x64 \
  --ssh-keys <fingerprint-or-id> \
  --tag-names project-name \
  --wait

# Common create extras
#   --user-data-file cloud-init.yaml   run cloud-init on first boot
#   --vpc-uuid <uuid>                  place it in a specific VPC
#   --volumes <volume-id>              attach block storage at boot
#   --project-id <uuid>                file it under a project
#   --enable-backups                   backups on from the start
#   --enable-monitoring                install the metrics agent

# Find valid inputs first
doctl compute region list
doctl compute size list
doctl compute image list-distribution --public | grep -i ubuntu
doctl compute droplet 1-click list                   # Marketplace images

# (⚠️ requires approval). Takes several IDs, or a whole tag.
doctl compute droplet delete <droplet-id|droplet-name>
doctl compute droplet delete --tag-name project-name     # (⚠️ requires approval — deletes every tagged droplet)
```

### Access

```bash
doctl compute ssh <droplet-id|name>
doctl compute ssh <id> --ssh-user deploy --ssh-port 2222
doctl compute ssh <id> --ssh-command "systemctl status nginx"   # run one command and exit
doctl compute ssh <id> --ssh-private-ip                          # connect over the VPC address

# Turn on the legacy private network interface (⚠️ requires approval — reconfigures networking)
doctl compute droplet-action enable-private-networking <id> --wait
```

New droplets are already in a VPC; this is only for older ones that predate that default. VPC work
lives in `/do-network`.

### Power and state

Every `droplet-action` takes the droplet ID as a positional and accepts `--wait` to block until the
action finishes.

```bash
doctl compute droplet-action reboot <id>          # (⚠️ requires approval) graceful
doctl compute droplet-action shutdown <id>        # (⚠️ requires approval) graceful, OS-level
doctl compute droplet-action power-off <id>       # (⚠️ requires approval — hard pull, risks data loss)
doctl compute droplet-action power-on <id>
doctl compute droplet-action power-cycle <id>     # (⚠️ requires approval — hard off then on)
doctl compute droplet-action password-reset <id>  # (⚠️ requires approval) emails a new root password

# Reshape (⚠️ requires approval). doctl powers the droplet off for you, so this is an outage.
doctl compute droplet-action resize <id> --size s-2vcpu-4gb --wait
doctl compute droplet-action resize <id> --size s-2vcpu-4gb --resize-disk --wait   # (⚠️ requires approval) permanent, see gotchas

# Replace the OS, keeping the IP (⚠️ requires approval — wipes the disk)
doctl compute droplet-action rebuild <id> --image ubuntu-24-04-x64

# Roll back to a snapshot or backup (⚠️ requires approval — wipes the disk)
doctl compute droplet-action restore <id> --image-id <backup-id>          # backups of THIS droplet only

doctl compute droplet-action rename <id> --droplet-name new-name   # (⚠️ requires approval)
doctl compute droplet-action enable-ipv6 <id>   # (⚠️ requires approval)
doctl compute droplet-action change-kernel <id> --kernel-id <kernel-id>
doctl compute droplet kernels <id>                # list kernel IDs for the above
```

### Backups and snapshots

```bash
doctl compute droplet backups <id>                # automatic backups
doctl compute droplet snapshots <id>              # manual snapshots

# (⚠️ requires approval — droplet should be off for a consistent image)
doctl compute droplet-action snapshot <id> --snapshot-name pre-upgrade --wait

# Automatic backups (⚠️ requires approval — adds to the bill)
doctl compute droplet-action enable-backups <id>
doctl compute droplet-action enable-backups <id> --backup-policy-plan weekly --backup-policy-weekday SUN --backup-policy-hour 4   # (⚠️ requires approval)
doctl compute droplet-action change-backup-policy <id> --backup-policy-plan daily --backup-policy-hour 2
doctl compute droplet-action disable-backups <id>   # (⚠️ requires approval — stops new backups; existing ones survive to their normal expiry)

# `get` takes a droplet ID, `list` is account-wide, `list-supported` is a static menu.
doctl compute droplet backup-policies get <id> --format DropletID,BackupPolicyPlan,NextBackupWindowStart
doctl compute droplet backup-policies list
doctl compute droplet backup-policies list-supported
```

Snapshot and image management lives in `/do-storage`.

### SSH keys

```bash
doctl compute ssh-key list
doctl compute ssh-key get <key-id|key-fingerprint>
doctl compute ssh-key import <key-name> --public-key-file ~/.ssh/id_ed25519.pub   # (⚠️ requires approval)
doctl compute ssh-key create <key-name> --public-key "ssh-ed25519 AAAA..."   # (⚠️ requires approval)
doctl compute ssh-key update <key-id|fingerprint> --key-name new-name   # (⚠️ requires approval)
doctl compute ssh-key delete <key-id|key-fingerprint>      # (⚠️ requires approval)
```

### Autoscale pools

```bash
doctl compute droplet-autoscale list
doctl compute droplet-autoscale get <autoscale-pool-id>
doctl compute droplet-autoscale list-members <autoscale-pool-id>    # droplets currently in the pool
doctl compute droplet-autoscale list-history <autoscale-pool-id>    # why it scaled, and when

# (⚠️ requires approval). Name is a flag here, not a positional.
doctl compute droplet-autoscale create \
  --name web-pool \
  --region sgp1 \
  --size s-1vcpu-1gb \
  --image ubuntu-24-04-x64 \
  --ssh-keys <fingerprint> \
  --min-instances 2 \
  --max-instances 10 \
  --cpu-target 70 \
  --cooldown-minutes 5

# --name is required on every update, even when only changing a number.
doctl compute droplet-autoscale update <autoscale-pool-id> --name web-pool --max-instances 20   # (⚠️ requires approval — changes pool capacity)
doctl compute droplet-autoscale delete <autoscale-pool-id>              # (⚠️ requires approval — pool only, droplets survive)
doctl compute droplet-autoscale delete-dangerous <autoscale-pool-id>   # (⚠️ requires approval — pool AND every droplet in it)
```

### Watching async actions

Most writes return an action ID instead of blocking. `--wait` covers the common case; these commands
poll one by hand.

```bash
doctl compute action list
doctl compute action list --action-type create --status in-progress
doctl compute action get <action-id>
doctl compute action wait <action-id>                 # --poll-timeout is the re-poll INTERVAL in seconds (default 5), not a deadline
doctl compute droplet actions <droplet-id>            # action history for one droplet
doctl compute droplet-action get <id> --action-id <action-id>
```

### Tags and neighbors

```bash
doctl compute droplet tag <droplet-id|name> --tag-name project-name   # (⚠️ requires approval)
doctl compute droplet untag <droplet-id|name> --tag-name project-name   # (⚠️ requires approval)
doctl compute droplet neighbors <id>                  # other droplets on the same physical host
```

Tag lifecycle and project assignment live in `/do-projects`.

## Gotchas

**Creating a droplet without `--ssh-keys` emails a root password.** Always pass `--ssh-keys`. Run `doctl compute ssh-key list` to find the fingerprint.

**`--resize-disk` is a one-way door, and resize always means downtime.** Without the flag, resize changes CPU and RAM only and is reversible. With it the disk grows too, and DigitalOcean cannot shrink a disk, so the droplet is pinned at that size or larger forever. Either way `doctl` powers the droplet off before resizing, so a resize on a live box is an outage whether you planned one or not.

**`doctl compute droplet delete --tag-name` deletes every droplet carrying that tag.** It prompts once for the whole batch, and `-f` skips even that. The prompt does not say how many droplets it is about to destroy, so run `doctl compute droplet list --tag-name <tag>` first and count what comes back.

**`power-off` is pulling the cord, `shutdown` is the OS shutting down.** Use `shutdown` unless the droplet is unresponsive. `power-off` risks filesystem corruption on a busy disk.

**Droplet names are not unique, IDs are.** `get`, `delete`, and `ssh` accept either, but if two droplets share a name the command acts on whichever the API returns first. Use the ID for anything destructive.

**Autoscale pools have two delete verbs and the safe-looking one is the safe one.** `droplet-autoscale delete` removes the pool and leaves its droplets running and billing. `droplet-autoscale delete-dangerous` removes the pool *and every droplet in it*. Run `list-members` first so you know what it will take down. Kubernetes differs: there the equivalent is a flag, `doctl kubernetes cluster delete <id> --dangerous`, and there is no `kubernetes cluster delete-dangerous`.
