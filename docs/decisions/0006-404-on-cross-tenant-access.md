# 0006: 404 and not 403 on cross-tenant resource access

- **Date:** 08/04/26
- **Status:** Accepted

## Context
As referenced in ```ADR 0005```, a ```SecurityEvent``` belongs to one organization, so when an authenticated user
requests an event that exists but belongs to a different organization, should it return ```403 Forbidden``` or
```404 Not Found```?

## Decision
Despite ```403``` making the most sense initially, I want it to return ```404```. The main reasoning for this is
because the client/user should not be able to distinguish between "does not exist" and "exists, but not in your
organization". This is simply just a resource-level denial, so it makes the most sense to return ```404``` (if
this was a role-level denial, it makes more sense to return ```403```). There is no reason to leak existence,
since a malicious actor could enumerate through IDs to find IDs that return ```403```, confirming to them that
it exists.

## Alternatives Considered
The clear alternative is to return ```403``` instead. However, like mentioned before, this lets someone confirm
the existence of an event with that ID without having permission to view the event. Especially for a piece of
software for security, it makes zero sense to return ```403```.

## Consequences
An actual user won't be able to tell the two different types of errors apart, making it difficult to actually
tell from the server-side whether the error was because of a true "not found" error or if it was a "permissions"
error. So, from the server-side, I implemented logging in order to see the difference between the two errors from 
the server; a true ```404``` gets logged as ```INFO```, while a ```404``` that's caused because of permissions is
logged as ```WARNING```. So, a user and/or malicious actor does not learn anything, but from the server-side we 
do not lose visibility of what actually caused the error.