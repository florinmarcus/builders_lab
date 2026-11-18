# Running costs of a small pilot on Amazon Bedrock and one small AWS server (checked 18 Nov 2026)

All prices checked on **18 Nov 2026**. All AWS and Anthropic prices are in **USD**. No source gave GBP prices (see Gaps). "Price List API" means the public AWS offer files (JSON/CSV) at `pricing.us-east-1.amazonaws.com`. Their own publication dates are given next to each figure.

Source shorthand used below:
- [AWS-FM-FRA] = https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/current/eu-central-1/index.json (publicationDate 2026-11-09)
- [AWS-FM-LON] = https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/current/eu-west-2/index.json (publicationDate 2026-11-09)
- [AWS-BR-FRA] = https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/eu-central-1/index.json (publicationDate 2026-11-11)
- [AWS-BR-LON] = https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/eu-west-2/index.json (publicationDate 2026-11-11)
- [ANT-PRICING] = https://platform.claude.com/docs/en/about-claude/pricing
- [ANT-BEDROCK] = https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock
- [ANT-RESIDENCY] = https://platform.claude.com/docs/en/manage-claude/data-residency
- [ANT-CPAWS] = https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws

## 1. Bedrock on-demand prices for Claude (Frankfurt and London), and how they compare to Anthropic list prices

### Takeaway
On Bedrock, the **global** endpoint price for Haiku 5.5, Sonnet 5.5 and Opus 5.5 is exactly the Anthropic list price. The **regional / EU geo** price (the one that keeps data in the EU) is **10% higher**. Frankfurt and London have identical Claude prices. The Anthropic list prices given in the brief ($0.10/$0.50, $2/$10, $4/$20) are confirmed.

### Cited Findings

**Anthropic first-party list prices (per 1M tokens), confirmed** — [ANT-PRICING](https://platform.claude.com/docs/en/about-claude/pricing)

| Model | Input | 5m cache write | 1h cache write | Cache read | Output |
|---|---|---|---|---|---|
| Haiku 5.5 (prompts up to 100K tokens) | $0.10 | $0.125 | $0.20 | $0.01 | $0.50 |
| Haiku 5.5 (prompts over 100K tokens) | $0.50 | $0.625 | $1.00 | $0.05 | $2.50 |
| Sonnet 5.5 | $2.00 | $2.50 | $4.00 | $0.10 | $10.00 |
| Opus 5.5 | $4.00 | $5.00 | $8.00 | $0.20 | $20.00 |
| Haiku 4.5 (previous) | $1.00 | $1.25 | $2.00 | $0.10 | $5.00 |
| Sonnet 4.6 (previous) | $3.00 | $3.75 | $6.00 | $0.30 | $15.00 |

- On Sonnet 5.5 and Opus 5.5, cache hits are 0.05x base input. Other models use 0.1x. — [ANT-PRICING](https://platform.claude.com/docs/en/about-claude/pricing)
- First-party Batch API: 50% off input and output. Batch: Haiku 5.5 $0.05/$0.25, Sonnet 5.5 $1/$5, Opus 5.5 $2/$10. — [ANT-PRICING](https://platform.claude.com/docs/en/about-claude/pricing)
- Claude 4.7 and later use a newer tokenizer that "produces approximately 30% more tokens for the same text". — [ANT-PRICING](https://platform.claude.com/docs/en/about-claude/pricing)

**Bedrock, Claude 5.5 models, on-demand, per 1M tokens.** Frankfurt (eu-central-1) and London (eu-west-2) show the same numbers. — [AWS-FM-FRA](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/current/eu-central-1/index.json); [AWS-FM-LON](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/current/eu-west-2/index.json)

| Model | Endpoint | Input | Cache write 5m | Cache write 1h | Cache read | Output |
|---|---|---|---|---|---|---|
| Haiku 5.5 | Global | $0.10 | $0.125 | $0.20 | $0.01 | $0.50 |
| Haiku 5.5 | Regional/geo ("Standard") | $0.11 | $0.1375 | $0.22 | $0.011 | $0.55 |
| Haiku 5.5 long context | Global | $0.50 | $0.625 | $1.00 | $0.05 | $2.50 |
| Haiku 5.5 long context | Regional/geo | $0.55 | $0.6875 | $1.10 | $0.055 | $2.75 |
| Sonnet 5.5 | Global | $2.00 | $2.50 | $4.00 | $0.10 | $10.00 |
| Sonnet 5.5 | Regional/geo | $2.20 | $2.75 | $4.40 | $0.11 | $11.00 |
| Opus 5.5 | Global | $4.00 | $5.00 | $8.00 | $0.20 | $20.00 |
| Opus 5.5 | Regional/geo | $4.40 | $5.50 | $8.80 | $0.22 | $22.00 |

- The Price List labels the global rows "Standard, Global" and the other rows just "Standard". For older models the non-global rows are labelled "Regional" (Haiku 4.5) or "Regional CRIS" (Sonnet 4.6). — [AWS-FM-LON](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/current/eu-west-2/index.json)
- Previous models on Bedrock (Frankfurt = London): Haiku 4.5 global $1.00 in / $5.00 out, regional $1.10 / $5.50. Batch global $0.50 / $2.50, batch regional $0.55 / $2.75. Sonnet 4.6 global $3.00 / $15.00, regional CRIS $3.30 / $16.50. Batch global $1.50 / $7.50. — [AWS-FM-FRA](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/current/eu-central-1/index.json)
- Anthropic says: "Regional and multi-region endpoints include a 10 percent premium over global endpoints." On Bedrock, global endpoints have no premium. Regional endpoints and geo inference profiles (US, EU, JP, AU) carry the 10% premium. — [ANT-PRICING](https://platform.claude.com/docs/en/about-claude/pricing); [ANT-BEDROCK](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock)
- **Batch on Bedrock for the 5.5 models:** the Frankfurt and London Price List files have **no batch rows** for Haiku 5.5, Sonnet 5.5 or Opus 5.5. Older models (Haiku 4.5, Sonnet 4.6) do have batch rows at 50% off. — [AWS-FM-FRA](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/current/eu-central-1/index.json)
- On the bedrock-mantle (Messages API) endpoint, "Message Batches" is listed under "Features not supported". — [ANT-BEDROCK](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock)
- Prompt caching is supported on Claude in Amazon Bedrock. — [ANT-BEDROCK](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock)

### Inferences
- Bedrock global = Anthropic list price. Bedrock EU geo = list price x 1.1. If council-email data has to stay in the EU, budget the 1.1x price.
- London and Frankfurt cost the same for Claude, so the choice can depend on the server and the embeddings price (see section 3).
- For the one-off ingestion, a 50% batch discount does not seem to be available on Bedrock for the 5.5 models right now. With Haiku 5.5 the ingestion cost is small anyway.

### Gaps
- I did not render the HTML tables on aws.amazon.com/bedrock/pricing. Figures come from the AWS Price List API files, which feed that page.
- I could not confirm whether batch inference for the 5.5 models exists on the bedrock-runtime endpoint with prices not yet in the Price List.
- "Standard" (non-global) for the 5.5 models: the Price List does not say whether it means in-region, EU geo, or both. The Anthropic page says both carry the same 10% premium.

## 2. Which current Claude models run in London (eu-west-2) vs Frankfurt (eu-central-1)

### Takeaway
Both London and Frankfurt offer the **Global** endpoint and the **EU geo** inference profile. Neither offers "in-region only" routing; in Europe that is only Stockholm and Ireland. The 5.5 models are priced in both regions.

### Cited Findings
- Region table (Claude in Amazon Bedrock, bedrock-mantle): `eu-central-1` Frankfurt = "Global, EU". `eu-west-2` London = "Global, EU". `eu-north-1` Stockholm and `eu-west-1` Ireland = "Global, EU, In-region only". — [ANT-BEDROCK](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock)
- "The global endpoint is available for Claude Fable 5.1, Claude Fable 5, Claude Opus 5.5, Claude Opus 5, Claude Opus 4.8, Claude Opus 4.7, Claude Sonnet 5.5, Claude Sonnet 5, Claude Haiku 5.5, and Claude Haiku 4.5." — [ANT-BEDROCK](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock)
- "Regional: ... To route across multiple regions within a geography, use an inference profile (US, EU, JP, or AU)." — [ANT-BEDROCK](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock)
- Bedrock model IDs: `anthropic.claude-haiku-5-5`, `anthropic.claude-sonnet-5-5`, `anthropic.claude-opus-5-5`. Access for these three is "See Access" (check model access in the console). Haiku 4.5 and Sonnet 5 are "Open". — [ANT-BEDROCK](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock)
- Both the Frankfurt and London Price List files contain Global and "Standard" (non-global) on-demand rows for Haiku 5.5, Sonnet 5.5 and Opus 5.5. — [AWS-FM-FRA](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/current/eu-central-1/index.json); [AWS-FM-LON](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/current/eu-west-2/index.json)
- Default quota: 2M input tokens per minute, raisable to 5M input / 500K output TPM without Anthropic approval. — [ANT-BEDROCK](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock)

### Inferences
- An EU inference profile called from London may run inference in any EU-geo region (for example Frankfurt or Paris), not only in the UK. No option in the sources keeps Claude inference **inside the UK only**.

### Gaps
- I did not fetch the AWS-side page "Supported foundation models by region" (docs.aws.amazon.com/bedrock/latest/userguide/models-regions.html). Model-by-region detail is taken from Anthropic's Bedrock page and the AWS Price List.
- I found no source that lists which EU regions sit inside the "EU" inference profile.

## 3. Embeddings, rerank and guardrails prices on Bedrock

### Takeaway
Titan Text Embeddings V2 costs **$0.0001 per 1K tokens in London** but **$0.0002 in Frankfurt**. Amazon Rerank 1.0 ($1 per 1,000 search units) and Cohere Rerank 3.5 ($2 per 1,000 search units) show up in the **Frankfurt** price file only, not London. Guardrails content filters cost about $0.15 per 1,000 text units.

### Cited Findings
- Titan Text Embeddings V2, on-demand: Frankfurt $0.0002 per 1K input tokens, batch $0.0001 per 1K. — [AWS-BR-FRA](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/eu-central-1/index.json)
- Titan Text Embeddings V2, on-demand: London $0.0001 per 1K input tokens, batch $0.00005 per 1K. — [AWS-BR-LON](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/eu-west-2/index.json)
- Amazon Rerank v1: Frankfurt "$1 per 1000 search units" (`EUC1-AmazonRerank-v1-searchunits`). No Amazon Rerank row in the London file. — [AWS-BR-FRA](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/eu-central-1/index.json); [AWS-BR-LON](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/eu-west-2/index.json)
- Cohere Rerank 3.5: Frankfurt $0.002 "per 1 search unit" (= $2 per 1,000). No Cohere Rerank 3.5 row in the London file. — [AWS-FM-FRA](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/current/eu-central-1/index.json); [AWS-FM-LON](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/current/eu-west-2/index.json)
- Bedrock Guardrails, Frankfurt and London (same prices): content policy $0.15 per 1K text units; denied topics $0.15 per 1K; contextual grounding $0.10 per 1K; sensitive information (PII) filter paid tier $0.10 per 1K; word filters $0; content filter on images $0.75 per 1K images (Frankfurt); automated reasoning $0.17 per 1K (Frankfurt). — [AWS-BR-FRA](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/eu-central-1/index.json); [AWS-BR-LON](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/eu-west-2/index.json)
- London also lists per-unit "GuardrailChecks" rows: prompt attack check $0.00008 per text unit, content filter check $0.00007 per text unit, sensitive information check $0.0001 per text unit. — [AWS-BR-LON](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/eu-west-2/index.json)

### Inferences
- For a pilot this size, embeddings cost is close to zero in either region.
- If the pilot uses Bedrock rerank, Frankfurt is the only region of the two with a priced rerank model. A London server could still call the Frankfurt rerank endpoint, but the data would then leave the UK.

### Gaps
- I did not verify the exact definitions of a "search unit" (rerank) or a "text unit" (Guardrails, usually quoted as 1,000 characters). The worked estimate below marks these as assumptions.
- The London "GuardrailChecks" rows look like a newer pricing model next to the older per-1K rows. I could not confirm which one applies to new guardrails.

## 4. Alternatives: Claude Platform on AWS, and the direct Anthropic API with UK/EU data residency

### Takeaway
**Claude Platform on AWS** is run by Anthropic and billed through AWS Marketplace at Anthropic's standard per-token rates. The AWS region you pick does **not** decide where inference runs. **Neither Claude Platform on AWS nor the direct Anthropic API offers EU or UK inference today**: `inference_geo` takes only `"global"` (standard price) or `"us"` (1.1x), and workspace geo is US only. **For EU-only inference, Bedrock (EU profile) is the only option of the three.**

### Cited Findings
- Claude Platform on AWS: "Anthropic operates the infrastructure and runs model inference. AWS handles authentication (SigV4 or API key), IAM access control, and billing through AWS Marketplace. This differs from Amazon Bedrock, where AWS operates the inference stack." — [ANT-CPAWS](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)
- Regions: "All AWS commercial regions are supported." The page does not list them one by one. — [ANT-CPAWS](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)
- "The AWS region of your workspace controls which endpoint you call and where AWS-side resources (IAM, CloudTrail, billing) are scoped. It does not determine where inference runs." — [ANT-CPAWS](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)
- "For workspaces created before September 18, 2026 (00:00 UTC), Anthropic might process requests, store data, and run inference outside AWS." — [ANT-CPAWS](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)
- Billing: AWS Marketplace in Claude Consumption Units (CCUs). "Anthropic rates your token usage in USD at standard per-model, per-feature rates, applies any negotiated discount, converts the result to CCUs at $0.01 USD per CCU". — [ANT-PRICING](https://platform.claude.com/docs/en/about-claude/pricing)
- Data residency: "Inference geo: Only "us" and "global" are available." "Workspace geo: Only "us" is currently available." US-only inference costs 1.1x on Claude 4.6 and later. Global costs the standard price. This applies to the Claude API, Claude Platform on AWS, and Claude Models on Google Cloud (Anthropic managed). — [ANT-RESIDENCY](https://platform.claude.com/docs/en/manage-claude/data-residency)
- On Bedrock, "the inference region is determined by the endpoint URL or inference profile, so inference_geo is not applicable." — [ANT-RESIDENCY](https://platform.claude.com/docs/en/manage-claude/data-residency)
- Claude Platform on AWS has the full Anthropic API (for example the Batch API, Files API, server tools). Bedrock-mantle lacks Message Batches, the Files API, server-side tools and Managed Agents. — [ANT-CPAWS](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws); [ANT-BEDROCK](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock)

### Inferences
- Price for global inference: the direct API, Claude Platform on AWS and Bedrock global all cost the same per token. The 50% Batch API discount is available on the direct API and (by API parity) on Claude Platform on AWS, but not on Bedrock-mantle.
- If the council data must stay in the EU, Bedrock's EU profile at 1.1x is the only one of these options that does it. If global routing is acceptable, the direct API or Claude Platform on AWS gives the same token price plus batch.

### Gaps
- I found no Anthropic news post giving a launch date for Claude Platform on AWS. Its SDK client is labelled beta.
- No source gave a UK-only inference option on any of the three routes.

## 5. Small server prices (EC2, EBS, IPv4, data transfer, Lightsail, free tier)

### Takeaway
A t4g.small costs about $14 a month and a t4g.medium about $27–28 a month in London or Frankfurt, before disk and IPv4. A Lightsail 4 GB bundle is a flat **$24 a month** in both regions, with SSD, a public IPv4 address and 4 TB transfer included. That makes it the simplest cheap option.

### Cited Findings
- EC2 Linux on-demand, per hour (publication 2026-11-17). London: t4g.micro $0.0094, t4g.small $0.0188 (2 vCPU, 2 GiB), t4g.medium $0.0376 (2 vCPU, 4 GiB), t3.small $0.0236. Frankfurt: t4g.micro $0.0096, t4g.small $0.0192, t4g.medium $0.0384, t3.small $0.0240. — [AWS EC2 price JSON, London](https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/EU%20(London)/Linux/index.json); [Frankfurt](https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/EU%20(Frankfurt)/Linux/index.json)
- EBS gp3 (effective 2026-11-01): London $0.0928 per GB-month, Frankfurt $0.0952 per GB-month. Snapshots: London $0.053, Frankfurt $0.054 per GB-month. — [AWS Price List AmazonEC2 eu-west-2 CSV](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/eu-west-2/index.csv); [eu-central-1 CSV](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/eu-central-1/index.csv)
- gp3 includes "a free baseline performance of 3,000 provisioned IOPS" and 125 MB/s. — [AWS EBS pricing](https://aws.amazon.com/ebs/pricing/)
- Public IPv4 (including Elastic IP): $0.005 per hour, in use or idle. Billed per second, 60-second minimum. — [AWS VPC pricing](https://aws.amazon.com/vpc/pricing/)
- Data transfer out to the internet: first 100 GB per month free, "aggregated globally". Then $0.09 per GB for the first 10 TB (London, effective 2026-11-01). — [AWS Price List AWSDataTransfer eu-west-2](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSDataTransfer/current/eu-west-2/index.csv); [AWS EC2 on-demand pricing](https://aws.amazon.com/ec2/pricing/on-demand/)
- Lightsail Linux bundles with public IPv4, per month: $5 (0.5 GB RAM, 2 vCPU, 20 GB SSD, 1 TB), $7 (1 GB, 40 GB, 2 TB), $12 (2 GB, 60 GB, 3 TB), $24 (4 GB, 2 vCPU, 80 GB, 4 TB), $44 (8 GB, 160 GB, 5 TB). IPv6-only bundles are cheaper ($3.50 to $40). — [AWS Lightsail pricing](https://aws.amazon.com/lightsail/pricing/)
- The Lightsail Price List gives the same hourly rates for Frankfurt and London (for example the 4 GB bundle at $0.03225 per hour; 2 GB at $0.01612 per hour). Frankfurt and London are not among the regions with halved transfer allowances. — [AWS Lightsail price JSON](https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/lightsail/USD/current/lightsail.json) (publication 2026-11-13); [AWS Lightsail pricing](https://aws.amazon.com/lightsail/pricing/)
- Lightsail managed Postgres: from $15 a month (1 GB, no encryption on that plan) or $30 (2 GB). — [AWS Lightsail pricing](https://aws.amazon.com/lightsail/pricing/)
- Free tier for new accounts: "$100 in credits immediately", up to $200 over 6 months. A Free-plan account closes after 6 months or when the credits run out. EC2 and Bedrock are "Available on both plans". Free-plan accounts are not eligible for promotional credits. — [AWS Free Tier](https://aws.amazon.com/free/)

### Inferences
- EC2 t4g.small in London, per month (730 hours): $0.0188 x 730 = **$13.72**. Add 30 GB gp3 (30 x $0.0928 = $2.78) and one public IPv4 ($0.005 x 730 = $3.65). Total **≈ $20.15/month**.
- EC2 t4g.medium in London: $0.0376 x 730 = $27.45, + $2.78 + $3.65 = **≈ $33.88/month**. In Frankfurt: $28.03 + $2.86 + $3.65 = **≈ $34.54/month**.
- Lightsail 4 GB ($24) is cheaper than a t4g.medium with disk and IPv4 (≈ $34). It is also simpler (fixed price, transfer included). For Postgres + pgvector + a small web app, 2 GB ($12) may be tight; 4 GB is the safer pick. That sizing is my judgement, not a sourced fact.
- Data transfer for two users will stay far under the free 100 GB per month.
- The $100–$200 credits would cover the pilot server for several months. Whether credits can pay for Anthropic models on Bedrock is not confirmed (see Gaps).

### Gaps
- No GBP prices: AWS lists all of these in USD. I did not verify an exchange rate, so I give no GBP conversion.
- Not confirmed whether AWS Free Tier credits apply to Claude models on Bedrock (they are billed as AWS Marketplace items, per the Price List service names "Claude ... (Amazon Bedrock Edition)").
- The 1 GB Lightsail bundle could run a tiny pilot, but I have not checked memory needs.

## 6. Worked estimate (ESTIMATE, not a quote)

### Takeaway
At 500 questions a month, the model cost is small. About **$0.72/month on Haiku 5.5** and **$14.30/month on Sonnet 5.5** (Bedrock EU geo, London). The server is the biggest line: **$24/month** Lightsail 4 GB, or about $20–34 on EC2. One-off ingestion is about **$1–3 with Haiku 5.5** or **$26–59 with Sonnet 5.5**. Estimated monthly total: **≈ $25 (Haiku) to ≈ $39 (Sonnet)**, plus the one-off ingestion.

### Cited Findings (inputs)
- Model prices: section 1 tables — [AWS-FM-LON](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/current/eu-west-2/index.json)
- Titan V2 London $0.0001 per 1K tokens — [AWS-BR-LON](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/eu-west-2/index.json)
- Server prices: section 5 sources.

### Inferences (the arithmetic)

**Assumptions (mine, not sourced):**
- 50 flats x 15 documents x 10 pages = **7,500 pages** ingested once.
- Low case: **1,000 tokens per page** of extracted text = 7.5M tokens. High case: **3,000 tokens per page**, if PDFs go to Claude as PDFs (text + page image) = 22.5M tokens. The tokens-per-page figures are assumptions; I did not verify them against Anthropic's PDF docs. The newer tokenizer gives about 30% more tokens per text ([ANT-PRICING](https://platform.claude.com/docs/en/about-claude/pricing)).
- Each of the 750 documents gets one Claude extraction call: about 1,000 prompt tokens of instructions (+0.75M input in total) and about 1,000 output tokens (0.75M output in total).
- Questions: 500 per month x 10,000 input tokens = **5M input**. 500 x 600 output tokens = **0.3M output**. Thinking tokens are billed as output. Haiku 5.5 and Sonnet 5.5 think adaptively by default, so real output could be higher.
- Prices: Bedrock **EU geo (1.1x)**, London. Global prices are shown for comparison and equal the Anthropic list price.
- The Haiku 5.5 prompt stays under 100K tokens, so standard (not long-context) rates apply.

**A. One-off ingestion: Claude extraction**

| Case | Model | Input tokens | Output tokens | Global (= Anthropic list) | EU geo (1.1x) |
|---|---|---|---|---|---|
| Low (1,000 tok/page) | Haiku 5.5 | 8.25M x $0.10 = $0.825 | 0.75M x $0.50 = $0.375 | **$1.20** | **$1.32** |
| Low | Sonnet 5.5 | 8.25M x $2 = $16.50 | 0.75M x $10 = $7.50 | **$24.00** | **$26.40** |
| High (3,000 tok/page) | Haiku 5.5 | 23.25M x $0.10 = $2.325 | $0.375 | **$2.70** | **$2.97** |
| High | Sonnet 5.5 | 23.25M x $2 = $46.50 | $7.50 | **$54.00** | **$59.40** |

**B. One-off ingestion: embeddings (Titan V2)**
- 7.5M tokens x $0.0001/1K (London) = **$0.75**. In Frankfurt ($0.0002/1K): **$1.50**. More chunk overlap would add a little.

**C. Monthly questions**

| Model | Input | Output | Global / month | EU geo / month |
|---|---|---|---|---|
| Haiku 5.5 | 5M x $0.10 = $0.50 | 0.3M x $0.50 = $0.15 | **$0.65** | **$0.72** |
| Sonnet 5.5 | 5M x $2 = $10.00 | 0.3M x $10 = $3.00 | **$13.00** | **$14.30** |
| Opus 5.5 (reference) | 5M x $4 = $20.00 | 0.3M x $20 = $6.00 | $26.00 | $28.60 |

- Query embeddings: 500 x ~50 tokens = 25K tokens, which is a fraction of a cent.
- Optional prompt caching: if, say, 2,000 tokens of system prompt per question were cached on Sonnet 5.5 EU, cache reads at $0.11/M instead of $2.20/M would save about 1M x ($2.20 − $0.11) ≈ $2/month. This ignores cache writes. It only works while the cache stays warm (5 minutes by default), which with ~17 questions a day it often will not.
- Optional rerank (Frankfurt only): if 1 search unit per question, Amazon Rerank 500 x $0.001 = $0.50/month; Cohere Rerank 3.5 500 x $0.002 = $1.00/month. The search-unit definition is not verified.
- Optional Guardrails content filter on the user question only (≈ 1 text unit each): 500 x $0.15/1K ≈ $0.08/month. On the full 10K-token prompt (≈ 40 text units, assuming 1 unit = 1,000 characters): 20,000 units x $0.15/1K ≈ $3.00/month.

**D. Server per month (from section 5)**
- Lightsail 4 GB: **$24.00** (Lightsail 2 GB: $12.00)
- EC2 t4g.small + 30 GB gp3 + IPv4 (London): **$20.15**
- EC2 t4g.medium + 30 GB gp3 + IPv4 (London): **$33.88**

**E. Estimated monthly total (London, Bedrock EU geo, Lightsail 4 GB, no rerank or guardrails)**
- **Haiku 5.5:** $0.72 + $24.00 ≈ **$24.72/month**
- **Sonnet 5.5:** $14.30 + $24.00 ≈ **$38.30/month**
- Plus one-off ingestion: Haiku ≈ $1.3–3.0 + $0.75 embeddings. Sonnet ≈ $26–59 + $0.75 embeddings.
- With global routing (Anthropic list price), the model lines drop by about 9% (1/1.1). The server line stays the same.

**F. Same workload on the direct Anthropic API (global, list price)**
- Questions: Haiku 5.5 $0.65/month, Sonnet 5.5 $13.00/month. The Batch API could halve the ingestion: Haiku low case ≈ $0.60, Sonnet low case ≈ $12.00. Inference may run anywhere ("global"); EU or UK is not an option.

### Gaps
- Tokens per page and output tokens per document are my assumptions. A sample run on 5–10 real (or mock) council PDFs is needed to measure them.
- Thinking-token overhead on Haiku 5.5 / Sonnet 5.5 is not measured. It could raise output cost noticeably on Sonnet.
- GBP figures not given: no verified exchange rate.
