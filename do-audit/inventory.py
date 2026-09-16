#!/usr/bin/env python3
"""Build the scoped, credential-free inventory that every audit playbook reads.

    ./inventory.py <project-name-or-id> <out-dir> [doctl-context]

Writes <out-dir>/inventory.json and prints a one-line count summary. Read-only:
every doctl call below is a `list` or `get`.

Two reasons this is a script and not a list of commands in the playbook. doctl
embeds live secrets in ordinary output (`databases list -o json` returns
connection.password and users[].password), so redaction has to happen before
anything is written or shown. And running the listers once here keeps tens of
thousands of tokens of raw JSON out of six subagents' context windows.
"""
import json, subprocess, sys, os, datetime

# Value replaced, key kept, so an audit can still see that a credential exists.
REDACT = {"password", "uri", "private_uri", "token", "access_token", "api_token",
          "secret", "private_key", "auth_key", "service_key", "bgp_auth_key",
          "credentials", "certificate_chain", "leaf_certificate"}

# app.active_deployment repeats the whole spec plus every build step, ~9 KB per app.
# Six subagents read this file, so anything duplicated here is paid for six times.
DROP = {"active_deployment", "metrics_endpoints", "private_connection"}

# urn type -> lister, and the field holding the id that the URN is built from.
SOURCES = [
    ("droplet",      "compute droplet list",      "id"),
    ("volume",       "compute volume list",       "id"),
    ("dbaas",        "databases list",            "id"),
    ("app",          "apps list",                 "id"),
    ("domain",       "compute domain list",       "name"),
    ("kubernetes",   "kubernetes cluster list",   "id"),
    ("loadbalancer", "compute load-balancer list", "id"),
    ("floatingip",   "compute reserved-ip list",  "ip"),
]

CTX = sys.argv[3] if len(sys.argv) > 3 else ""
gaps = []

def scrub(o, top=False):
    if isinstance(o, dict):
        return {k: ("[redacted]" if k in REDACT and o[k] else scrub(v))
                for k, v in o.items() if not (top and k in DROP)}
    return [scrub(v, top) for v in o] if isinstance(o, list) else o

def strip_env_values(spec):
    """Drop app env values, keep every key, scope, and type.

    A real account returned 1545 plaintext env values across 67 apps and no audit check
    reads one. Dropping them is 29% off spec bytes and removes the risk of an operator's
    mislabelled secret riding along. SECRET-typed envs come back encrypted (`EV[1:...]`)
    and are redacted too, since an audit has no use for either form.
    """
    for group in ("services", "workers", "jobs", "static_sites", "functions"):
        for c in spec.get(group) or []:
            for e in c.get("envs") or []:
                e["value"] = "[redacted]"
    for e in spec.get("envs") or []:
        e["value"] = "[redacted]"
    return spec

def do(cmd):
    """Run a read-only doctl command, return scrubbed JSON. Records gaps, never raises."""
    argv = ["doctl"] + cmd.split() + ["-o", "json"] + (["--context", CTX] if CTX else [])
    r = subprocess.run(argv, capture_output=True, text=True)
    if r.returncode != 0:
        gaps.append(f"doctl {cmd}: {(r.stderr or r.stdout).strip().splitlines()[0][:120]}")
        return []
    return scrub(json.loads(r.stdout.strip() or "[]") or [], top=True)

def main():
    project, outdir = sys.argv[1], sys.argv[2]
    projects = do("projects list")
    hit = [p for p in projects if project in (p.get("id"), p.get("name"))]
    if len(hit) != 1:
        sys.exit(f"DO_PROJECT {project!r} matched {len(hit)} projects. "
                 f"Known: {', '.join(repr(p['name']) for p in projects)}")
    proj = hit[0]

    assigned = do(f"projects resources list {proj['id']}")
    urns = {r["urn"]: r for r in assigned}
    in_scope = lambda t, i: f"do:{t}:{i}" in urns

    acct = do("account get")
    inv = {"generated": datetime.datetime.now(datetime.timezone.utc)
                                .strftime("%Y-%m-%dT%H:%M:%SZ"),
           "project": {k: proj.get(k) for k in ("id", "name", "purpose", "environment", "is_default")},
           "account": {k: acct.get(k) for k in ("email", "uuid", "team")} if isinstance(acct, dict) else {},
           "urn_count": len(urns), "resources": {}}

    for typ, cmd, idf in SOURCES:
        items = [x for x in do(cmd) if in_scope(typ, x.get(idf))]
        for x in items:
            x["_urn"] = f"do:{typ}:{x.get(idf)}"
            x["_assigned_at"] = urns[x["_urn"]].get("assigned_at")
        inv["resources"][typ] = items

    for a in inv["resources"]["app"]:
        if a.get("spec"):
            strip_env_values(a["spec"])

    droplets = inv["resources"]["droplet"]
    dids = {d["id"] for d in droplets}
    vids = {v["id"] for v in inv["resources"]["volume"]}

    # Firewalls and VPCs are not project-assignable, so pivot through the droplets.
    fws = {}
    for d in droplets:
        for f in do(f"compute firewall list-by-droplet {d['id']}"):
            fws[f["id"]] = f
    inv["resources"]["firewall"] = list(fws.values())
    inv["resources"]["vpc"] = [v for v in do("vpcs list")
                               if v.get("id") in {d.get("vpc_uuid") for d in droplets}]

    # Snapshots and alert policies attach to a scoped resource rather than the project.
    inv["resources"]["snapshot"] = [s for s in do("compute snapshot list")
                                    if str(s.get("resource_id")) in {str(i) for i in dids | vids}]
    inv["resources"]["alert"] = [a for a in do("monitoring alert list")
                                 if dids & {int(e) for e in a.get("entities") or [] if str(e).isdigit()}]
    inv["resources"]["backup_policy"] = [p for p in do("compute droplet backup-policies list")
                                         if p.get("droplet_id") in dids]

    # The droplet size catalog goes in its own file. Only the cost playbook joins against
    # it, and inlining 120 sizes would charge the other five playbooks for it too.
    prices = {s["slug"]: [s.get("price_monthly"), s.get("vcpus"), s.get("memory"), s.get("disk")]
              for s in do("compute size list")}

    # No project link, but scoped resources reference them.
    inv["account_wide"] = {"certificate": do("compute certificate list"),
                           "cdn": do("compute cdn list")}
    inv["unresolved_urns"] = sorted(u for u in urns if u.split(":")[1]
                                    not in {t for t, _, _ in SOURCES} | {"space"})
    inv["spaces"] = sorted(u.split(":", 2)[2] for u in urns if u.startswith("do:space:"))
    inv["gaps"] = gaps

    os.makedirs(outdir, exist_ok=True)
    for name, blob in (("inventory.json", inv),
                       ("prices.json", {"_fields": ["usd_mo", "vcpus", "memory_mb", "disk_gb"],
                                        "sizes": prices})):
        with open(os.path.join(outdir, name), "w") as fh:
            json.dump(blob, fh, separators=(",", ":"), sort_keys=True)
    counts = {k: len(v) for k, v in inv["resources"].items() if v}
    print(f"project={proj['name']} urns={len(urns)} " +
          " ".join(f"{k}={v}" for k, v in sorted(counts.items())) +
          (f" gaps={len(gaps)}" if gaps else ""))

if __name__ == "__main__":
    main()
