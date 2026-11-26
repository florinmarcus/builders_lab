# Deploy: server set-up, upgrades, rollback

Everything to run the MCP server on AWS, repeatably. Decision: ADR 0009. Picture: [runtime design](../architecture/design/runtime/design.md#6-deployment).

| File | What it does |
|---|---|
| `cloudformation/server.yaml` | Creates the AWS side: network, server, firewall, roles, snapshots, alerts, budget, GitHub deploy role |
| `scripts/install.sh` | First-time set-up of the server (runs by itself at first boot). Safe to run again |
| `scripts/upgrade.sh` | Move to a version: backup, build, migrate, restart, health check, automatic rollback |
| `scripts/rollback.sh` | Go back to the previous version |
| `scripts/backup.sh` | Database dump (also runs daily at 02:30 UTC; newest 14 kept) |
| `scripts/env-from-ssm.sh` | Writes the server's settings file from AWS Parameter Store; creates secrets once |
| `compose.yaml`, `Caddyfile`, `db-init/` | The running stack: Postgres, MCP server, Caddy (HTTPS) |
| `../.github/workflows/ci-deploy.yml` | Tests every push; deploys main after tests pass |

## First install (once)

You need: the AWS CLI logged in to your account, region `eu-west-2` (London), with the permissions in
`iam/deployer-policy.json` (scoped to `builders-lab-*` resources in London). An admin attaches it once:

```
aws iam put-user-policy --user-name <deploy user> --policy-name builders-lab-deployer \
  --policy-document file://deploy/iam/deployer-policy.json
```

For the regulations corpus (embeddings and re-rank, ADR 0013), attach a second, managed policy. It is separate
because a user's inline policies may total only 2,048 bytes:

```
aws iam create-policy --policy-name builders-lab-corpus-bedrock \
  --policy-document file://deploy/iam/corpus-bedrock-policy.json
aws iam attach-user-policy --user-name <deploy user> \
  --policy-arn arn:aws:iam::<account id>:policy/builders-lab-corpus-bedrock
```

1. **If the GitHub repo is private:** create a fine-grained GitHub token with read access to this repo only, then:
   ```
   aws ssm put-parameter --region eu-west-2 --type SecureString \
     --name /builders-lab/prod/secrets/github_token --value <token>
   ```
2. **Create the stack** (about 5 minutes; the server then installs itself in about 5 more):
   ```
   aws cloudformation deploy --region eu-west-2 --stack-name builders-lab-prod \
     --template-file deploy/cloudformation/server.yaml --capabilities CAPABILITY_IAM \
     --parameter-overrides AlertEmail=<your email>
   ```
   Add `CreateGitHubOidcProvider=false` if your account already has the GitHub OIDC provider.
   Add `DomainName=<your domain>` if you have one (point its DNS A record at the PublicIp output). Otherwise you get `<ip>.sslip.io`.
3. **Confirm the alert email** AWS sends you.
4. **See the outputs:**
   ```
   aws cloudformation describe-stacks --region eu-west-2 --stack-name builders-lab-prod --query "Stacks[0].Outputs"
   ```
5. **Check it is up:** `https://<Domain>/healthz` should say ok.
6. **Load the demo data and make a key** (see "Run a command on the server"):
   ```
   cd /opt/builders-lab/repo/deploy && source scripts/common.sh
   dc exec -T app python -m builders_api.db.seed
   dc exec -T app python -m builders_api.admin keys create --firm oakline --label "Florin, Claude app" --expires 2026-12-31
   ```
7. **The connector addresses** (ADR 0015) are `https://<Domain>/mcp/<path secret>` (firm data) and
   `https://<Domain>/mcp/<path secret>/regulations` (regulations library). The same key works on both. Read the secret:
   ```
   aws ssm get-parameter --region eu-west-2 --with-decryption --name /builders-lab/prod/secrets/mcp_path_secret --query Parameter.Value --output text
   ```
8. **Turn on automatic deploys:** in GitHub, Settings, Secrets and variables, Actions, Variables:
   `AWS_DEPLOY_ROLE_ARN` (output DeployRoleArn), `AWS_INSTANCE_ID` (output InstanceId), `DEPLOY_ENABLED` = `true`.

## Current production (20 Nov 2026)

- Stack `builders-lab-prod`, server `i-0f7814c27302e471f` (t4g.medium since 24 Nov 2026: stack parameter InstanceType), address `https://16-60-88-218.sslip.io`.
- Florin's API key (expires 31 Dec 2026) is in Parameter Store, not in chat or Git:
  ```
  aws ssm get-parameter --region eu-west-2 --with-decryption --name /builders-lab/prod/handover/florin_api_key --query Parameter.Value --output text
  ```

## Logs and security alerts (20 Nov 2026)

- **Logs survive deploys.** The app and Caddy log to CloudWatch (`compose.aws.yaml`, added by `scripts/common.sh` on the server): log groups `/builders-lab/prod/app` and `/builders-lab/prod/caddy`, kept 90 days. `docker logs` still works on the server. Before this, each deploy wiped the log.
- **No secrets in logs.** The MCP path secret is masked as `<path-secret>` (app: `builders_api/mcp_server/logredact.py`; Caddy: `Caddyfile` log filter). Key headers are dropped from Caddy logs.
- **Alarms (email via the alert topic):** 10+ rejected keys in 5 minutes; any IP block; any lockdown or security alert; 100+ wrong-path requests in 5 minutes (scanner); 5+ server errors in 5 minutes. Metric namespace `BuildersLab/Security`.
- Read logs: CloudWatch console, Logs, the log group; or `aws logs tail /builders-lab/prod/app --since 1h --region eu-west-2` (in Git Bash put `MSYS_NO_PATHCONV=1` in front).

## Stack updates: server protected (20 Nov 2026)

- The server image is pinned (`ImageId` parameter). It used to resolve "latest Amazon Linux" at every stack update, so any update after Amazon published a new image would have **replaced the server and its database**.
- A stack policy (`cloudformation/stack-policy.json`, set on the stack) denies replacing or deleting `Server` and `Ip`. An update that would do that fails and rolls back. Set it again after recreating the stack: `aws cloudformation set-stack-policy --stack-name builders-lab-prod --stack-policy-body file://deploy/cloudformation/stack-policy.json --region eu-west-2`.
- Always preview a stack update as a change set and check that nothing says Replacement: True. Take a backup first (`scripts/backup.sh <label>`).
- To upgrade the OS on purpose: back up, lift the stack policy for `Server`, set a new `ImageId`, restore data if needed.

## Run a command on the server

No SSH. Use Session Manager:

```
aws ssm start-session --region eu-west-2 --target <InstanceId>
sudo -i
```

Or the AWS console: EC2, the instance, Connect, Session Manager.

## Regulations corpus (24 Nov 2026)

The corpus lives in its own container, `corpus-db` (pgvector, own volume `corpusdata`, no ports), next to the firm
database. Set-up runs once when the volume is created: `corpus-db-init/01-corpus.sh` makes the owner and the
read-only reader (5 connections, 5-second queries), the same as `rds/corpus-setup.sql`. Passwords are created in
Parameter Store by `env-from-ssm.sh` (`secrets/corpus_owner_password`, `corpus_reader_password`,
`corpus_super_password`). The app uses the reader; an outside URL in `secrets/corpus_reader_url` wins, so delete
that parameter to stop using Frankfurt.

Load a new index: build it where the chunks and vectors are (`python -m system.rag.load` into any Postgres with
pgvector), dump the schema, copy the file to the server, restore it as the owner:

```
pg_dump -n corpus -Fc -f corpus.dump <local corpus database>
cd /opt/builders-lab/repo/deploy && source scripts/common.sh
dc exec -T corpus-db pg_restore -U builders_corpus_owner -d builders_corpus --clean --if-exists --single-transaction < corpus.dump
```

The restore is one transaction: searches see the old index until it commits. Then set `rag_enabled` to `on` in
Parameter Store and run `upgrade.sh`.

## Upgrade

- **Normal:** push to main. GitHub runs the tests, then `upgrade.sh <commit>` on the server.
- **By hand:** `sudo /opt/builders-lab/repo/deploy/scripts/upgrade.sh <commit, tag or branch>`

If the new version is not healthy after about a minute, `upgrade.sh` restores the database from the backup it just took (only if a migration ran), goes back to the previous version and fails loudly.

## Roll back

- **Code only:** `sudo /opt/builders-lab/repo/deploy/scripts/rollback.sh`
- **Database too:** pick a file in `/opt/builders-lab/backups/`, then:
  ```
  cd /opt/builders-lab/repo/deploy && source scripts/common.sh
  dc stop app
  dc exec -T db pg_restore -U builders_owner -d builders --clean --if-exists < /opt/builders-lab/backups/<file>.dump
  dc start app
  ```
- **Whole disk:** restore a daily EBS snapshot (kept 7 days) from the EC2 console.

## Demo mail feed

The server reads new email from its demo mail folder (`MAIL_SOURCE=eml:/data/mail`) until it has a Gmail login.

```
cd /opt/builders-lab/repo/deploy && source scripts/common.sh
dc exec -T app python -m builders_api.admin feed history        # past emails (done 20 Nov 2026)
dc exec -T app python -m builders_api.admin feed today          # demo morning: the new emails arrive
```

Then in Claude: "check my emails" (sync_inbox, then save_facts per email).
After a tool is added or changed, reconnect the connector in the Claude app so it sees the new tool list.

## Demo reset (one command)

```
sudo /opt/builders-lab/repo/deploy/scripts/demo-reset.sh              # clean start + today's emails
sudo /opt/builders-lab/repo/deploy/scripts/demo-reset.sh --no-today   # clean start only
sudo /opt/builders-lab/repo/deploy/scripts/demo-reset.sh --save-baseline
```

Restores `/opt/builders-lab/demo-baseline.dump` (past emails ingested, facts saved), keeps current API keys and the
kill switch, re-applies newer migrations, empties the mail folder and feeds the demo-day emails. A backup is taken first.

## Customer keys and the off switch

```
cd /opt/builders-lab/repo/deploy && source scripts/common.sh
dc exec -T app python -m builders_api.admin keys list
dc exec -T app python -m builders_api.admin keys extend --prefix <prefix> --expires 2027-01-31
dc exec -T app python -m builders_api.admin keys revoke --prefix <prefix>
dc exec -T app python -m builders_api.admin kill on     # stop all requests within 5 seconds
dc exec -T app python -m builders_api.admin kill off
```

## Eval key (26 Nov 2026, S161)

Answer evals call the live regulations server many times (a full run is about 500 searches). They use their own
firm, `evals` (migration 0004: no firm data, 5,000 tool calls a day), so they never use up the demo firm's 500.
Make the key once, after the deploy that carries migration 0004:

```
cd /opt/builders-lab/repo/deploy && source scripts/common.sh
dc exec -T app python -m builders_api.admin keys create --firm evals --label "Evals" --expires 2027-01-31
```

Save it in Parameter Store as `/builders-lab/prod/handover/evals_api_key` (SecureString), never in chat or Git. In
claude.ai, add a second connector with this key for the regulations address (for example "Builders Regulations
Evals"); answer helpers use only that connector. `demo-reset.sh` keeps the key: it now runs migrations before it
restores the keys.

## What was tested where (20 Nov 2026)

| Part | Tested |
|---|---|
| `compose.yaml`, `Caddyfile`, `db-init`, Dockerfile | Yes, locally in Docker: HTTPS, 401 without key, 404 on wrong path, tool call with key, app database user cannot drop tables |
| `upgrade.sh` first start, broken upgrade with rollback and database restore | Yes, locally |
| `cloudformation/server.yaml` | Yes, in AWS (third attempt; two permission fixes) |
| `install.sh`, `env-from-ssm.sh` | Yes, on the real server (one bug fixed: log lines mixed into secrets) |
| `ci-deploy.yml` | Test job yes; deploy job switched on 20 Nov 2026 (repository variables set) |
