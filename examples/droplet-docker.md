# Docker on a droplet, under $10/mo

The leanest thing that comfortably runs a Compose stack. $6/mo.

---

Stand up a droplet running my Docker Compose stack.

- Check `/do-ops` first for which account and context you are pointed at. If `DO_CONTEXT`
  is not set in this project's `.env`, stop and ask me which account this deploys to.
- Size `s-1vcpu-1gb`, $6/mo, in the region nearest me. Do not exceed $10/mo.
- Image `docker-20-04`, created with `/do-droplets`. It ships Docker and Compose already
  installed. The slug says
  20-04 but it is Ubuntu 22.04, so do not "correct" it to a 24.04 slug.
- Bring the stack up on first boot by passing a cloud-init file with `--user-data-file`.
  Use the `compose.yaml` in this repo; ask me if there isn't one.
- Add a cloud firewall allowing inbound 22, 80, and 443 and nothing else. See `/do-network`.
- Assign it to `DO_PROJECT` with `/do-projects` once it exists. Nothing lands in a project
  by itself, so this is a separate step and easy to forget.
- Tag it so I can find it again.

Show me the monthly cost and the exact create command before you run anything.

---

512MB ($4/mo, `s-1vcpu-512mb-10gb`) exists and will boot Docker, but a build or a second
container will hit the OOM killer. Use it for a single tiny container, not Compose.
