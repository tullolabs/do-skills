---
name: do-network
description: DigitalOcean networking operations with doctl. Use for creating VPCs and peerings, editing cloud firewall rules, building load balancers, uploading SSL certificates, and assigning reserved IPv4 and IPv6 addresses. Also covers NAT gateways and Partner Network Connect.
user-invocable: true
argument-hint: "[list|create|update|delete] [vpc]"
---

# Networking

> Destructive ops need operator approval. Reads are always safe.
> Auth: `doctl` is pre-authenticated. See `/do-ops` for auth contexts.

Firewalls, load balancers, and NAT gateways all take VPC and droplet IDs. Collect them from `doctl vpcs list` first.

### VPCs

Every region already has a default VPC. Create one only when you want a separate private network.

```bash
doctl vpcs list --format Name,IPRange,Region,Default
doctl vpcs get <vpc-id>
# Create (⚠️ requires approval). Omit --ip-range and DO picks a range.
doctl vpcs create --name my-vpc --region sgp1 --ip-range 10.116.0.0/20 --description "app tier"
doctl vpcs update <vpc-id> --name new-name      # (⚠️ requires approval)
doctl vpcs update <vpc-id> --default=true       # (⚠️ requires approval — moves the region default)
doctl vpcs delete <vpc-id>                      # (⚠️ requires approval — irreversible)

# --- Peerings ---
doctl vpcs peerings list --vpc-id <vpc-id>      # omit --vpc-id to list them all
doctl vpcs peerings get <peering-id>
# Create — name is positional, then exactly two VPC IDs (⚠️ requires approval)
doctl vpcs peerings create my-peering \
  --vpc-ids f81d4fae-7dec-11d0-a765-00a0c91e6bf6,3f900b61-30d7-40d8-9711-8c5d6264b268 --wait
doctl vpcs peerings update <peering-id> --name new-name   # --name required (⚠️ requires approval)
doctl vpcs peerings delete <peering-id> --wait            # (⚠️ requires approval)
```

### Cloud firewalls

A rule is one comma-separated key-value string needing `protocol`, `ports`, and one of `address`,
`droplet_id`, `load_balancer_uid`, `kubernetes_id`, or `tag`. Multiple rules go in one quoted flag,
space-separated. `ports` takes `22`, `8000-9000`, or `all`.

```bash
doctl compute firewall list
doctl compute firewall get <firewall-id>
doctl compute firewall list-by-droplet <droplet-id>
# Create — needs --name plus at least one rule (⚠️ requires approval)
doctl compute firewall create --name example-firewall \
  --inbound-rules "protocol:tcp,ports:22,address:192.0.2.0/24 protocol:tcp,ports:443,address:0.0.0.0/0" \
  --outbound-rules "protocol:tcp,ports:all,address:0.0.0.0/0 protocol:udp,ports:53,address:0.0.0.0/0" \
  --droplet-ids 386734086,391669331 --tag-names frontend,backend
# Edit rules in place — safer than update, touches only what you name (⚠️ requires approval)
doctl compute firewall add-rules <firewall-id> --inbound-rules "protocol:tcp,ports:5432,tag:app"
doctl compute firewall remove-rules <firewall-id> --outbound-rules "protocol:udp,ports:53,address:0.0.0.0/0"   # (⚠️ requires approval)
# Membership (⚠️ requires approval)
doctl compute firewall add-droplets <firewall-id> --droplet-ids 386734086,391669331
doctl compute firewall remove-droplets <firewall-id> --droplet-ids 386734086   # (⚠️ requires approval)
doctl compute firewall add-tags <firewall-id> --tag-names frontend,backend   # (⚠️ requires approval)
doctl compute firewall remove-tags <firewall-id> --tag-names backend   # (⚠️ requires approval)
# Full replace — pass every attribute you want kept (⚠️ requires approval — resets omitted fields)
doctl compute firewall update <firewall-id> --name example-firewall \
  --inbound-rules "protocol:tcp,ports:22,address:192.0.2.0/24" \
  --outbound-rules "protocol:tcp,ports:all,address:0.0.0.0/0" \
  --droplet-ids 386734086,391669331
# Delete — takes one or more IDs; droplets are untouched (⚠️ requires approval)
doctl compute firewall delete <firewall-id>
```

### Load balancers

Forwarding rules are comma-separated key-value strings of `entry_protocol`, `entry_port`,
`target_protocol`, `target_port`, plus optional `certificate_id` or `tls_passthrough`. Protocols:
`http`, `https`, `http2`, `http3`, `tcp`, `udp`.

```bash
doctl compute load-balancer list --format ID,Name,IP,Status,ForwardingRules
doctl compute load-balancer get <load-balancer-id>
# Create an HTTPS-terminating LB. --name is the only required flag; --size and --size-unit are
# mutually exclusive, and --algorithm is deprecated and ignored (⚠️ requires approval)
doctl compute load-balancer create --name my-lb --region sgp1 --size lb-small --vpc-uuid <vpc-id> \
  --forwarding-rules "entry_protocol:https,entry_port:443,target_protocol:http,target_port:80,certificate_id:<certificate-id>" \
  --health-check "protocol:http,port:80,path:/health,check_interval_seconds:10,response_timeout_seconds:5,healthy_threshold:5,unhealthy_threshold:3" \
  --droplet-ids 386734086,391669331 --redirect-http-to-https --wait
# Target by tag instead of IDs — new droplets join automatically (⚠️ requires approval)
doctl compute load-balancer create --name my-lb --region sgp1 --tag-name frontend \
  --forwarding-rules "entry_protocol:tcp,entry_port:3306,target_protocol:tcp,target_port:3306"
# Incremental edits (⚠️ requires approval)
doctl compute load-balancer add-forwarding-rules <load-balancer-id> \
  --forwarding-rules "entry_protocol:tcp,entry_port:3306,target_protocol:tcp,target_port:3306"
doctl compute load-balancer remove-forwarding-rules <load-balancer-id> \
  --forwarding-rules "entry_protocol:tcp,entry_port:3306,target_protocol:tcp,target_port:3306"
doctl compute load-balancer add-droplets <load-balancer-id> --droplet-ids 12,33
doctl compute load-balancer remove-droplets <load-balancer-id> --droplet-ids 12   # (⚠️ requires approval)
# Full replace, same reset-on-omit behavior as firewalls (⚠️ requires approval)
doctl compute load-balancer update <load-balancer-id> --name my-lb --region sgp1 \
  --forwarding-rules "entry_protocol:https,entry_port:443,target_protocol:http,target_port:80" \
  --droplet-ids 386734086,391669331
doctl compute load-balancer purge-cache <load-balancer-id>   # global LBs only (⚠️ requires approval)
doctl compute load-balancer delete <load-balancer-id>        # (⚠️ requires approval — irreversible)
```

### Certificates

```bash
doctl compute certificate list --name my-cert     # omit --name to list them all
doctl compute certificate get <certificate-id> --format ID,Name,DNSNames,NotAfter,State
# Let's Encrypt — free, auto-renewed, domains must already be in DO DNS (⚠️ requires approval)
doctl compute certificate create --type lets_encrypt --name my-cert --dns-names example.com,www.example.com
# Custom upload — all three PEM paths are local files (⚠️ requires approval)
doctl compute certificate create --type custom --name my-cert \
  --leaf-certificate-path cert.pem --certificate-chain-path fullchain.pem --private-key-path privkey.pem
doctl compute certificate delete <certificate-id>     # (⚠️ requires approval)
```

### Reserved IPs

IPv4 and IPv6 are separate trees with different shapes. Attaching IPv4 lives under `reserved-ip-action`.
IPv6 puts `assign` and `unassign` on the resource itself.

```bash
# --- IPv4 ---
doctl compute reserved-ip list --region sgp1      # omit --region to list them all
doctl compute reserved-ip get 203.0.113.25
# Create — --region and --droplet-id are mutually exclusive (⚠️ requires approval)
doctl compute reserved-ip create --region sgp1
doctl compute reserved-ip create --droplet-id 386734086   # (⚠️ requires approval)
# Attach and detach live under reserved-ip-action (⚠️ requires approval)
doctl compute reserved-ip-action assign 203.0.113.25 386734086
doctl compute reserved-ip-action unassign 203.0.113.25
doctl compute reserved-ip-action get 203.0.113.25 <action-id>    # poll that action
doctl compute reserved-ip delete 203.0.113.25   # (⚠️ requires approval — releases the address)

# --- IPv6 ---
doctl compute reserved-ipv6 list
doctl compute reserved-ipv6 get <reserved-ipv6>
doctl compute reserved-ipv6 create --region sgp1                 # (⚠️ requires approval)
doctl compute reserved-ipv6 assign <reserved-ipv6> 386734086     # (⚠️ requires approval)
doctl compute reserved-ipv6 unassign <reserved-ipv6>             # (⚠️ requires approval)
doctl compute reserved-ipv6 delete <reserved-ipv6>               # (⚠️ requires approval)
```

### NAT gateways and BYOIP

A VPC NAT gateway gives private droplets one stable egress IP. `--vpcs` takes a VPC ID, optionally
suffixed with `:default` to make that gateway the VPC's default route.

```bash
doctl compute vpc-nat-gateway list
doctl compute vpc-nat-gateway get <gateway-id>
# Create and update both require --name and --region (⚠️ requires approval)
doctl compute vpc-nat-gateway create --name my-nat --region sgp1 --size 1 \
  --vpcs <vpc-id>:default --tcp-timeout 300 --udp-timeout 30 --icmp-timeout 30
doctl compute vpc-nat-gateway update <gateway-id> --name my-nat --region sgp1 --size 2
# Delete — --force has no -f shorthand here (⚠️ requires approval)
doctl compute vpc-nat-gateway delete <gateway-id>

# --- BYOIP prefixes ---
doctl network byoip-prefix list
doctl network byoip-prefix get <prefix-uuid>
doctl network byoip-prefix resource <prefix-uuid>        # what is using addresses in the prefix
doctl network byoip-prefix create --region sgp1 --prefix 198.51.100.0/24 --signature <signature>   # (⚠️ requires approval)
doctl network byoip-prefix update <prefix-uuid> --advertise=true    # (⚠️ requires approval)
doctl network byoip-prefix delete <prefix-uuid>                     # (⚠️ requires approval)
# Hand a BYOIP address to an LB or gateway with --ip on create; it must be unassigned, same region
```

### Partner Network Connect

Partner attachments bridge a DO VPC to a carrier circuit over BGP. `--type` defaults to `partner`.

```bash
doctl network attachment list
doctl network attachment get <partner-attachment-id>
doctl network attachment list-routes <partner-attachment-id> --format Cidr
doctl network attachment get-service-key <partner-attachment-id>   # hand this to the carrier
doctl network attachment get-bgp-auth-key <partner-attachment-id>
# Create — name, bandwidth, provider, region, and VPC IDs are all required (⚠️ requires approval)
doctl network attachment create --name example-pia --connection-bandwidth-in-mbps 50 \
  --naas-provider MEGAPORT --region nyc --vpc-ids c5537207-ebf0-47cb-bc10-6fac717cd672 \
  --bgp-local-asn 64512 --bgp-peer-asn 64513
# Update — both --name and --vpc-ids are required (⚠️ requires approval)
doctl network attachment update <partner-attachment-id> --name new-name --vpc-ids <vpc-id>
doctl network attachment regenerate-service-key <partner-attachment-id>   # (⚠️ requires approval — invalidates the old key)
doctl network attachment delete <partner-attachment-id> --wait            # (⚠️ requires approval — irreversible)
```

## Gotchas

**`firewall update` and `load-balancer update` reset every attribute you leave out.** Both help texts say the request must contain a full representation of the resource and that any attribute not provided is reset to its default value. Run `get` first and replay every flag, or skip `update` entirely and use `add-rules`, `remove-rules`, `add-forwarding-rules`, and `add-droplets`, which only touch what you name.

**A cloud firewall is default-deny the moment it attaches.** `create` refuses to run without at least one inbound or outbound rule, and anything you did not allow is dropped. The symptom is a connection that hangs and times out rather than returning `connection refused`. Run `doctl compute firewall list-by-droplet <droplet-id>` before blaming credentials or the service.

**You cannot delete a VPC that is a region's default network.** `doctl vpcs delete` rejects it. Promote another VPC first with `doctl vpcs update <vpc-id> --default=true`, then delete the original. A VPC also has to be empty, so move or destroy the droplets, databases, and load balancers inside it first.

**IPv4 assign and unassign are not subcommands of `reserved-ip`.** They live under `doctl compute reserved-ip-action`, and `assign` takes two positionals in the order `<reserved-ip> <droplet-id>`. `doctl compute reserved-ip assign` fails with `unknown command`. Reserved IPv6 is the opposite: `assign` and `unassign` sit directly on `doctl compute reserved-ipv6`.

**Reserved IPs are pinned to the region they were created in.** You can only assign one to a droplet in that same region, and `reserved-ip create` rejects `--region` alongside `--droplet-id` because the droplet already fixes the region. Unassigned IPv4 reserved addresses keep billing, so delete them instead of parking them.

**A `lets_encrypt` certificate only issues for domains DigitalOcean already serves DNS for.** Every `--dns-names` entry must resolve through DO nameservers or the certificate sits in `pending` and then flips to `error`. Check with `doctl compute certificate get <certificate-id> --format State`, and see `/do-dns` for delegating the zone. A `custom` certificate skips that but needs all three PEM files: leaf, chain, and private key.
