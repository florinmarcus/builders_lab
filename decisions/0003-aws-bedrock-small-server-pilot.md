# 0003: AWS with existing Bedrock access, one small server for the pilot

Date: 7 Nov 2026. Status: accepted for the pilot. Prices to be checked (backlog).

## Context

Cost comes first (AGENTS.md rule 3) and we must be able to run models (rule 4). Florin already has Amazon Bedrock access in an AWS account, used by `agentic-rag-lab`: Frankfurt (eu-central-1), Claude through EU inference profiles, Titan Text Embeddings V2, rerank models, Bedrock Guardrails. That lab's AWS set-up (AgentCore, RDS, NAT gateway) costs money by the hour.

## Decision

- Use the **same AWS account and Bedrock access**. Separate code: builders_lab has its own app; it reuses ideas (pgvector, rerank, citations), not code.
- **Region: Frankfurt for now**, as in agentic-rag-lab. Mock data only, so EU is fine. Re-check London (eu-west-2) model availability before any real council data (UK hosting).
- **One small server** (EC2 or Lightsail) running the web app and Postgres with pgvector in Docker, calling Bedrock through an IAM role. No NAT gateway, RDS or AgentCore for the pilot.
- **Access:** HTTPS always (e.g. Caddy with an automatic certificate) and a simple username and password login for Florin and Builder 1. Optionally limit by IP. Cognito later if more users join.

## Options considered

- Reuse agentic-rag-lab's AgentCore + RDS set-up: works, but hourly costs for a pilot with two users.
- Azure AI Foundry or Google Vertex: no existing access; would add set-up for no gain now.
- Run only locally: free, but Florin and Builder 1 can't reach it remotely.

## Consequences

- Monthly cost is mostly the server plus Bedrock calls per question. Both to be priced and dated in `research/hosting-costs/` and `research/models/`.
- Rerank may be left out at first if London is needed later (no rerank model there as of 14 Oct 2026, per agentic-rag-lab ADR 0012).
