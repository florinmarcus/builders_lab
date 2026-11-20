# Deploy: server set-up, upgrades, rollback

Everything to run the MCP server on AWS, repeatably. Decision: ADR 0008. Picture: [architecture/design/server.md](../architecture/design/server.md).

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

You need: the AWS CLI logged in to your account, region `eu-west-2` (London).

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
7. **The connector address** is `https://<Domain>/mcp/<path secret>`. Read the secret:
   ```
   aws ssm get-parameter --region eu-west-2 --with-decryption --name /builders-lab/prod/secrets/mcp_path_secret --query Parameter.Value --output text
   ```
8. **Turn on automatic deploys:** in GitHub, Settings, Secrets and variables, Actions, Variables:
   `AWS_DEPLOY_ROLE_ARN` (output DeployRoleArn), `AWS_INSTANCE_ID` (output InstanceId), `DEPLOY_ENABLED` = `true`.

## Run a command on the server

No SSH. Use Session Manager:

```
aws ssm start-session --region eu-west-2 --target <InstanceId>
sudo -i
```

Or the AWS console: EC2, the instance, Connect, Session Manager.

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

## Customer keys and the off switch

```
cd /opt/builders-lab/repo/deploy && source scripts/common.sh
dc exec -T app python -m builders_api.admin keys list
dc exec -T app python -m builders_api.admin keys extend --prefix <prefix> --expires 2027-01-31
dc exec -T app python -m builders_api.admin keys revoke --prefix <prefix>
dc exec -T app python -m builders_api.admin kill on     # stop all requests within 5 seconds
dc exec -T app python -m builders_api.admin kill off
```

## What was tested where (20 Nov 2026)

| Part | Tested |
|---|---|
| `compose.yaml`, `Caddyfile`, `db-init`, Dockerfile | Yes, locally in Docker: HTTPS, 401 without key, 404 on wrong path, tool call with key, app database user cannot drop tables |
| `upgrade.sh` first start, broken upgrade with rollback and database restore | Yes, locally |
| `cloudformation/server.yaml` | Lint only (cfn-lint). Not yet run in AWS |
| `install.sh`, `env-from-ssm.sh` | Shellcheck only. Need a real Amazon Linux server and Parameter Store |
| `ci-deploy.yml` | Not yet run |
