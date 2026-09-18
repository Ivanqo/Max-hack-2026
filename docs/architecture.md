# Architecture

```text
React Student UI ---\
                    +--> Django REST API --> PostgreSQL
React Admin UI -----/          |
                               +--> Matching Engine
                               +--> Career GPS
                               +--> Knowledge Search
                               +--> Analytics
                               +--> MAX Integration Adapter
```

## Modular Monolith

The MVP uses a modular monolith because the product needs one coherent release unit, simple local setup, and clear transactional behavior. Backend domains are split into Django apps so the code stays navigable without adding service-to-service network overhead.

## Tenant Isolation

Users, student profiles, career roles, opportunities, knowledge items, subscriptions, and demo universities carry university context. Student and admin endpoints filter by the current user's university so demo data from `Demo University` and `North Tech University` stays separated.

## Service Layer

Business rules live in small services:

- `KnowledgeSearchService` ranks verified knowledge and returns a safe fallback when no answer is confirmed.
- `CareerGPSService` calculates readiness, strengths, gaps, and next actions.
- `OpportunityMatchingService` ranks opportunities and stores explainable match results.
- Notification services route product events to either a mock or real MAX client.

Views stay thin enough to handle request/response details, permissions, audit logging, and tenant filters.

## Integration Boundaries

MAX is behind an adapter. Mock mode marks messages as `simulated` and keeps local development deterministic. Real mode requires `MAX_API_URL` and `MAX_BOT_TOKEN`; if either is missing or delivery fails, the product keeps the notification state explicit instead of pretending a message was sent. Return-to-app buttons use MAX `open_app` only when `MAX_OPEN_APP_TARGET` is configured with the public bot username/link for the mini-app.

## Scaling Path

The first scaling step is still inside the monolith: add indexes, broaden tenant checks, and move static reference data to managed tables. If load or ownership requires it later, matching, search, analytics exports, and notifications can be extracted because their logic already sits behind service boundaries.
