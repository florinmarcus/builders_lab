# 0009: One EC2 server, set up by CloudFormation and scripts, upgraded by GitHub Actions

Date: 20 Nov 2026. Status: accepted. Changes ADR 0003 (EC2, not Lightsail; London, not Frankfurt).
Changed by: 0015 (both servers on the same machine and deploy).

## Context

Florin wants a repeatable server set-up in Git, safe upgrades, and security without stored keys. ADR 0006 removed the chat model from the server, so Frankfurt (Bedrock model choice) no longer decides the region. UK data should stay in the UK.

## Decision

- **Region:** London (eu-west-2).
- **Server:** one EC2 `t4g.small` (Amazon Linux 2023, ARM; resized to `t4g.medium` on 24 Nov 2026 so the regulations corpus fits in memory, N17), not Lightsail, because Lightsail cannot take an IAM role and does not support Session Manager in the same simple way.
- **AWS side as code:** `deploy/cloudformation/server.yaml`: own network, firewall with 80 and 443 only, no SSH, IMDSv2, encrypted disk, daily snapshots (7 kept), server-down alarm with auto-recover, alert email, monthly budget alarm, GitHub OIDC deploy role.
- **On the server:** Docker Compose with Postgres, our MCP server and Caddy (automatic HTTPS). Database not exposed. App runs as non-root, read-only, no Linux capabilities, with a database user that cannot change tables.
- **Secrets:** AWS Parameter Store. Created once at random by `install.sh`, never in Git.
- **Upgrades:** `upgrade.sh <version>`: backup, build image tagged with the commit, migrate, restart, health check, automatic rollback (with database restore if a migration ran).
- **Pipeline:** GitHub Actions tests every push. On main it assumes the deploy role through OIDC and runs `upgrade.sh` through Systems Manager Run Command.
- **Images:** base images from Amazon's public mirror of Docker Hub (avoids Docker Hub pull limits).

## Options considered

- **Lightsail:** simpler and cheap, but no IAM role and no Session Manager without extra set-up.
- **Containers on ECS Fargate with RDS:** managed, but several times the monthly cost for a pilot.
- **Terraform instead of CloudFormation:** fine too; CloudFormation needs no extra tool or state file.
- **Build images in GitHub and push to ECR:** cleaner, adds a registry; building on the server is enough for one server.

## Consequences

- One server in one zone: if it dies, AWS tries to recover it; worst case, restore a snapshot. Parked.
- Backups stay in the same account and region. Parked.
- Rough cost: see `research/hosting-costs/connector-auth-options.md` (about $12 to $20 a month, to check).
