# 0004: Deciding what type of pagination to use

- **Date:** 08/03/26
- **Status:** Accepted

## Context
Before starting to write the ```GET /api/events``` route, I have to make a clear decision on pagination:
offset vs. keyset/cursor. Because the events table is constantly getting rows inserted (one row per event),
this choice sort of shapes the whole public API contract.

## Decision
I chose to use a keyset/cursor pagination over an offset pagination. The main reason why I chose this is that
it feels the most correct for a live write stream. The performance is flat and does not change based on grabbing
older events, because keyset will just use the indexes I already built. New events arriving at the top of the order
does not shift any pages when walking through it (something offset would do) because it will just grab rows older
than an exact ```(occurred_at, id)``` pair; this means no duplicates and no skips.

## Alternatives Considered
Using offset pagination over keyset pagination was a consideration. This is mainly because offset pagination would
allow a clean "jump straight to page 5" sort of function, which keyset cannot do. However, this consideration was
pretty quickly overturned because "deeper" pages get much slower (i.e. going to page 100 would be much slower than
just going to page 1). Along with this, offset could cause a drift/skip/duplication problem when it comes to a live
stream of data (because of concurrent inserts, a user could miss an alert while paging).

## Consequences
Keyset is basically "infinite scroll", meaning there is no easy way to jump to a specific page in a UI (see 
```Alternatives Considered``` for more details). With keyset, there is no cheap total count, meaning I will have to
create a separate ```COUNT(*)``` query if I want to grab the total number of events being grabbed. And, just overall,
keyset is more complex because I will need a compound cursor at ```(occurred_at, id)``` due to ```occurred_at``` not
being unique by itself.