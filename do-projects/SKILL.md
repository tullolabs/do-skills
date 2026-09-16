---
name: do-projects
description: Use for any DigitalOcean Projects task. Create a project, list and update it, set the default project, assign droplets, apps, and databases to it by URN, look up a resource by URN, and create tags to apply to or remove from compute resources.
user-invocable: true
argument-hint: "[list|create|assign|tag]"
---

# Projects and Tags

> Destructive ops need operator approval. Reads are always safe.
> Auth: `doctl` is pre-authenticated. See `/do-ops` for auth contexts.

### Projects

`--name` and `--purpose` are the two required flags on create. `--environment` takes `Development`,
`Staging`, or `Production`. The literal string `default` works anywhere a project ID does.

```bash
doctl projects list
doctl projects list --format ID,Name,IsDefault
doctl projects get <project-id>
doctl projects get default

# (⚠️ requires approval)
doctl projects create --name "Example Project" --purpose "Frontend development" \
  --environment Production --description "customer-facing web tier"

doctl projects update <project-id> --name "API Project" --purpose "Backend development"   # (⚠️ requires approval)
doctl projects update <project-id> --is_default      # (⚠️ requires approval) move the default flag onto this project

doctl projects delete <project-id>    # (⚠️ requires approval — refuses while resources are still assigned)
```

### Resource assignment

Resources are addressed by uniform resource name, `do:<resource-type>:<id>`. Droplet IDs are numeric, most
others are UUIDs. `--resource` is repeatable and also accepts a comma-separated list.

```bash
doctl projects resources list <project-id>
doctl projects resources list default --format URN,AssignedAt,Status
doctl projects resources get do:droplet:386734086
doctl projects resources get do:app:be5aab85-851b-4cab-b2ed-98d5a63ba4e8

doctl projects resources assign <project-id> --resource=do:droplet:386734086   # (⚠️ requires approval)
# (⚠️ requires approval)
doctl projects resources assign <project-id> \
  --resource=do:droplet:386734086 --resource=do:dbaas:02971b0e-5a7e-49c4-9a82-7b5930489636
```

`resources get` is documented as supporting droplets, floating IPs, load balancers, domains, volumes, and
App Platform apps. Droplet IDs come from `/do-droplets`.

### Tags

Tags apply to droplets, images, volumes, volume snapshots, and database clusters. They are what a cloud
firewall rule or an alert policy targets when you want a moving set rather than a fixed ID list.

```bash
doctl compute tag list
doctl compute tag get web
doctl compute tag create web   # (⚠️ requires approval)

doctl compute tag apply web --resource=do:droplet:386734086,do:droplet:191669331   # (⚠️ requires approval)
doctl compute tag remove web --resource=do:droplet:386734086   # (⚠️ requires approval)

doctl compute tag delete web    # (⚠️ requires approval — also untags every resource carrying it)
```

## Gotchas

**Nothing lands in the right project on its own.** `apps create`, `compute droplet create`, and `databases create` take no project flag at all, so every new resource goes to whichever project holds the default flag. Check with `doctl projects list --format Name,IsDefault`. Assignment is a second step, `doctl projects resources assign <project-id> --resource=<urn>`, and an agent that was never told the target project simply will not take it. Record the target as `DO_PROJECT` in the project's `.env`, or ask the operator before creating anything.

**`--is_default` exists on `projects update` only, never on `projects create`.** Create the project first, then run `doctl projects update <project-id> --is_default` to move the flag onto it. `doctl projects list --format ID,Name,IsDefault` shows which project currently holds it, and `doctl projects get default` resolves to that one.

**A project with anything assigned to it will not delete.** The delete help states the project must have no resources. Run `doctl projects resources list <project-id>` first and reassign everything it returns to another project with `doctl projects resources assign`, or the delete comes back rejected.

**The URN type word is not always the product name.** Database clusters are `do:dbaas:<uuid>`, not `do:database:`. Apps are `do:app:<uuid>`, droplets are `do:droplet:<numeric-id>`. Run `doctl projects resources list default` against a real project and read the exact strings out of the URN column rather than guessing the type word.

**`compute tag apply` and `compute tag remove` want URNs through `--resource`, not bare IDs.** Both take `<tag-name>` as the first positional and then `--resource=do:droplet:386734086`, repeated or comma-separated. Note also that `doctl compute tag get` reports only a droplet count, so a tag applied purely to volumes or database clusters still reads `0`.
