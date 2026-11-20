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
   - `/builders-lab/prod/secrets/corpus_owner_url`, the same with the owner (for the loader; or keep it only on the laptop).
4. Optional, if the lab's database still lets any user connect: `REVOKE CONNECT ON DATABASE <lab db> FROM PUBLIC;`
   and grant it back to the lab's own user. The Builders users have no rights on the lab's tables either way.

## Then

- Loader (owner): `python -m system.rag.load` (next step) creates the tables in `corpus` and loads chunks and vectors.
- Server (reader): reads `corpus_reader_url` from Parameter Store; `rag.search` connects only with it.
