# Neon free-tier database efficiency standard

Status: engineering policy, not a claim that the runtime has been optimized. Applies whenever this project uses Neon PostgreSQL. If the project does not use Neon, keep this policy conditional; do not introduce a database unnecessarily.

## Required behavior
1. Allow Neon compute to suspend when no legitimate work is occurring. Do not use always-on SELECT 1 heartbeats, keep-alive cron jobs or DB-backed uptime probes.
2. Do not poll database tables from browser components or server timers merely to keep UI fresh. Prefer user-driven fetches, mutation-triggered revalidation, caching with appropriate TTL, and event-driven updates.
3. Keep connections bounded and reuse clients/pools appropriately for the deployment runtime. Do not open a new pool per request or run an always-on process just to keep the DB warm.
4. Avoid database access during module imports, static builds, unauthenticated health probes, and irrelevant page views. Lazy-initialize where safe.
5. Batch reads/writes where appropriate; use indexed predicates, limits and pagination. Avoid N+1 queries and unbounded full-table scans.
6. Background jobs must run only for real queued work, with exponential backoff and a capped retry count. Job status checks should be bounded, preferably client-visible only while an active job exists.
7. Cache only non-sensitive, safely invalidatable data. Never compromise authorization, correctness, freshness requirements, or tenant isolation to save queries.
8. Add query-count/latency instrumentation, record compute usage via Neon dashboard, and set budget alerts if supported. Do not log credentials or full connection strings.
9. Document why every scheduled DB access is needed, its interval and stop condition. Prefer no scheduled DB queries when there are no users or jobs.
10. Verify idle behavior: close browser sessions, stop legitimate jobs, wait beyond the configured suspend interval, and confirm Neon compute scales to zero. Then verify first request wakes DB and succeeds.

## Deployment review checklist
- [ ] No periodic database keep-alive/health-check queries.
- [ ] No unnecessary background polling when idle.
- [ ] Pool sizing and serverless connection lifecycle reviewed.
- [ ] Indexes, query limits, pagination and caching reviewed.
- [ ] Workers and cron tasks have explicit stop conditions.
- [ ] Real idle-to-suspend and wake-up tested in Neon dashboard.
- [ ] Authentication, data integrity and security regression tests passed.

This policy does not imply that the application has passed the checklist. Record measured results separately.
