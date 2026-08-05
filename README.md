# Security Event Triage API
A multi-tenant REST API for ingesting security events from customer tooling and tracking them through triage.
Uses Flask, PostgreSQL 17, SQLAlchemy 2.0, Pydantic v2. Two kinds of users share one platform: a customer's
own staff, and the provider's analysts who work across every customer organization. That shared platform
design is what makes isolation the hard part. The provider's analysts are supposed to see across organizations,
and customers are never supposed to see past their own.

## Highlights
- **Tenant scoping lives in the service layer:** The API never does fetch-then-compare (scoping is done in the 
```WHERE``` clause). An AST based test parses every route module and fails the build if a route imports a model
or DB session at all. This makes it so a route physically cannot open its own query (see [ADR 0005](docs/decisions/0005-query-scoping-lives-in-service-layer.md)).
- **Cross-tenant reads return 404 instead of 403:** If a ```403``` is returned when another organization tries to
retrieve a ```SecurityEvent``` that exists but is owned by a different organization, it would confirm that
the row/event exists. This is not ideal when thinking about malicious actors. Because of this, if
a user tries to retrieve an event that they do not have access to see, it will return a ```404```. However,
in order to make sure we do not lose visibility of making a distinction of the two errors from the server-side,
a logger is implemented to show what really caused the error (see [ADR 0006](docs/decisions/0006-404-on-cross-tenant-access.md)).
- **Idempotent ingestion:** A unique index on events are made on ```(org_id, source, external_id)```. Events are
inserted with an ```ON CONFLICT DO NOTHING``` clause in order for the database to resolve collisions. Inserting
an event will return ```201``` if the event is new, and ```200``` if the event already exists based on the
unique index. Why ```ON CONFLICT DO UPDATE``` is not used is because ```status``` and/or ```assigned_to```
might have been changed/updated between the first attempt to insert an event and the attempt to retry an insert of
an event, meaning that ```ON CONFLICT DO UPDATE``` will erase these changes.
- **Keyset pagination instead of offset:** Because of a constant data stream of inserting ```SecurityEvents```
as rows, using offset pagination when grabbing multiple events could and will skip incoming events and can
duplicate rows; using keyset pagination prevents this. The cursor for the keyset pagination is a compound
```(occurred_at, id)``` pair because ```occurred_at``` itself is not unique (see [ADR 0004](docs/decisions/0004-pagination-choice.md)).
- **`org_id` is never accepted from a request body:** This is set from the authenticated user after validation,
so a body cannot spoof tenancy.

## How to Run Locally
Requires Python 3.12+ and Docker.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Fill in ```SECRET_KEY```, ```JWT_SECRET_KEY```, and ```SEED_PASSWORD``` in an ```.env```. See the ```.env.example```
file for more information and instructions on how to generate these keys.

Compose starts **Postgres only** and the app runs locally against it:
```bash
docker compose up -d
flask db upgrade
flask seed provider --org-name "Provider Company" --admin-email admin@providercompany.example
flask seed demo
python run.py
```

The API is at ```http://127.0.0.1:5000```. Log in as a seeded demo user to get a token:
```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@companya.example","password":"<your SEED_PASSWORD>"}'
```

## Tests
```bash
pytest
```

Tests run against a real PostgreSQL instance, and not an in-memory database like SQLite; the schema leans on ```CHECK```
constraints, partial indexes, and JSONB. The ```triage_test``` database is created by the init script in ```docker/postgres/init/```,
which Postgres runs only on a fresh data volume. If this is missing, reset with ```docker compose down -v``` and bring
it back up.

## Status
Built and tested:
- JWT login, argon2 password hashing, rate-limited login endpoint.
- ```organizations``` / ```users``` with a provider vs. customer tier, ```security_events``` using CHECK-constrained
severity and status.
- ```POST /api/events``` as an idempotent ingest, ```GET /api/events``` as filtered and keyset paginated, ```GET
/api/events/<id>``` as tenant-scoped.
- One error envelope for every failure with a per-request ID echoed as ```X-Request-ID```.
- Seed CLI for bootstrapping a provider organization and demo data.

In Progress: triage state transitions with an audit log written in the same transaction as the state change.

Planned: an OWASP API Top 10 test suite as executable evidence, GitHub Actions CI against a real Postgres
service container, and HMAC-signed outbound webhook delivery.