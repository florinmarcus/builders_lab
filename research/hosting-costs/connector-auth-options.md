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
