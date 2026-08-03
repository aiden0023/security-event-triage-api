# 0002: Name constraints via a metadata naming convention

- **Date:** 07/31/26
- **Status:** Accepted

## Context
In order to drop a constraint, there must be a name; if SQLAlchemy does not give a constraint a name,
Postgres will make one. However, this name that Postgres makes would not exist in the models, and only
the database. This will ultimately mean that Alembic cannot reference it, and a ```downgrade()``` for
a migration would fail.

## Decision
Set a ```naming_convention``` on ```Base.metadata``` which would cover indexes, check constraints, unique
constraints, foreign keys, and primary keys; SQLAlchemy will name everything itself the same way every time.
This will be used as a fallback for anything unnamed (composite indexes will still be named explicitly at
the call site).

## Alternatives Considered
Letting Postgres name things, but this would let names between models and the database be different, which
would not let rollbacks work for anything unnamed. Naming every constraint by hand, however there is the
possibility of just simply forgetting to name a constraint, which would make Postgres name it.

## Consequences
The naming convention cannot be changed later, since this would break the migrations.