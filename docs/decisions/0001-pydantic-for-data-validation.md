# 0001: Using Pydantic (v2) for data validation

- **Date:** 07/31/26
- **Status:** Accepted

## Context
First decision made (when determining the dependencies for this project) for data validation: Pydantic 
vs. Marshmallow.

## Decision
Choosing Pydantic over Marshmallow. Already familiar with Pydantic. Pydantic's ```ValidationError.errors()```
function returns a list of dicts with loc, msg, and type, while Marshmallow gives a nested dict. Pydantic 
has ```extra="forbid"``` which allows me to write one less custom check for mass-assignment rejection.
Pydantic has ```IPvAnyAddress``` which allows me to reject malformed IPs with a real parser rather than
using regex.

## Alternatives Considered
As mentioned before, Marshmallow was considered as well. Choosing Pydantic over Marshmallow does force
me to give up several things that Marshmallow has over Pydantic.

## Consequences
Marshmallow has ```marshmallow-sqlalchemy```, which can auto-generate schemas from models; Pydantic needs
```model_config``` defined and explicitly declared output fields (however, since this is a security API,
the explicit output fields is overall better).