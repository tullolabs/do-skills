# Working on do-skills

Instructions for any agent or human touching this repo. `CLAUDE.md` is a one-line import
of this file, so there is only ever one copy to keep current.

## Writing style

**Em dashes are fine in this repo.** The global unslop rule against them does not apply
here. Do not strip them, do not rewrite them into commas or periods. This was decided
deliberately; leave them alone.

Everything else about house style is set by the existing files. Match them rather than
inventing a new shape. In short: frontmatter is four keys in a fixed order, the body
opens with an H1 and the shared two-line approval and auth blockquote, commands live in
```bash fences with terse `#` labels, destructive commands carry `(⚠️ requires approval)`,
and the file ends with `## Gotchas` written as bolded-lead-in paragraphs.

## This is a live DigitalOcean account

Run `doctl <path> --help` and nothing else. Never run a command that creates, deletes, or
modifies anything, not even to see what error it returns.

An agent on an earlier pass tried exactly that: it passed `--access-token fake-token-xxxx`
to `monitoring uptime create` expecting a 401 it could document. doctl ignored the token
override and created a real, billable uptime check on the account. It was deleted within
the minute, but the lesson is that a bogus credential is not a dry run. `--help` is the
only safe way to learn what a command does.

## Accuracy rule

Every command in this repo must be verified against `doctl --help` before it is written
or changed. Do not write a command, flag, or positional argument from memory.

This is not paranoia. Earlier passes on this repo shipped a flag that was actually a
positional, an engine slug claim that was half true, and a database firewall documented
backwards. Every one came from writing first and checking afterward.

Validate the whole repo with `validate.py`, which runs two gates:

```bash
./validate.py              # uses whichever doctl is on PATH
./validate.py /tmp/doctl   # or point it at a specific build
```

Gate 1 asserts every `doctl` path and flag written in a skill exists in `--help`.
Gate 2 walks the whole `doctl` tree and asserts every leaf command is documented in some
skill or named in the `EXCLUDED` dict with a reason. Gate 2 is what keeps "covers the
full catalog" honest when DigitalOcean ships a new product. Re-run both before any commit
that touches commands.

One warning about gate 2, learned the hard way. Its tree walker parses `--help` output by
column, and an early version required two or more spaces after a command name. Cobra pads
each group to a fixed column, so the *longest* name in every group gets exactly one space
and was silently dropped, along with everything beneath it. That hid 55 commands and made
the gate report a confident, wrong 456. If you touch the `leaves()` regex, check the total
moves in the direction you expect, and spot-check a group's longest-named command by hand.

## Scope

One skill per product area, named `do-<product>`, each standalone and invocable as
`/do-<product>`. `do-ops` is the index and owns auth, billing, and cross-cutting gotchas.
A skill's frontmatter `description` is always resident in an agent's context, so keep it
tight and packed with the words someone would actually search for.
