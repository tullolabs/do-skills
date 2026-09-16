---
name: do-registry
description: DigitalOcean Container Registry. Use for repositories, tags, and manifests, Docker login, Docker and Kubernetes pull credentials, garbage collection, and creating or deleting registries.
user-invocable: true
argument-hint: "[list|tags|delete|gc]"
---

# Container Registry

> Destructive ops need operator approval. Reads are always safe.
> Auth: `doctl` is pre-authenticated. See `/do-ops` for auth contexts.

Stay in the singular `doctl registry` tree unless the account holds more than one registry; see the
separate-trees gotcha below.

### The default registry

```bash
doctl registry get
doctl registry options available-regions     # region slugs valid for --region
doctl registry options subscription-tiers    # tier slugs valid for --subscription-tier

# Create the account's registry (⚠️ requires approval — the name is a positional, not a flag)
doctl registry create my-registry --region sgp1 --subscription-tier basic

# Delete it (⚠️ requires approval — destroys every repository, tag, and manifest in it)
doctl registry delete
doctl registry delete --force                # (⚠️ requires approval) skip the confirmation prompt
```

### Docker auth and pull credentials

`logout` revokes the token through DigitalOcean's OAuth revoke endpoint. `docker-config` and
`kubernetes-manifest` only print to stdout, so both are safe to run. For clusters,
`doctl kubernetes cluster registry add` in `/do-k8s` beats applying a manifest by hand.

```bash
doctl registry login                                    # auth local docker; token expires in 30 days
doctl registry login --read-only --expiry-seconds 3600  # short-lived, push operations fail
doctl registry login --never-expire
doctl registry logout                                   # revokes the token, then drops it from docker config

# Print a Docker auth config rather than writing one
doctl registry docker-config                            # read-only unless you ask otherwise
doctl registry docker-config --read-write --expiry-seconds 86400

# Emit a Kubernetes image-pull Secret; --name defaults to the registry name prefixed with registry-
doctl registry kubernetes-manifest --namespace kube-system
```

### Repositories, tags, and manifests

`--registry <name>` exists only on these subcommands. Tags and digests are both variadic, so you can
pass several in one call.

```bash
doctl registry repository list-v2                    # `list` was removed; v2 is the only lister
doctl registry repository list-tags <repo-name>
doctl registry repository list-manifests <repo-name>
doctl registry repository list-v2 --registry my-registry   # only needed with multiple registries

# Delete an image (⚠️ requires approval)
doctl registry repository delete-tag <repo-name> <tag>
doctl registry repository delete-tag <repo-name> <tag> <tag> --force   # (⚠️ requires approval)
# Delete by digest (⚠️ requires approval — takes out every tag pointing at that manifest)
doctl registry repository delete-manifest <repo-name> <manifest-digest>
```

### Garbage collection

`--exclude-unreferenced-blobs` narrows the sweep to manifests and nothing else.

```bash
doctl registry garbage-collection start              # (⚠️ requires approval) deletes unreferenced blobs
doctl registry garbage-collection start --include-untagged-manifests   # (⚠️ requires approval) also drop untagged manifests
doctl registry garbage-collection start --exclude-unreferenced-blobs --force   # (⚠️ requires approval)
doctl registry garbage-collection get-active         # the run in progress, if there is one
doctl registry garbage-collection list               # past runs, with BlobsDeleted and FreedBytes
doctl registry garbage-collection cancel <gc-uuid>   # (⚠️ requires approval) aborts the active run
```

### Multiple registries

Aliases are `regs` and `rs`, against `reg` and `r` for the singular tree.

```bash
doctl registries list
doctl registries get my-registry
doctl registries options available-regions
doctl registries options subscription-tiers

# Create (⚠️ requires approval — --subscription-tier is required)
doctl registries create my-registry --region sgp1 --subscription-tier basic
# Delete (⚠️ requires approval — one registry per call, there is no bulk form)
doctl registries delete my-registry --force

doctl registries login my-registry --read-only
doctl registries logout my-registry
doctl registries docker-config my-registry --read-write --expiry-seconds 86400
doctl registries kubernetes-manifest my-registry --namespace kube-system
```

### Repositories and garbage collection for a named registry

Same subcommands as the singular tree, shifted one positional right — the registry name is always the
first argument, and there is no `--registry` flag here.

```bash
doctl registries repository list-v2 my-registry
doctl registries repository list-tags my-registry <repo-name>
doctl registries repository list-manifests my-registry <repo-name>

# Registry, then repository, then one or more tags or digests (⚠️ requires approval)
doctl registries repository delete-tag my-registry <repo-name> <tag>
doctl registries repository delete-manifest my-registry <repo-name> <manifest-digest>   # (⚠️ requires approval)

doctl registries garbage-collection start my-registry --include-untagged-manifests   # (⚠️ requires approval)
doctl registries garbage-collection get-active my-registry
doctl registries garbage-collection list my-registry
doctl registries garbage-collection cancel my-registry <gc-uuid>   # (⚠️ requires approval)
```

## Gotchas

**Container registry deletes don't free quota.** Tags and manifests disappear immediately; storage only drops after `doctl registry garbage-collection start`.

**Garbage collection makes the registry read-only while it runs,** and it waits up to 15 minutes for outstanding write tokens to expire before it starts. Do not run it mid-deploy.

**`doctl registry` and `doctl registries` are separate trees, not aliases.** The plural takes `<registry-name>` as its first positional on every leaf except `list` and `options`; the singular takes no positional at all except on `create`. Several registries on the account do not force you into the plural tree — `doctl registry repository list-v2 --registry my-registry` works, and that `--registry` flag exists only on the singular `repository` subcommands. What the singular tree cannot do is list registries: `doctl registry list` does not exist, only `doctl registries list`.

**The singular tree's `Usage:` lines and its own `Examples:` disagree.** `doctl registry delete --help` prints `Usage: doctl registry delete [flags]` with no positional, yet its example is `doctl registry delete example-registry`. Same for `garbage-collection cancel`, whose usage line shows no argument while the example passes a `gc-uuid`. Trust the usage line for flags, pass `<gc-uuid>` to `cancel` because there is no other way to name a run, and use `doctl registries` whenever you need to name a registry explicitly.

**`--subscription-tier` is required on `create` despite having a default.** Both `doctl registry create` and `doctl registries create` mark it `(required)` and print `(default "basic")` on the same line. Pass it anyway. Valid values come from `doctl registry options subscription-tiers`, `--region` slugs from `doctl registry options available-regions`.
