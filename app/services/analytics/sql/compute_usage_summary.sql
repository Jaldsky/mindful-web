WITH last_before AS (
    SELECT domain, event_type, timestamp
    FROM attention_events
    WHERE user_id = :user_id AND timestamp <= :start_ts
    ORDER BY timestamp DESC
    LIMIT 1
),
events_in_range AS (
    SELECT domain, event_type, timestamp
    FROM attention_events
    WHERE user_id = :user_id AND timestamp >= :start_ts AND timestamp <= :end_ts
),
timeline AS (
    SELECT domain, event_type, timestamp FROM last_before
    UNION ALL
    SELECT domain, event_type, timestamp FROM events_in_range
),
ordered AS (
    SELECT
        domain,
        event_type,
        timestamp,
        LEAD(timestamp) OVER (ORDER BY timestamp ASC) AS next_ts
    FROM timeline
),
bounded AS (
    SELECT
        domain,
        event_type,
        GREATEST(timestamp, :start_ts) AS s,
        LEAST(COALESCE(next_ts, :end_ts), :end_ts) AS e
    FROM ordered
),
intervals AS (
    SELECT domain, EXTRACT(EPOCH FROM (e - s)) AS seconds
    FROM bounded
    WHERE e > s AND event_type = 'active'
),
agg AS (
    SELECT domain, CAST(SUM(seconds) AS BIGINT) AS total_seconds
    FROM intervals
    GROUP BY domain
),
summary AS (
    SELECT
        COALESCE(CAST(SUM(total_seconds) AS BIGINT), 0) AS total_seconds,
        COUNT(*)::INT AS total_domains,
        COALESCE(CAST(AVG(total_seconds) AS BIGINT), 0) AS avg_seconds_per_domain
    FROM agg
),
top_domain AS (
    SELECT domain AS top_domain, total_seconds AS top_domain_seconds
    FROM agg
    ORDER BY total_seconds DESC, domain ASC
    LIMIT 1
)
SELECT
    s.total_seconds,
    s.total_domains,
    s.avg_seconds_per_domain,
    t.top_domain,
    COALESCE(t.top_domain_seconds, 0)::BIGINT AS top_domain_seconds
FROM summary s
LEFT JOIN top_domain t ON TRUE;
