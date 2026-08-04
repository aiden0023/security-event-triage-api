# 0005: Query scoping lives in the service layer

- **Date:** 08/04/26
- **Status:** Accepted

## Context
Every ```SecurityEvent``` belongs to an organization, so every read/write must be constrained to the caller's
organization. This means that the API needs to be multi-tenant. This brings the question of where the organization
filter should live: the route or the service? The purpose of this is to prevent a cross-tenant data leak from a
route that forgets to scope or that fetches the event and then checks the organization.

## Decision
All tenant-scoped queries should live in the service layer, meaning that routes should never query any tenant model
directly. The organization filter goes into the actual SQL query, meaning there should never be a fetch-then-compare
done in Python. This also keeps the routes thin, where the route pass the organization's ID to a service function
that actually owns and runs the query.

## Alternatives Considered
The main alternative considered was to fetch-then-compare, as mentioned previously. This was ultimately rejected
because it will need to be done on every endpoint, and it loads data that the user may not be authorized to view
before actually checking; if one route forgets this check, it could lead to a data breach.

## Consequences
Because of this, routes cannot import tenant models or the DB; any route that needs the database will go through
a service. In order to enforce this, ```tests/unit/test_route_isolation.py``` was written, which parses each route
module with Python's ast module and fails the build if it imports anything under ```app.models``` or 
```app.extensions``` (which also blocks the DB too).