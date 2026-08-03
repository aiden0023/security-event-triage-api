# 0003: Why have a cli.py

- **Date:** 08/02/26
- **Status:** Accepted

## Context
I do not want open registration to be possible within the API (meaning no sort of open endpoint to something
like ```POST /auth/register```). Because of this, there needs to be something that creates the initial 
organization and first admin user in the database in order for new organizations and users to be created.

## Decision
Create a CLI with commands outside the HTTP layer that creates the first organization and the first admin user.
I will use ```flask.cli.AppGroup``` so the command runs inside an app context that has the database already
initialized.

## Alternatives Considered
Having an open endpoint like ```POST /auth/register```. However, I would consider this to be a security concern
since that would allow anyone to register a user with the API.

## Consequences
I could not think of any obvious consequences of this decision, since it keeps the API more secure.