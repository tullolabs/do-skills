---
name: do-ai
description: DigitalOcean Gradient AI. Use for agents and agent routes, knowledge bases, indexing jobs, scenario sets and simulations, vector databases, dedicated GPU inference, and the serverless chat, embeddings, and image APIs.
user-invocable: true
argument-hint: "[list|create|attach|invoke] [agent]"
---

# AI and Inference

> Destructive ops need operator approval. Reads are always safe.
> Auth: `doctl` is pre-authenticated. See `/do-ops` for auth contexts.

Aliases: `doctl gradient` also answers to `ai`, `genai`, and `gradientai`; `vector-databases` is `vdb`,
`dedicated-inference` is `di`, and `serverless-inference` is `inference` or `si`.

### Gradient agents

Model and region IDs come from `list-models` and `list-regions`. Neither route subcommand takes a positional.

```bash
# all five flags are required (⚠️ requires approval — billable)
doctl gradient agent create --name "my-agent" --project-id <project-id> --model-id <model-id> \
  --region tor1 --instruction "You answer billing questions" --knowledge-base-id <knowledge-base-id>

doctl gradient agent list --region tor1 --tag production    # both filters optional
doctl gradient agent get <agent-id>
doctl gradient agent list-versions <agent-id>               # shows which version is CurrentlyApplied

# Tune a live agent (⚠️ requires approval)
doctl gradient agent update <agent-id> --instruction "..." --temperature 0.2 --top-p 0.9 --max-tokens 512
doctl gradient agent update <agent-id> --k 5 --retrieval-method RETRIEVAL_METHOD_REWRITE   # (⚠️ requires approval)
doctl gradient agent update <agent-id> --model-id <model-id> --openai-key-id <openai-key-id>   # (⚠️ requires approval) swap the model

doctl gradient agent update-visibility <agent-id> --visibility VISIBILITY_PUBLIC   # (⚠️ requires approval — enables the unauthenticated chatbot embed; direct endpoint calls still need an access key)
doctl gradient agent delete <agent-id>                                             # (⚠️ requires approval)

# --- Agent API keys: the bearer token callers use against the agent endpoint ---
doctl gradient agent apikeys list --agent-id <agent-id>
doctl gradient agent apikeys create --name "prod-key" --agent-id <agent-id>       # (⚠️ requires approval)
doctl gradient agent apikeys update <apikey-id> --agent-id <agent-id> --name "new-name"   # (⚠️ requires approval)
doctl gradient agent apikeys regenerate <apikey-id> --agent-id <agent-id>         # (⚠️ requires approval — old value stops working)
doctl gradient agent apikeys delete <apikey-id> --agent-id <agent-id>             # (⚠️ requires approval)

# --- Agent routes: parent agent delegates to a child agent ---
# (⚠️ requires approval)
doctl gradient agent route add --parent-agent-id <agent-id> --child-agent-id <agent-id> \
  --route-name billing --if-case "the user asks about an invoice"                 # (⚠️ requires approval)
doctl gradient agent route update --parent-agent-id <agent-id> --child-agent-id <agent-id> --if-case "..."  # (⚠️ requires approval)
doctl gradient agent route delete --parent-agent-id <agent-id> --child-agent-id <agent-id>  # (⚠️ requires approval)

# --- Function routes: agent calls a DigitalOcean Functions function. All seven flags required ---
# (⚠️ requires approval)
doctl gradient agent functionroute create --agent-id <agent-id> --name get-weather \
  --description "Looks up weather" --faas-name default/testing --faas-namespace <namespace-id> \
  --input-schema '<json>' --output-schema '<json>'                                # (⚠️ requires approval)
doctl gradient agent functionroute update --agent-id <agent-id> --function-id <function-id> --name new-name  # (⚠️ requires approval)
doctl gradient agent functionroute delete --agent-id <agent-id> --function-id <function-id>  # (⚠️ requires approval)
```

### Knowledge bases

Every `add-datasource` call kicks off an indexing job.

```bash
# Create — --data-sources required; also takes --database-id and --vpc_uuid (underscore) (⚠️ requires approval)
doctl gradient knowledge-base create --name example-kb --region tor1 --project-id <project-id> \
  --embedding-model-uuid <model-id> \
  --data-sources '[{"web_crawler_data_source":{"base_url":"https://example.com/","crawling_option":"DOMAIN","embed_media":true}}]'

doctl gradient knowledge-base list
doctl gradient knowledge-base get <knowledge-base-id>        # LastIndexingJob is in this output
doctl gradient knowledge-base update <knowledge-base-id> --name updated-kb --tags tag1,tag2  # (⚠️ requires approval)
doctl gradient knowledge-base delete <knowledge-base-id>     # (⚠️ requires approval)

# --- Data sources: one Spaces bucket OR one web crawler per call ---
doctl gradient knowledge-base list-datasources <knowledge-base-id>
doctl gradient knowledge-base add-datasource <knowledge-base-id> --base-url https://example.com --crawling-option DOMAIN --embed-media  # (⚠️ requires approval)
doctl gradient knowledge-base add-datasource <knowledge-base-id> --bucket-name my-bucket --item-path /docs --region tor1  # (⚠️ requires approval)
doctl gradient knowledge-base delete-datasource <knowledge-base-id> <data-source-id>  # (⚠️ requires approval)

# --- Indexing jobs. These take the JOB uuid, not the knowledge base uuid ---
doctl gradient knowledge-base list-indexing-jobs                 # account-wide, no filter flag
doctl gradient knowledge-base get-indexing-job <indexing-job-id> # Phase, Status, TotalItemsIndexed/Failed/Skipped
doctl gradient knowledge-base list-indexing-job-data-sources <indexing-job-id>
doctl gradient knowledge-base cancel-indexing-job <indexing-job-id>   # (⚠️ requires approval)

# --- Attach to an agent. Agent UUID comes FIRST, knowledge base UUID second ---
doctl gradient knowledge-base attach <agent-id> <knowledge-base-id>   # (⚠️ requires approval)
doctl gradient knowledge-base detach <agent-id> <knowledge-base-id>   # (⚠️ requires approval)
```

### Models, regions, and OpenAI keys

An "OpenAI key" is your own `sk-...` key stored on DigitalOcean so a Gradient agent can run on an OpenAI model.
A key linked to an agent cannot be deleted until the agent drops it.

```bash
doctl gradient list-models                               # --format Id,Name,isFoundational
doctl gradient list-regions --serves-inference           # or --serves-batch

doctl gradient openai-key list
doctl gradient openai-key get <openai-key-id>
doctl gradient openai-key get-agents <openai-key-id>     # which agents currently use this key
doctl gradient openai-key create --name my-key --api-key <openai-api-key>                  # (⚠️ requires approval)
doctl gradient openai-key update <openai-key-id> --name my-key --api-key <openai-api-key>  # (⚠️ requires approval)
doctl gradient openai-key delete <openai-key-id>         # (⚠️ requires approval)
```

### Scenario sets and simulation runs

A scenario set is the test cases; a simulation run plays one against an agent and produces journeys, each judged
success, failure, or inconclusive. `generate` returns in `GENERATING` status, so poll `get` first.

```bash
# --- Scenario sets. create takes --file or --scenarios, never both ---
doctl gradient scenario-set create --name support-flows --file ./scenarios.jsonl     # (⚠️ requires approval)
doctl gradient scenario-set generate --name refund-flows --num-scenarios 10 --goal-description "Refund requests"  # (⚠️ requires approval)
doctl gradient scenario-set list --statuses ready --source-kinds goal_generated --sort-by created_at
doctl gradient scenario-set get <scenario-set-id>
doctl gradient scenario-set download-url <scenario-set-id>   # presigned URL with an ExpiresAt
doctl gradient scenario-set list-scenarios <scenario-set-id> --search refund --sort-by name   # the individual scenarios inside the set
doctl gradient scenario-set update <scenario-set-id> --name support-flows-v2  # (⚠️ requires approval — --scenarios replaces the whole set)
doctl gradient scenario-set delete <scenario-set-id>         # (⚠️ requires approval)

# --- DigitalOcean's curated library, copied into a set you own ---
doctl gradient scenario-library list --category support
doctl gradient scenario-library list-scenarios <library-entry-id>
doctl gradient scenario-library create-scenario-set <library-entry-id> --name support-flows  # (⚠️ requires approval)

# --- Simulation runs ---
# (⚠️ requires approval)
doctl gradient simulation-run create --scenario-set-uuid <scenario-set-id> --agent-uuid <agent-id> \
  --name nightly-regression --max-turns 12 --exploration-budget 3 --judge-model-uuid <model-id>  # (⚠️ requires approval)
doctl gradient simulation-run list --statuses running
doctl gradient simulation-run get <run-id> -o json           # per-scenario results only show up in JSON
doctl gradient simulation-run list-journeys <run-id> --verdicts failure
doctl gradient simulation-run get-journey <run-id> <journey-id>
doctl gradient simulation-run get-trajectory <run-id> <journey-id> -o json   # transcript, tool calls, judge reasoning
doctl gradient simulation-run get-trajectory-url <run-id> <journey-id>        # presigned download URL for the same trajectory file
doctl gradient simulation-run update <run-id> --name nightly-regression-v2   # (⚠️ requires approval)
doctl gradient simulation-run cancel <run-id>                # (⚠️ requires approval)
doctl gradient simulation-run delete <run-id>                # (⚠️ requires approval)
```

### Vector databases

Weaviate clusters, sized by tier rather than node count. A Weaviate client needs the admin `UserID` and
`APIToken` from `credentials` plus the endpoints from `get`.

```bash
doctl vector-databases list
doctl vector-databases get <vector-database-id>          # HTTPEndpoint and GRPCEndpoint
doctl vector-databases credentials <vector-database-id>  # admin UserID + APIToken
doctl vector-databases backups <vector-database-id>

# Create — defaults to nyc3 and size small when the flags are omitted (⚠️ requires approval — billable)
doctl vector-databases create <name> --region nyc3 --size small --project-id <project-id> --tag production --wait

doctl vector-databases update <vector-database-id> --enable-auto-schema --weaviate-version <version> --default-quantization <setting>  # (⚠️ requires approval)
doctl vector-databases tags <vector-database-id> --tag production --tag ml   # (⚠️ requires approval — replaces every existing tag)
doctl vector-databases resize <vector-database-id> --size medium --wait      # (⚠️ requires approval)
doctl vector-databases restore <vector-database-id> <backup-id>              # (⚠️ requires approval — async, poll restore-status)
doctl vector-databases restore-status <vector-database-id> <backup-id>       # Status and Error
doctl vector-databases delete <vector-database-id>                           # (⚠️ requires approval)
```

### Dedicated inference

Your own GPU endpoints running a chosen model. Check `get-gpu-model-config` first: it maps model slugs to
compatible GPU slugs and flags gated models, which need `--hugging-face-token`.

```bash
doctl dedicated-inference get-sizes               # GPUSlug, PricePerHour, GPUVramGB, Regions
doctl dedicated-inference get-gpu-model-config    # ModelSlug, IsModelGated, compatible GPUSlugs

doctl dedicated-inference list --region nyc2 --name my-endpoint    # both filters optional
doctl dedicated-inference get <dedicated-inference-id>
doctl dedicated-inference list-accelerators <dedicated-inference-id> --slug gpu-mi300x1-192gb

# Spec-driven, JSON or YAML. Use --spec - to read from stdin (⚠️ requires approval — billable GPU)
doctl dedicated-inference create --spec spec.yaml --hugging-face-token <hf-token>
doctl dedicated-inference update <dedicated-inference-id> --spec spec.yaml   # (⚠️ requires approval)

doctl dedicated-inference list-tokens <dedicated-inference-id>     # token values are NOT returned here
doctl dedicated-inference create-token <dedicated-inference-id> --token-name my-token  # (⚠️ requires approval)
doctl dedicated-inference revoke-token <dedicated-inference-id> <token-id>   # (⚠️ requires approval)
doctl dedicated-inference delete <dedicated-inference-id>   # (⚠️ requires approval — destroys all associated resources)
```

### Serverless inference

Pay-per-token calls to hosted models at `https://inference.do-ai.run`. Every subcommand takes `--model` plus a
prompt flag, or `--request <file>` for a full JSON body (`-` reads stdin).

```bash
doctl serverless-inference models list            # only the models your key can reach

doctl serverless-inference chat-completions create --model <model-id> --message "Hello" --system-message "Be brief" --max-tokens 512 --temperature 0.2   # (⚠️ requires approval)
doctl serverless-inference chat-completions create --request ./chat-request.json --stream   # (⚠️ requires approval)
doctl serverless-inference messages create --model <model-id> --message "Hello" --max-tokens 256   # (⚠️ requires approval)
doctl serverless-inference responses create --model <model-id> --input "Hello" --instructions "Be brief"   # (⚠️ requires approval)
doctl serverless-inference embeddings create --model <model-id> --input "hello"   # (⚠️ requires approval)
doctl serverless-inference images create --model <model-id> --prompt "a green cube" --output cube.png --n 2   # (⚠️ requires approval)

# Async fal jobs: submit, get a request ID back, then poll
doctl serverless-inference async-invoke create --model fal-ai/flux/schnell --prompt "A city at sunset" --tag env=prod   # (⚠️ requires approval)
doctl serverless-inference async-invoke create --model fal-ai/elevenlabs/tts/multilingual-v2 --text "Hello world"   # (⚠️ requires approval)
doctl serverless-inference async-invoke get <request-id>   # output appears only at COMPLETED or FAILED
```

## Gotchas

**`gradient agent create` wants `--name`, even though the usage line shows a positional.** The help prints `doctl gradient agent create <agent-name>... [flags]`, but `--name` is marked `(required)` and the help's own example passes no positional at all. The same mismatch appears on `agent apikeys create`.

**`serverless-inference` authenticates against a different API than the rest of `doctl`.** Its help says `--access-token` takes either a model access key or a DigitalOcean personal access token with full access and all scopes granted. A narrowly scoped token that works everywhere else fails here, so mint a model access key rather than reusing a restricted PAT.

**Indexing job commands take the job UUID, and `list-indexing-jobs` is account-wide.** It has no knowledge base filter, so on a busy account you get every job for every knowledge base. Get the one you care about from `doctl gradient knowledge-base get <knowledge-base-id>`, which reports `LastIndexingJob`.

**`vector-databases tags` replaces the tag list, and `restore` returns before the restore is done.** Passing `--tag production` on a database already tagged `staging` leaves only `production`. Poll `doctl vector-databases restore-status <vector-database-id> <backup-id>` with both IDs until `Status` settles, and read the `Error` column when it does not.

**`dedicated-inference create` needs a spec file whose schema `--help` never shows.** The only flags are `--spec` and `--hugging-face-token`; the field list lives in the Dedicated-Inference section of the DigitalOcean API reference the help links to. Do not guess the spec keys — dump a working endpoint with `doctl dedicated-inference get <dedicated-inference-id> -o json` and edit that.
