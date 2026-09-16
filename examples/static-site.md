# Static site on Spaces + CDN

Cheaper than App Platform for plain files. No build step, no instance.

---

Publish this site's build output to Spaces and put the CDN in front of it.

- Spaces does not use `doctl` auth. It needs the six `DO_SPACES_*` variables in the
  environment. `/do-spaces` covers where they come from; ask me if any are missing rather
  than proceeding with an empty one.
- Sync the build directory to the bucket, public-read.
- Set up the CDN endpoint and give me the URL.
- Flush the CDN cache at the end, otherwise I get the old files for up to an hour.

Tell me which files you're about to delete before any sync that prunes.

---

An empty `DO_SPACES_BUCKET` expands to a path like `s3:///images/file.jpg` that looks
almost right and silently targets nothing. `/do-spaces` has the guard for this.
