---
name: do-apps
description: DigitalOcean App Platform operations with doctl. Use for listing apps, reading logs, validating a spec, deploying, restarting, cancelling events and job invocations, upgrading buildpacks, and building components locally. Also covers why a static site needs its own domain.
user-invocable: true
argument-hint: "[logs|spec|deploy|restart] [app]"
---

# App Platform

> Destructive ops need operator approval. Reads are always safe.
> Auth: `doctl` is pre-authenticated. See `/do-ops` for auth contexts.

> **Deployment workflow:** App Platform is connected to GitHub. Push to the linked branch and report back immediately. Do **not** poll deployment status, wait for builds, or trigger deploys manually. Push → done.

### Static Sites on App Platform

**Our convention: static sites run at `/`, not under a sub-path.** App Platform does support sub-path routing
for static sites, so this is a rule we picked, not a limit the platform imposes.

Ingress rules can match and rewrite a path prefix, so `/docs` does reach the component. The breakage happens
one layer down. The built HTML asks for `/assets/app.js`, that request never matches the `/docs` rule, and the
ingress hands it to whatever owns `/`. Getting it right means the build's base path, the ingress match, and
`preserve_path_prefix` all agree, and any one of them drifting gives a white page with 404s in the console.

**The fix:** Give each static site its own domain or subdomain.
- Point a CNAME to the App Platform ingress
- Set `baseUrl: '/'` so all assets resolve from root
- No routing to keep in sync

Sub-path routing is worth the effort for **dynamic backends** (services), where an API prefix is one rule and
there are no relative asset URLs to break.

Three spec fields to know:
- `catchall_document: index.html` is what makes client-side routing work. Without it a deep link 404s.
- Component-level `routes:` is deprecated. Use the top-level `ingress:` block for new specs.
- Component-level `preserve_path_prefix` is deprecated with it. The live one is
  `ingress.rules[].component.preserve_path_prefix`, and it is mutually exclusive with `rewrite`.

### Core app lifecycle

```bash
# List all apps
doctl apps list

# Get app details (includes ID, URL, status)
doctl apps get <id>

# Logs (these do NOT follow by default; there is no --no-follow flag)
doctl apps logs <id> --type run          # runtime logs (default type)
doctl apps logs <id> --type build        # build logs
doctl apps logs <id> --type deploy       # deploy logs
doctl apps logs <id> --type run_restarted  # logs from before a crash-restart
doctl apps logs <id> --type autoscale_event  # scaling decisions
doctl apps logs <id> --tail 50           # last 50 lines
doctl apps logs <id> <component> -f      # follow one component

# Why is it broken
doctl apps list-deployments <id>
doctl apps get-deployment <id> <deployment-id>
doctl apps list-events <id>              # surfaces build/deploy failures with reasons

# Read the live spec (do this before editing anything)
doctl apps spec get <id> > app.yaml
doctl apps propose --spec app.yaml       # dry-run validate, no changes made

# Apply a spec change (⚠️ requires approval)
# Spec only. Add --update-sources to also pull the latest source or image.
doctl apps update <id> --spec app.yaml

# Deploy from spec (⚠️ requires approval — only for new apps)
# A new spec needs the source repo, which nothing on the account can tell you yet.
# Read DO_APP_REPO from the project's .env, or ask the operator. Never guess it
# from the directory name or the git remote.
doctl apps create --spec app.yaml

# Trigger re-deploy manually (⚠️ requires approval — rarely needed, prefer git push)
# Without --update-sources this rebuilds the SAME commit and image.
doctl apps create-deployment <id> --update-sources

# Restart an app, or one component (⚠️ requires approval)
doctl apps restart <id>
doctl apps restart <id> --components <component>

# Shell into a running component (⚠️ requires approval)
doctl apps console <id> <component>

# Delete (⚠️ requires approval)
doctl apps delete <id>
```

`doctl apps propose` validates a spec without applying it. Run it before every `update`.

### Events and job invocations

Text output is a summary; add the global `-o json` flag for the full record and its failure reason. Only
autoscaling events can be cancelled, and job invocations are individual runs of a `job` component.

```bash
doctl apps list-events <id> --event-type DEPLOYMENT,AUTOSCALING   # narrow the list above
doctl apps get-event <id> <event-id>
doctl apps logs <id> --event-id <event-id>                 # the logs one autoscaling event produced
doctl apps list-job-invocations <id>                       # both filter flags below are optional
doctl apps list-job-invocations <id> --job-name cron --deployment <deployment-id>
doctl apps get-job-invocation <id> <job-invocation-id>
doctl apps logs <id> --job-invocation <job-invocation-id>  # output of one run
# Stop work already in flight (⚠️ requires approval — an event leaves the app part-scaled, a job stops mid-write)
doctl apps cancel-event <id> <event-id>
doctl apps cancel-job-invocation <id> <job-invocation-id>   # (⚠️ requires approval)
```

### Instances, alerts, regions, and sizes

`list-regions` and `tier instance-size list` take no app ID. Use them to pick a `region` and `instance_size_slug`.

```bash
doctl apps list-instances <id>           # the ephemeral compute instances running right now
doctl apps list-alerts <id> --format ID,Trigger,Spec.Rule
# Repoint one alert's emails and Slack webhooks (⚠️ requires approval)
# The flag is --app-alert-destinations. The built-in help example prints --alert-destinations, which is wrong.
doctl apps update-alert-destinations <id> <alert-id> --app-alert-destinations destinations.yaml
doctl apps list-regions                  # add --format Slug,DataCenters,Disabled,Reason
doctl apps tier instance-size list
doctl apps tier instance-size get <instance-size-slug>
```

### Buildpacks

```bash
doctl apps list-buildpacks --format ID,Version   # columns: Name, ID, Version, Documentation
# Upgrade (⚠️ requires approval — --trigger-deployment defaults to true, so this deploys)
# --buildpack is required and wants the buildpack ID from list-buildpacks, not its name
doctl apps upgrade-buildpack <id> --buildpack <buildpack-id>
doctl apps upgrade-buildpack <id> --buildpack <buildpack-id> --major-version 3 --trigger-deployment=false   # (⚠️ requires approval)
```

### Spec validation

`spec validate` checks a file locally. `propose` is the server-side dry run. Validate while editing, propose
before applying.

```bash
doctl apps spec get <id> --format json                   # --format here is yaml|json, not the global -o
doctl apps spec get <id> --deployment <deployment-id>    # the spec a past deployment ran
doctl apps spec validate app.yaml
doctl apps spec validate app.yaml --schema-only          # shape only, skips correctness checks
cat app.yaml | doctl apps spec validate -                # a bare - reads stdin
```

### Local development (BETA)

`doctl apps dev build` builds one component into a container image on your machine. It needs a running Docker
daemon and a git repository. It builds and stops there: it does not run your app. On success it prints the
`docker run -p 8080:8080 --rm <image>` line and leaves executing it to you.

`doctl apps dev config` writes a repo-local file, `.do/dev-config.yaml` at the top level of the git repo, never a
global one. doctl also writes `.do/.gitignore` containing `dev-config.yaml`, so the file is never committed.

```bash
# Component name is optional only when running interactively
doctl apps dev build <component>
doctl apps dev build <component> --spec .do/app.yaml     # default spec path is .do/app.yaml
doctl apps dev build <component> --app <id>              # fetch the spec from a live app instead
doctl apps dev build <component> --env-file .env --build-command "npm run build"
doctl apps dev build <component> --no-cache --timeout 15m30s --registry my-registry
# Persist those flags to .do/dev-config.yaml instead of retyping them
doctl apps dev config set registry=my-registry no_cache=true
doctl apps dev config set components.web.build_command="npm run build"
doctl apps dev config unset no_cache components.web.build_command
doctl apps dev config set spec=app.yaml --dev-config /path/to/other-config.yaml
```

## Gotchas

**App IDs are UUIDs, not names.** Use `doctl apps list` to find the ID before running any app command. `doctl apps logs` is the one subcommand that also takes a name. Everything else rejects a name with `400 invalid uuid`.

**The built-in help example for `update-alert-destinations` names a flag that does not exist.** It prints `--alert-destinations src/your-alert-destinations.yaml`. Copy it and you get `Error: unknown flag: --alert-destinations`. The real flag is `--app-alert-destinations`.

**`doctl apps tier list` and `doctl apps tier get` are hidden and dead.** They do not appear under `doctl apps tier --help` but still parse, then fail with `410 ... resource retired: the concept of tiers has been retired`. Use `doctl apps tier instance-size list` instead.

**`doctl apps dev` is useless outside a git repo.** Both `dev build` and `dev config` walk up for the top-level git directory to find their workspace. Run either one in a plain directory and you get `Error: preparing workspace: no git repository found`.

**`doctl apps dev config unset` blanks a key, it does not remove it.** After `unset no_cache` the file still holds `no_cache: ""`. That empty string is what gets loaded on the next build. Delete the line by hand if you need the key genuinely gone.
