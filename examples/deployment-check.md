# Is the deployment still fine

A short read-only check of what is already deployed. Answers in one line when
nothing is wrong, which is most of the time.

---

Check this project's existing DigitalOcean deployment. Read-only, change nothing.

- Live account. Run list and get only, never create, update, delete, or start.
  A bogus `--access-token` is not a dry run, doctl ignores it. See the auth
  gotcha in `/do-ops`.
- Never print a credential value. Reference a secret by name.
- Read `DO_CONTEXT` and `DO_PROJECT` from this project's `.env`, pass
  `--context "$DO_CONTEXT"` on every command, and look only at resources
  assigned to `DO_PROJECT`.
- Use `-o json`. The text columns drop fields the JSON object carries.

Check what is running against what this repo expects, plus:

- anything billing for nothing: powered-off droplets still bill at the full
  rate, unattached volumes, unassigned reserved IPs, snapshots whose source
  is gone
- anything open: inbound `0.0.0.0/0` on 22 or all ports, droplets with no
  firewall, databases with an empty trusted-source list, certs near expiry
- anything with no safety net: droplets with no backup policy, single-node
  databases

Answer in one line if it is clean: `all systems good`.

Otherwise list only what needs changing, one line each, worst first, with the
command that fixes it. No report, no summary of what you checked, no praise for
what is fine. One line per thing you could not check and why.

---

For the full version with fixed check ids, severity counts, and output you can
diff between runs, use `/do-audit` instead.
