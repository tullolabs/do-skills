---
name: do-apps
description: DigitalOcean App Platform operations with doctl. Use for listing apps, reading build, deploy, and runtime logs, getting or validating an app spec, triggering a deploy or restart, and hosting static sites. Also covers why a static site needs its own domain instead of a sub-path.
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

## Gotchas

**App IDs are UUIDs, not names.** Use `doctl apps list` to find the ID before running any app command. `doctl apps logs` is the one subcommand that also takes a name. Everything else rejects a name with `400 invalid uuid`.
