# Regulations corpus on the shared RDS instance

ADR 0013. The corpus (chunks, vectors, keyword data) lives in its own database, `builders_corpus`, on Florin's
existing RDS Postgres instance, next to the lab's database. The Builders server only reads it.

## Once, by Florin (admin)

1. **Run the set-up** as the master user: see the command at the top of `corpus-setup.sql`. Pick two new long
   passwords (owner, reader). It creates the database, the pgvector extension, the `corpus` schema and two users:
   - `builders_corpus_owner`: creates and loads tables. Used only by the loader.
   - `builders_corpus_reader`: for the server. SELECT only, every transaction read-only by default, at most
     5 connections, 5-second query limit.
2. **Network:** in the RDS instance's security group, allow port 5432 from the Builders server's Elastic IP
   only (`/32`). Keep SSL on (`rds.force_ssl = 1` in the parameter group, or `sslmode=require` on every client).
3. **Store the connection strings** in Parameter Store (SecureString), London:
   - `/builders-lab/prod/secrets/corpus_reader_url` =
     `postgresql://builders_corpus_reader:<password>@<endpoint>:5432/builders_corpus?sslmode=require`
   - `/builders-lab/admin/corpus_owner_url`, the same with the owner. Not under `/builders-lab/prod/`: the server
     role can read everything there, and the server must never get the owner (least privilege). The deploy user
     and admins can read `/builders-lab/admin/`.
4. Optional, if the lab's database still lets any user connect: `REVOKE CONNECT ON DATABASE <lab db> FROM PUBLIC;`
   and grant it back to the lab's own user. The Builders users have no rights on the lab's tables either way.

## Then

- Rebuild and load from Git on any machine that can reach the database (your laptop: its IP is allowed):
  `python -m system.rag.build --load` (raw files, parse, chunk, embed, local index, then `system.rag.load` as the
  owner, URL from `/builders-lab/admin/corpus_owner_url`). The load replaces the corpus in one transaction.
- Server (reader): reads `corpus_reader_url` from Parameter Store; `rag.search` connects only with it.

## Done (20 Nov 2026)

- Instance `rag-lab-db`, Frankfurt (`eu-central-1`), endpoint `rag-lab-db.ct624uuqgiy1.eu-central-1.rds.amazonaws.com`.
- First run stopped at "must be able to SET ROLE builders_corpus_owner" (Postgres 16 on RDS: the master user is
  not a full superuser). `corpus-setup-finish.sql` completed it; `corpus-setup.sql` now joins the role first.
- Reader URL in `/builders-lab/prod/secrets/corpus_reader_url`, owner URL in `/builders-lab/admin/corpus_owner_url`.
- Git Bash on Windows turns `/builders-lab/...` into a Windows path: run AWS and Docker commands with
  `MSYS_NO_PATHCONV=1`.
- The lab's `infra/provision.py` has `pause` (stops the instance) and `down` (deletes it, no backup): either
  also stops or deletes this corpus. It can be rebuilt from Git with `python -m system.rag.build --load`.

## Switch the server to the corpus (go-live)

1. **Stack update** (server role gets Bedrock rights; metadata hop limit 2). Same command as the first install,
   with your usual parameters (`deploy/README.md`):
   `aws cloudformation deploy --region eu-west-2 --stack-name builders-lab-prod --template-file deploy/cloudformation/server.yaml --capabilities CAPABILITY_IAM --parameter-overrides AlertEmail=<your email>`
2. **Network:** the RDS security group must allow 5432 from the server's Elastic IP (step 2 of "Once").
3. **Switch on:** `MSYS_NO_PATHCONV=1 aws ssm put-parameter --region eu-west-2 --type String --overwrite --name /builders-lab/prod/rag_enabled --value on`
4. **Redeploy** (any push to main, or run the pipeline by hand). Each upgrade re-reads Parameter Store
   (`upgrade.sh` runs `env-from-ssm.sh`). Back to the fallback: set `rag_enabled` to `off` and redeploy.

## Live (20 Nov 2026, 19:53 UTC)

Stack updated (role rights, hop limit 2), `rag_enabled=on`, two deploys (the first installs the `upgrade.sh` that
re-reads Parameter Store). `search_regulations` returns `"backend": "corpus"`: the asbestos licence question finds
HSG227 paragraph 21, Awaab's Law finds the 24-hour emergency sections, "best pizza in London" returns nothing.
