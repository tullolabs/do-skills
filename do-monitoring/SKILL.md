---
name: do-monitoring
description: DigitalOcean Monitoring. Use for metric alert policies on droplets, load balancers, and database clusters, and uptime checks against a URL or IP with latency, downtime, and SSL expiry alerts.
user-invocable: true
argument-hint: "[alert|uptime|create|delete]"
---

# Monitoring and Alerts

> Destructive ops need operator approval. Reads are always safe.
> Auth: `doctl` is pre-authenticated. See `/do-ops` for auth contexts.

### Metric alert policies

Target a fixed list with `--entities` or every tagged resource with `--tags`. `--window` takes `5m`, `10m`,
`30m`, or `1h`.

```bash
doctl monitoring alert list
doctl monitoring alert get <alert-policy-uuid>

# (⚠️ requires approval)
doctl monitoring alert create \
  --type v1/insights/droplet/memory_utilization_percent \
  --compare GreaterThan \
  --value 80 \
  --window 5m \
  --entities 386734086,191669331 \
  --emails admin@example.com

# Every droplet carrying a tag, alerting into Slack instead of email
# (⚠️ requires approval)
doctl monitoring alert create --type v1/insights/droplet/cpu --compare GreaterThan --value 90 \
  --window 10m --tags project-name --slack-channels production-alerts \
  --slack-urls https://hooks.slack.com/services/T1234567/AAAAAAAA/ZZZZZZ

# --type values accepted by doctl 1.168:
#   v1/insights/droplet/   cpu load_1 load_5 load_15 memory_utilization_percent
#                          disk_utilization_percent disk_read disk_write public_outbound_bandwidth
#   v1/insights/lbaas/     avg_cpu_utilization_percent connection_utilization_percent droplet_health
#                          tls_connections_per_second_utilization_percent
#                          increase_in_http_error_rate_percentage_4xx and _5xx, _count_4xx and _count_5xx
#                          high_http_request_response_time and its _50p _95p _99p variants
#   v1/dbaas/alerts/       cpu_alerts memory_utilization_alerts disk_utilization_alerts load_15_alerts

# (⚠️ requires approval)
doctl monitoring alert update <alert-policy-uuid> --type v1/insights/droplet/cpu \
  --compare GreaterThan --value 90 --window 30m --entities 386734086 --emails admin@example.com

doctl monitoring alert delete <alert-policy-uuid>    # (⚠️ requires approval)
```

`update` replaces the whole policy, so re-send every field, not just the one you changed. Droplet IDs for
`--entities` come from `/do-droplets`; database entities are cluster UUIDs.

### Uptime checks and their alerts

A check monitors one endpoint over `--type` `http`, `https`, or `ping` from the regions you name. Alerts nest
under a check, so the check has to exist first.

```bash
doctl monitoring uptime list
doctl monitoring uptime get <uptime-check-id>
doctl monitoring uptime create my-check --target https://example.com --type https --regions us_east,us_west   # (⚠️ requires approval)
# (⚠️ requires approval)
doctl monitoring uptime update <uptime-check-id> --name my-check --type https \
  --target https://example.com --regions us_east,us_west
doctl monitoring uptime delete <uptime-check-id>     # (⚠️ requires approval)

doctl monitoring uptime alert list <uptime-check-id>
doctl monitoring uptime alert get <uptime-check-id> <uptime-alert-id>

# --threshold is milliseconds for latency, days for ssl_expiry, and unused for down / down_global
# (⚠️ requires approval)
doctl monitoring uptime alert create <uptime-check-id> \
  --name "Example Alert" --type latency --threshold 100 --comparison greater_than \
  --period 2m --emails admin@example.com

# (⚠️ requires approval)
doctl monitoring uptime alert update <uptime-check-id> <uptime-alert-id> \
  --name "Example Alert" --type down --comparison greater_than --period 5m --emails admin@example.com

doctl monitoring uptime alert delete <uptime-check-id> <uptime-alert-id>   # (⚠️ requires approval)
```

`--regions` takes `us_east`, `us_west`, `eu_west`, or `se_asia` and defaults to `us_east` alone. `--period`
takes `2m`, `3m`, `5m`, `10m`, `15m`, `30m`, or `1h`.

## Gotchas

**Nothing on `monitoring alert create` is a required flag, so the validation errors arrive one at a time.** Run it bare and you get `'' is not a valid alert policy type`. Add `--type` and you get `comparator must be GreaterThan or LessThan`. Add `--compare` and you get `must provide either emails or slack details to send the alert to`. Supply `--type`, `--compare`, and a destination together.

**`uptime create` takes the check name as a positional, but `uptime update` takes it as `--name`.** The help example for create omits the positional entirely, and copying it verbatim fails with `(uptime.create) command is missing required arguments`. The name goes immediately after `create`, before any flag.

**Every uptime alert subcommand except `create` and `list` wants two positionals.** The order is always `<uptime-check-id> <uptime-alert-id>` for `get`, `update`, and `delete`. There is no way to look up an alert without its parent check ID.

**`doctl` cannot disable an uptime check once it exists.** `--enabled` is on `create` and defaults to true, but `update` has no such flag and its help says checks can only be disabled from the control panel or the public API. Delete the check, or delete its alerts and leave it running.

**`doctl`'s `--type` validator is narrower than the monitoring API, so "not a valid alert policy type" does not mean the alert is impossible.** doctl 1.168 rejects `public_inbound_bandwidth`, `private_outbound_bandwidth`, `private_inbound_bandwidth`, `load_1`/`load_5` for dbaas, and the whole `v1/droplet/autoscale_alerts/` family, all of which the API documents as valid. The rejection happens client-side before any request, so the list above is what the binary accepts, not what DigitalOcean supports. For a type doctl refuses, post to `/v2/monitoring/alerts` directly; see `/do-ops` for the raw API recipe.
