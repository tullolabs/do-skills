#!/usr/bin/env python3
"""Two gates for do-skills. Run before any commit that touches commands.

  gate 1  every `doctl` path and flag written in a skill exists in `doctl --help`
  gate 2  every doctl leaf command is documented in some skill, or explicitly excluded

Usage:  ./validate.py [path-to-doctl]
"""
import re, sys, glob, os, subprocess
from collections import defaultdict

DOCTL = sys.argv[1] if len(sys.argv) > 1 else "doctl"
ROOT = os.path.dirname(os.path.abspath(__file__))
FILES = sorted(glob.glob(os.path.join(ROOT, "do-*", "SKILL.md")))
# Gate 1 also checks bundled playbooks; gate 2 deliberately does not. A leaf documented
# only inside a playbook would otherwise count as covered and hide a missing product skill.
PLAYBOOKS = sorted(glob.glob(os.path.join(ROOT, "do-*", "playbooks", "*.md")))

# Commands that intentionally stay undocumented, with the reason.
EXCLUDED = {
    "completion bash": "shell plumbing, not a DO operation",
    "completion fish": "shell plumbing, not a DO operation",
    "completion zsh": "shell plumbing, not a DO operation",
    "completion powershell": "shell plumbing, not a DO operation",
    "help": "built-in help",
    "version": "covered by the stale-doctl gotcha in /do-ops",
}

def helptext(path):
    r = subprocess.run([DOCTL] + path.split() + ["--help"], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr

def skill_commands():
    """Every doctl invocation written in the skills, with continuations joined."""
    paths, locs = defaultdict(set), defaultdict(list)
    for f in FILES + PLAYBOOKS:
        lines, buf, start = [], "", 0
        for i, raw in enumerate(open(f).read().split("\n"), 1):
            s = raw.split("#")[0].rstrip()
            if buf == "":
                start = i
            if s.endswith("\\"):
                buf += s[:-1].strip() + " "
                continue
            lines.append((start, (buf + s.strip()).strip()))
            buf = ""
        for i, s in lines:
            s = s.strip().lstrip("$ ")
            if not s.startswith("doctl "):
                continue
            s = s.split("|")[0].split(">")[0].strip()
            path, flags, seen = [], [], False
            for t in s.split()[1:]:
                if t.startswith("-") and len(t) > 1:
                    seen = True
                    flags.append(t.split("=")[0])
                elif not seen and re.fullmatch(r"[a-z0-9][a-z0-9-]*", t):
                    path.append(t)
            if path:
                k = " ".join(path)
                paths[k].update(flags)
                locs[k].append(f"{os.path.relpath(f, ROOT)}:{i}")
    return paths, locs

def gate1():
    paths, locs = skill_commands()
    bad, help_of, real_of = [], {}, {}
    for k in sorted(paths):
        rc, h = helptext(k)
        help_of[k] = h
        if rc != 0 or "Usage:" not in h:
            bad.append(f"no such command: doctl {k}  ({locs[k][0]})")
            continue
        # cobra accepts an unknown trailing word as a positional and prints the parent's
        # help, so rc==0 does not prove the subcommand exists. Keep the path cobra echoes
        # back; anything we wrote beyond it was swallowed as an argument.
        m = re.search(r"^Usage:\n\s+doctl\s+(.*)$", h, re.M)
        real_of[k] = [t for t in m.group(1).split()
                      if re.fullmatch(r"[a-z0-9][a-z0-9-]*", t)] if m else k.split()

    # Every token cobra itself uses as a path component. A swallowed tail that appears
    # here is a phantom subcommand; one that does not is a literal example value like
    # `my-registry` or `web`, which is correct usage and must not fail the gate.
    known = {t for r in real_of.values() for t in r}
    for k in sorted(real_of):
        tail = [t for t in k.split()[len(real_of[k]):] if t in known]
        if tail:
            bad.append(f"not a subcommand: doctl {k}  "
                       f"(real: doctl {' '.join(real_of[k])})  ({locs[k][0]})")
            continue
        h = help_of[k]
        for fl in sorted(paths[k]):
            if not re.search(r"(^|\s)" + re.escape(fl) + r"(\s|,|=|$)", h, re.M):
                bad.append(f"no such flag: {fl} on doctl {k}  ({locs[k][0]})")
    print(f"gate 1  commands written: {len(paths)}   "
          f"flag pairs: {sum(len(v) for v in paths.values())}   problems: {len(bad)}")
    for b in bad:
        print("        " + b)
    return not bad

def leaves():
    """Walk the whole doctl tree and return every leaf command path."""
    HEADS = ("Available Commands", "Manage DigitalOcean Resources", "Inference",
             "Configure doctl", "View Billing", "Additional Commands")
    out = []
    def kids(path):
        _, h = helptext(" ".join(path)) if path else helptext("")
        found = []
        for head in HEADS:
            for m in re.finditer(rf"^{head}:\n((?:[ \t]+\S.*\n|\n(?=[ \t]+\S))*)", h, re.M):
                found += re.findall(r"^\s{2,}([a-z0-9][a-z0-9-]*)\s+\S", m.group(1), re.M)
        return sorted(set(found))
    def walk(path):
        c = kids(path)
        if not c:
            out.append(" ".join(path))
            return
        for k in c:
            walk(path + [k])
    for top in kids([]):
        walk([top])
    return out

def gate2():
    blob = "\n".join(open(f).read() for f in FILES)
    missing = []
    all_leaves = leaves()
    for leaf in all_leaves:
        if leaf in EXCLUDED:
            continue
        if not re.search(r"doctl " + re.escape(leaf) + r"(?![a-z0-9-])", blob):
            missing.append(leaf)
    print(f"gate 2  leaf commands: {len(all_leaves)}   "
          f"excluded: {len(EXCLUDED)}   undocumented: {len(missing)}")
    for m in missing:
        print("        missing: doctl " + m)
    return not missing

if __name__ == "__main__":
    rc, v = helptext("version")
    print(f"doctl: {DOCTL}  {v.splitlines()[0] if v else '?'}\n"
          f"files: {len(FILES)} skills + {len(PLAYBOOKS)} playbooks\n")
    ok = gate1()
    ok = gate2() and ok
    print("\nPASS" if ok else "\nFAIL")
    sys.exit(0 if ok else 1)
