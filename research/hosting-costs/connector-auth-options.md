# Connector login: API keys in our database vs Cognito

Checked 20 Nov 2026 by web search. Prices from third-party summaries of AWS list prices; confirm on the AWS pricing page before budgeting. Guesses are marked.

## What the Claude app accepts for a custom connector

- **OAuth 2.0:** each user signs in with their own account. Claude's callback: `https://claude.ai/api/mcp/auth_callback`. Servers without dynamic client registration can be set up with a custom client ID and secret. ([Claude connector auth docs](https://www.claude.com/docs/connectors/building/authentication))
- **Fixed credential in a request header** (API key or bearer token), entered in "Request headers" when adding the connector. Only approved header names are accepted. ([Claude remote MCP guide](https://claude.com/docs/connectors/custom/remote-mcp))
- **No authentication.**
- Users report OAuth problems with some external identity providers (Microsoft Entra ID, other OIDC). Anecdotal. ([issue 212](https://github.com/anthropics/claude-ai-mcp/issues/212), [issue 402](https://github.com/anthropics/claude-ai-mcp/issues/402))

## Hooks

Hooks are a Claude Code feature, configured in Claude Code settings files ([Claude Code hooks](https://code.claude.com/docs/en/hooks)). No source found for hooks in the Claude web or desktop app. Our server traces every tool call, which covers both.

## Cost

| Option | Cost | Notes |
|---|---|---|
| API key per firm, stored in our Postgres (hashed) | About £0 extra (guess: a table on the server we already run) | We write issue, expire, revoke. One key per firm or per person. |
| Cognito user pool, Lite or Essentials | First 10,000 monthly active users free per account; Essentials about $0.015 per user after that; Lite about $0.0055 | Per-person login (OAuth). 100 builders = within free tier. |
| Cognito Plus | About $0.02 per user, no free tier | Adds threat protection. Not needed for the pilot. |
| Cognito machine-to-machine tokens | About $0.00225 per token request, plus a monthly charge per app client | Guess: a client asking for a 1-hour token all month is about 720 requests, about $1.60 per month. |

Sources: [AWS Cognito pricing](https://aws.amazon.com/cognito/pricing/), [Cognito feature plans](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-sign-in-feature-plans.html), [markaicode summary, Nov 2026](https://markaicode.com/pricing/amazon-cognito-pricing/), [The Stack on Cognito pricing](https://thestack.technology/awss-new-cognito-pricing-complicated-potentially-costly).

## Shared security and server costs (first pass, to review in detail)

Checked 20 Nov 2026 by web search. Mostly US East list prices; London (eu-west-2) can differ. "To check" means not confirmed.

| Item | Monthly (USD) | Source and notes |
|---|---|---|
| Server: Lightsail Linux, 2 GB RAM, 2 vCPU, 60 GB SSD, 3 TB transfer | about $10 | Third-party guide, us-east-1, June 2026 ([cloudburn](https://cloudburn.io/blog/amazon-lightsail-pricing)). London price to check on the [Lightsail pricing page](https://aws.amazon.com/lightsail/pricing). |
| Encryption key (KMS, customer managed) | $1 per key, plus $0.03 per 10,000 requests after 20,000 free | [AWS KMS pricing](https://aws.amazon.com/kms/pricing/). AWS-managed keys have no monthly charge. Rotation fee: sources disagree, to check. |
| Web firewall (WAF), optional | $5 per web ACL + $1 per rule group + $0.60 per million requests | [AWS WAF pricing](https://aws.amazon.com/waf/pricing). To check: WAF attaches to CloudFront, a load balancer or API Gateway, not directly to a Lightsail server. We already rate-limit in the app. |
| Logs (CloudWatch) | $0.50 per GB ingested, $0.03 per GB-month stored; 5 GB a month free | [AWS CloudWatch pricing](https://aws.amazon.com/cloudwatch/pricing/). Guess: we stay inside the free 5 GB. |
| Backups (EBS snapshots) | Billed on data stored; 1 GB free | [AWS EBS pricing](https://aws.amazon.com/ebs/pricing). Rate per GB to check. Guess: about $1. |
| Secrets (SSM Parameter Store, standard) | To check | Not found in this search. |
| HTTPS certificate (Let's Encrypt via Caddy) | $0 | |
| Login: API keys in Postgres / Cognito under 10,000 users | $0 | See above. |

**Rough total (guess):** about $20 a month with the firewall, about $12 without it. Plus the regulations corpus costs (embeddings, re-ranking) from the other session.

**Per customer (guess, at about £0.79 per $1, rate not checked):** about £1.60 each with 10 customers, £0.80 with 20, £0.30 with 50. Under the £2 target from about 8 customers.
