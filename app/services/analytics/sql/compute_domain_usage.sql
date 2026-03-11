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
joined AS (
    SELECT
        a.domain,
        dc.name AS category,
        a.total_seconds
    FROM agg a
    LEFT JOIN domain_to_category dtc ON dtc.domain = a.domain
    LEFT JOIN domain_categories dc ON dc.id = dtc.category_id
),
filtered AS (
    SELECT
        domain,
        category,
        total_seconds
    FROM joined
    WHERE (:search IS NULL OR domain ILIKE CONCAT('%', :search, '%'))
),
ranked AS (
    SELECT
        domain,
        category,
        total_seconds,
        COUNT(*) OVER() AS total_items
    FROM filtered
)
SELECT domain, category, total_seconds, total_items
FROM ranked
ORDER BY
    CASE
        WHEN :sort_by = 'total_seconds' AND :sort_order = 'asc'
        THEN total_seconds
    END ASC,
    CASE
        WHEN :sort_by = 'total_seconds' AND :sort_order = 'desc'
        THEN total_seconds
    END DESC,
    CASE
        WHEN :sort_by = 'domain' AND :sort_order = 'asc'
        THEN domain
    END ASC,
    CASE
        WHEN :sort_by = 'domain' AND :sort_order = 'desc'
        THEN domain
    END DESC,
    CASE
        WHEN :sort_by = 'category' AND :sort_order = 'asc'
        THEN COALESCE(category, '')
    END ASC,
    CASE
        WHEN :sort_by = 'category' AND :sort_order = 'desc'
        THEN COALESCE(category, '')
    END DESC,
    domain ASC
OFFSET :offset
LIMIT :limit
