# Deploy a repo to App Platform

For anything that builds from a Dockerfile or a buildpack and doesn't need a whole VM.

---

Deploy this repo to DigitalOcean App Platform.

- Confirm the target account with `/do-ops` before anything else.
- Read `DO_APP_REPO` from this project's `.env` for the source repo. If it's missing, ask
  me. Do not guess it from the git remote.
- Generate an app spec, then validate it before applying. `/do-apps` has the command that
  dry-runs a spec without changing anything; run that until it's clean.
- Smallest instance size that fits, one instance to start.
- Assign the app to `DO_PROJECT` with `/do-projects` after it deploys.

Show me the spec and the monthly cost before you create the app.

---

If this is a static site, say so: App Platform treats those differently and it cannot be
served from the default `ondigitalocean.app` domain. `/do-apps` covers why.
