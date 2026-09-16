---
name: do-secrets
description: DigitalOcean Secrets Manager. Use for regional secret containers, setting and unsetting keys, reading one value for scripting, version history, soft delete and restore, and CSPM security scans for findings.
user-invocable: true
argument-hint: "[create|set|get|scans]"
---

# Secrets and Security Scans

> Destructive ops need operator approval. Reads are always safe.
> Auth: `doctl` is pre-authenticated. See `/do-ops` for auth contexts.

### Reading secrets

A secret is a named regional container of key-value pairs. Every subcommand except `list` takes `--region`.

```bash
doctl secrets list                                             # all regions, no values
doctl secrets list-versions my-secret --region nyc3
doctl secrets get my-secret --region nyc3                      # values masked
doctl secrets get my-secret --region nyc3 --show               # reveal every value
doctl secrets get my-secret --region nyc3 --key api-key --raw  # one value, unformatted, for scripting
```

### Writing secrets

`set` merges into the existing keys, `update` replaces all of them. Prefer `key=@./path` or `key=-` over an
inline `key=value`, which lands the value in shell history.

```bash
doctl secrets create my-secret --region nyc3 --value api-key=@./api-key.txt   # (⚠️ requires approval)
doctl secrets create my-secret --region nyc3 --from-env-file ./secrets.env   # (⚠️ requires approval)
doctl secrets create my-secret --region nyc3 --interactive   # (⚠️ requires approval)

openssl rand -hex 32 | doctl secrets set my-secret --region nyc3 --value api-key=-
doctl secrets set my-secret --region nyc3 --value api-key=@./api-key.txt   # (⚠️ requires approval)

# Full replacement (⚠️ requires approval — drops every key you leave out)
doctl secrets update my-secret --region nyc3 --replace --value api-key=@./api-key.txt

doctl secrets unset my-secret --region nyc3 --key old-key --key other-key   # (⚠️ requires approval)
doctl secrets delete my-secret --region nyc3       # (⚠️ requires approval — soft delete, restorable)
doctl secrets restore my-secret --region nyc3   # (⚠️ requires approval)
```

Every write path writes a new version, which is what `doctl secrets list-versions` reports.

### CSPM security scans

A CSPM scan checks your resources against DigitalOcean's cloud posture rules. Standard rules cover IAM,
networking, and storage; workload rules cover droplets and managed databases. Findings come back keyed by rule
ID, each with a severity and a count of affected resources. `--wait` blocks until the scan finishes.

```bash
doctl security scans list
doctl security scans create --wait   # (⚠️ requires approval)
doctl security scans latest
doctl security scans latest --severity high
doctl security scans get <scan-uuid> --severity critical
doctl security scans get <scan-uuid> --type <finding-type>
doctl security scans affected-resources <scan-uuid> --finding-uuid <finding-uuid>
```

`affected-resources` returns URN, name, and type per resource, so it feeds straight into `/do-projects`.

## Gotchas

**`--value api-key=hunter2` lands the secret in your shell history in plaintext.** Every write command takes `key=@./path` to read a file and `key=-` to read stdin, so `openssl rand -hex 32 | doctl secrets set my-secret --region nyc3 --value api-key=-` never writes the value to a line zsh records. Omitting `--value` and running with `--interactive` masks each value as you type it.

**`set` merges and `update` replaces; `unset` prunes keys and `delete` removes the container.** `doctl secrets set` fetches the current secret, folds your keys in, and writes a new version. `doctl secrets update` writes only the keys you pass and silently drops the rest, which is why it refuses to run without `--replace` and prompts unless you add `--force`. `unset --key` removes named keys and leaves the secret alive. `delete` schedules the whole container for soft deletion, recoverable with `doctl secrets restore <name>`.

**Omit `--region` and the name alone will not resolve.** A secret is scoped to one region, so `my-secret` in `nyc3` and `my-secret` in `sfo3` are two different containers. Without `--region` you are prompted only when running with `--interactive`. `doctl secrets list` is the exception, sweeping every region and returning a Region column you can copy from.

**A `403` here is a token scope problem, not a missing resource.** Both `doctl secrets list` and `doctl security scans list` return `403 ... You are not authorized to perform this operation` on a token that reads droplets and projects without complaint. Secrets Manager and CSPM need their own scopes granted to the token. See `/do-ops` for switching auth contexts.
