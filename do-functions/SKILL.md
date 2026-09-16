---
name: do-functions
description: Use for any DigitalOcean Functions task. Install serverless support, create and connect to a functions namespace, scaffold a local project, deploy and undeploy packages, invoke a function, read activation logs and results, and manage namespace access keys.
user-invocable: true
argument-hint: "[connect|deploy|invoke|logs]"
---

# Serverless Functions

> Destructive ops need operator approval. Reads are always safe.
> Auth: `doctl` is pre-authenticated. See `/do-ops` for auth contexts.

### Local setup

The serverless support is extra software installed under `doctl`. Until it is there, most subcommands refuse
to run. `upgrade` reinstalls over the existing copy to match the current `doctl` version.

```bash
doctl serverless install                  # one-time, long-running, needs network
doctl serverless status                   # install state plus the connected namespace
doctl serverless status --languages       # keywords accepted by `init --language`
doctl serverless upgrade
doctl serverless uninstall                # (⚠️ requires approval — removes serverless support from `doctl`)
```

### Namespaces and access keys

`connect` binds your local machine to one namespace at a time. `namespaces create` connects you to the new
namespace automatically unless you pass `--no-connect`.

```bash
doctl serverless namespaces list
doctl serverless namespaces list-regions  # ams3 blr1 fra1 lon1 nyc1 sfo3 sgp1 syd1 tor1 and bare-region aliases
doctl serverless namespaces create --label my-namespace --region sgp1   # (⚠️ requires approval)
doctl serverless connect <namespace-hint>            # partial label or id; no argument matches all
doctl serverless namespaces delete <namespace-id-or-label>    # (⚠️ requires approval)

# Namespace-scoped keys, so CI never holds your main DigitalOcean token
doctl serverless key list
doctl serverless key create --name ci-cd-key --expiration 7d   # (⚠️ requires approval) or <int>h, min 1h, or `never`
doctl serverless key delete <access-key-id>          # (⚠️ requires approval — cannot be undone)
```

The secret half of a key is printed once at creation and never again.

### Projects and deploy

`init` writes `project.yml`, a `.gitignore`, and one sample function at `packages/sample/hello/hello.js`
(JavaScript unless you pass `--language`). `--remote-build` moves the build off your machine into the cloud;
the local path is what `--yarn` and `--verbose-build` describe.

```bash
doctl serverless init <path>
doctl serverless init <path> --language python --overwrite
doctl serverless deploy <directory>   # (⚠️ requires approval)
doctl serverless deploy <directory> --remote-build   # (⚠️ requires approval)
doctl serverless deploy <directory> --incremental --include sample/hello   # (⚠️ requires approval)

# Dump the project's layout as JSON without deploying — useful for a CI step that
# needs the function list before it builds.
doctl serverless get-metadata <directory>
doctl serverless get-metadata <directory> --exclude sample/hello --no-triggers
doctl serverless watch <directory>                   # redeploys on every change until interrupted

doctl serverless undeploy sample/hello               # (⚠️ requires approval)
doctl serverless undeploy sample --packages          # (⚠️ requires approval — removes the whole package)
doctl serverless undeploy --all                      # (⚠️ requires approval — every package and function)
```

A committed project directory is also what `/do-apps` builds an App Platform functions component from.

### Invoking and reading activations

```bash
doctl serverless functions list
doctl serverless functions list sample --limit 3
doctl serverless functions get sample/hello --url
doctl serverless functions get sample/hello --code --save-as local-hello.js

doctl serverless functions invoke sample/hello --param name:John,place:NY   # (⚠️ requires approval)
doctl serverless functions invoke sample/hello --param-file path/to/file.json --full   # (⚠️ requires approval)
doctl serverless functions invoke sample/hello --no-wait      # (⚠️ requires approval) returns an activation ID instead of a result

doctl serverless activations list
doctl serverless activations list sample/hello --limit 50     # default 30, max 200
doctl serverless activations get <activation-id>
# `logs` has no --last, despite doctl's own example using it. --limit defaults to 1 already.
doctl serverless activations logs --function sample/hello --limit 1
doctl serverless activations logs --function sample/hello --follow
doctl serverless activations result --function sample/hello --last
```

## Gotchas

**`doctl serverless install` is a one-time local step and most subcommands refuse to run without it.** `doctl serverless status` and `doctl serverless functions list` both fail with `serverless support is not installed (use doctl serverless install)`. `doctl serverless namespaces list` and `doctl serverless init` are the exceptions, since one is a plain API call and the other only writes local files.

**Connect before you deploy.** `doctl serverless --help` spells the order out: install, then `doctl serverless connect`, then everything else. `connect` is what picks the single namespace that `deploy`, `functions invoke`, and `activations` all act on, so switching namespaces means running `connect` again, not passing a flag.

**`activations logs` and `activations result` return different halves of the same record.** `logs` gives the function's log output and is the only one of the three with `--follow` for tailing. `result` gives just the value the function returned. `activations get` returns the whole record, both halves plus timing, and `--limit` on `logs` defaults to 1 while on `list` it defaults to 30.

**`-f` means two different things inside `doctl serverless`.** On `activations logs` and `activations result` it is `--function`. On `functions invoke` and `activations list` it is `--full`. Write the long flag out and the ambiguity disappears.
