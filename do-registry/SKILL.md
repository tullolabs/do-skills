---
name: do-registry
description: Use for any DigitalOcean Container Registry task. List repositories, container image tags, and manifests, log Docker in to the registry, delete a tag, and run garbage collection to reclaim storage.
user-invocable: true
argument-hint: "[list|tags|delete|gc]"
---

# Container Registry

> Destructive ops need operator approval. Reads are always safe.
> Auth: `doctl` is pre-authenticated. See `/do-ops` for auth contexts.

```bash
doctl registry get
doctl registry repository list-v2                    # `list` was removed; v2 is the only lister
doctl registry repository list-tags <repo-name>
doctl registry repository list-manifests <repo-name>

doctl registry login                                 # auth local docker
doctl registry garbage-collection start              # (⚠️ requires approval) deletes unreferenced blobs
doctl registry garbage-collection start --include-untagged-manifests   # also drop untagged manifests

# Delete an image (⚠️ requires approval)
doctl registry repository delete-tag <repo-name> <tag>
```

Deleting tags does not free quota. Storage only drops after garbage collection runs.

## Gotchas

**Container registry deletes don't free quota.** Tags and manifests disappear immediately; storage only drops after `doctl registry garbage-collection start`.

**Garbage collection makes the registry read-only while it runs,** and it waits up to 15 minutes for outstanding write tokens to expire before starting. Do not run it mid-deploy.

**`doctl registry` is the single-registry form.** Accounts with more than one registry use `doctl registries` instead.
