# First-time project setup

Run this once per repo, before any deploy. It decides which account you are on and
writes it down, so no later prompt has to guess.

---

Set up this project for DigitalOcean deploys.

- Use `/do-ops` to show me the auth contexts and which one is currently starred.
- Ask me which account this project deploys to. Do not assume the starred one, and do
  not infer it from the directory name or the git remote.
- Use `/do-projects` to list projects on that account and ask me which one new resources
  should land in.
- Write `DO_CONTEXT` and `DO_PROJECT` to this project's `.env`, creating it if needed.
  Add `DO_APP_REPO` as `owner/repo` if this is going to App Platform.
- Confirm `.env` is gitignored. These are not secrets, but they are per-machine.

Then read back the account email so I can confirm it's the right one.
