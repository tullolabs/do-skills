---
name: do-storage
description: Use for any DigitalOcean Block Storage task. Create, attach, detach, and resize volumes, snapshot a volume, list and delete Droplet and volume snapshots, create custom images and transfer them between regions, and manage NFS shares and access points.
user-invocable: true
argument-hint: "[create|attach|resize|snapshot] [volume]"
---

# Block Storage and Images

> Destructive ops need operator approval. Reads are always safe.
> Auth: `doctl` is pre-authenticated. See `/do-ops` for auth contexts.

### Volumes

The volume name is a positional. `--size` is required, takes a unit suffix, and defaults to `4TiB`. Pass
either `--region` or `--snapshot`, never both, since a snapshot already carries its region. Only a
pre-formatted volume auto-mounts on attach, so set `--fs-type ext4` or `xfs` at create time.

```bash
doctl compute volume list --region sgp1   # --region is an optional filter
doctl compute volume get <volume-id>

# Create (⚠️ requires approval)
doctl compute volume create my-volume --region sgp1 --size 100GiB --fs-type ext4 --tag project-name
# Restore from a snapshot instead. No --region: the snapshot's region wins.
doctl compute volume create my-volume --snapshot <snapshot-id> --size 100GiB   # (⚠️ requires approval)

# Delete (⚠️ requires approval — irreversible, destroys all data on the volume)
doctl compute volume delete <volume-id>
```

### Volume actions

`attach` and `detach` both take `<volume-id>` then `<droplet-id>` as positionals, in that order. `resize`
takes only `<volume-id>` and needs `--size` as a bare integer in GiB plus `--region` naming the volume's
*current* region. Add `--wait` to any of the three to block until the action finishes.

```bash
doctl compute volume-action attach <volume-id> <droplet-id> --wait   # (⚠️ requires approval)
doctl compute volume-action detach <volume-id> <droplet-id> --wait   # (⚠️ requires approval)
# doctl compute volume-action detach-by-droplet-id <volume-id> <droplet-id>
#   Same positionals, same result. `--help` marks it deprecated and points at `detach`. Use `detach`.
# Grow only, max 16TiB. Unmount inside the Droplet first, then grow the filesystem afterward.
doctl compute volume-action resize <volume-id> --size 200 --region sgp1 --wait   # (⚠️ requires approval)

# Watch progress
doctl compute volume-action list <volume-id>
doctl compute volume-action get <volume-id> --action-id <action-id>
```

### Snapshots

Two separate groups, and mixing them up is the usual mistake. `doctl compute volume snapshot` is the only
command that creates a volume snapshot, and it lives under `volume`. `doctl compute snapshot` only reads and
deletes, and it covers Droplet snapshots and volume snapshots together. `--snapshot-name` is required on
create. The `Size` column in `snapshot list` is the billable size. For volume snapshots it is measured at the block level, so it can exceed what `df` reports inside the droplet until unused blocks are trimmed with `fstrim`.

```bash
# Create — note this is under `volume`, not `snapshot` (⚠️ requires approval)
doctl compute volume snapshot <volume-id> --snapshot-name my-snapshot --snapshot-desc "nightly" --tag project-name

# Read across both Droplet and volume snapshots
doctl compute snapshot list
doctl compute snapshot list --resource volume --region sgp1
doctl compute snapshot get <snapshot-id>

# Delete, accepts several IDs (⚠️ requires approval — irreversible)
doctl compute snapshot delete <snapshot-id> <snapshot-id>
```

### Images

`create` uploads a custom image from a URL you host; `--image-url` and `--region` are both required and the
image name is a positional. `list-distribution` returns DigitalOcean's public OS images, `list-application`
the Marketplace 1-Click apps, and `list-user` your own snapshots, backups, and uploads.

```bash
doctl compute image list            # private images only; add --public for DO's public catalog
doctl compute image list-distribution --format ID,Distribution,Slug
doctl compute image list-application --format ID,Name,Slug
doctl compute image list-user --format ID,Name,Distribution,Slug
doctl compute image get <image-id|image-slug>

# Upload a custom image (⚠️ requires approval)
doctl compute image create "Example Image" --image-url "https://example.com/image.img" \
  --region sgp1 --image-distribution Ubuntu --tag-names project-name
# Rename. The required flag is --image-name, not --name.
doctl compute image update <image-id> --image-name "Example Image Name"
# Delete (⚠️ requires approval — irreversible)
doctl compute image delete <image-id>

# --- Cross-region copy ---
# An image is region-scoped. Transfer it before creating a Droplet from it elsewhere.
doctl compute image-action transfer <image-id> --region nyc3 --wait   # (⚠️ requires approval)
doctl compute image-action get <image-id> --action-id <action-id>
```

### Network file storage (NFS)

Unlike volumes, every `nfs` command is flag-driven with no positionals, and nearly all of them require
`--region`. A share attaches to a VPC rather than to a Droplet, so several Droplets on that VPC share it.
`create` requires `--name`, `--region`, `--size` in GiB, `--vpc-ids`, and `--performance-tier` together.
NFS is not in every region. It runs in nyc2, ams3, atl1, ric1, mkc1, and mem1, so `sgp1` and the other
Droplet regions will not take a share. A share and the VPCs it attaches to must be in the same region.
Standard tier starts at 50 GiB and high performance at 500 GiB, which is why `switch-performance-tier`
to `high` fails on a share smaller than that.

```bash
doctl nfs list --region atl1
doctl nfs get --region atl1 --id <share-id>
# (⚠️ requires approval)
doctl nfs create --name my-share --region atl1 --size 100 --vpc-ids <vpc-id> \
  --performance-tier standard   # (⚠️ requires approval)
doctl nfs resize --region atl1 --id <share-id> --size 200 --wait   # (⚠️ requires approval)
doctl nfs switch-performance-tier --id <share-id> --performance-tier high --wait   # (⚠️ requires approval — needs a share of 500 GiB or more; note there is no --region here)
doctl nfs delete --region atl1 --id <share-id>   # (⚠️ requires approval — irreversible)

# --- VPC membership ---
doctl nfs attach --region atl1 --id <share-id> --vpc-id <vpc-id> --wait   # (⚠️ requires approval)
doctl nfs detach --region atl1 --id <share-id> --vpc-id <vpc-id> --wait   # (⚠️ requires approval)
# Detach from one VPC and attach to another in a single call. Takes no --region.
doctl nfs reassign --id <share-id> --old-vpc-id <vpc-id> --new-vpc-id <vpc-id> --wait   # (⚠️ requires approval)

# --- Access points: the exported paths clients actually mount ---
doctl nfs access-point list --share-id <share-id>
doctl nfs access-point get --id <access-point-id>
# (⚠️ requires approval)
doctl nfs access-point create --share-id <share-id> --name my-access-point --path /exports/data \
  --vpc-id <vpc-id> --squash-config ROOT_SQUASH --protocols NFS4   # (⚠️ requires approval)
doctl nfs access-point delete --id <access-point-id>   # (⚠️ requires approval — clients lose the mount)

# --- Share snapshots ---
doctl nfs snapshot list --region atl1 --share-id <share-id>
doctl nfs snapshot get --region atl1 --id <snapshot-id>
doctl nfs snapshot create --region atl1 --share-id <share-id> --name my-snapshot --wait   # (⚠️ requires approval)
doctl nfs snapshot delete --region atl1 --id <snapshot-id>   # (⚠️ requires approval — irreversible)
```

## Gotchas

**A volume only attaches to a Droplet in the same region.** There is no cross-region attach and no move: `attach` fails if the Droplet lives elsewhere. To relocate data, run `doctl compute volume snapshot`, then `doctl compute volume create --snapshot <snapshot-id>` in the target region. `image-action transfer` is the equivalent escape hatch for images, and volumes have no counterpart.

**Volume resize is grow-only, caps at 16TiB, and takes a different `--size` format than create.** `volume-action resize --help` states volumes may only be resized upwards, so over-provisioning is permanent until you snapshot into a smaller new volume. `volume create --size` is a string with a unit suffix like `100GiB` and defaults to `4TiB` when omitted; `volume-action resize --size` is a bare integer already understood as GiB. Resize also only grows the block device, so grow the filesystem inside the Droplet afterward or `df` keeps reporting the old size.

**`doctl compute snapshot` cannot create anything.** The group only has `list`, `get`, and `delete`. Creation lives at `doctl compute volume snapshot <volume-id> --snapshot-name <name>` for volumes and under `doctl compute droplet-action snapshot` for Droplets. See `/do-droplets`.

**Snapshots keep billing after the source is gone.** Deleting a volume or a Droplet does not delete its snapshots; they stay on the account at the compressed size shown in the `Size` column of `doctl compute snapshot list`. Deleting a DOKS cluster leaves CSI-created volume snapshots behind the same way. See `/do-k8s`.
