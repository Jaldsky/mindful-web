WITH bounds AS (
    SELECT
        :start_ts AS start_ts,
        :end_ts AS end_ts,
        CASE
            WHEN :granularity = 'hour' THEN INTERVAL '1 hour'
            ELSE INTERVAL '1 day'
        END AS bucket_step
),
last_before AS (
    SELECT domain, event_type, timestamp
    FROM attention_events
    WHERE user_id = :user_id
      AND timestamp <= (SELECT start_ts FROM bounds)
    ORDER BY timestamp DESC
    LIMIT 1
),
events_in_range AS (
    SELECT domain, event_type, timestamp
    FROM attention_events
    WHERE user_id = :user_id
      AND timestamp >= (SELECT start_ts FROM bounds)
      AND timestamp <= (SELECT end_ts FROM bounds)
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
        GREATEST(timestamp, (SELECT start_ts FROM bounds)) AS s,
        LEAST(COALESCE(next_ts, (SELECT end_ts FROM bounds)), (SELECT end_ts FROM bounds)) AS e
    FROM ordered
),
active_intervals AS (
    SELECT domain, s, e
    FROM bounded
    WHERE e > s
      AND event_type = 'active'
),
buckets AS (
    SELECT generate_series(
        CASE
            WHEN :granularity = 'hour' THEN date_trunc('hour', (SELECT start_ts FROM bounds))
            ELSE date_trunc('day', (SELECT start_ts FROM bounds))
        END,
        CASE
            WHEN :granularity = 'hour' THEN date_trunc('hour', (SELECT end_ts FROM bounds))
            ELSE date_trunc('day', (SELECT end_ts FROM bounds))
        END,
        (SELECT bucket_step FROM bounds)
    ) AS bucket_start
),
bucket_domain AS (
    SELECT
        b.bucket_start,
        ai.domain,
        COALESCE(
            CAST(SUM(
                EXTRACT(
                    EPOCH FROM (
                        LEAST(ai.e, b.bucket_start + (SELECT bucket_step FROM bounds))
                        - GREATEST(ai.s, b.bucket_start)
                    )
                )
            ) FILTER (
                WHERE ai.e IS NOT NULL
                  AND ai.s IS NOT NULL
                  AND ai.e > b.bucket_start
                  AND ai.s < b.bucket_start + (SELECT bucket_step FROM bounds)
            ) AS BIGINT),
            0
        ) AS domain_seconds
    FROM buckets b
    LEFT JOIN active_intervals ai
        ON ai.e > b.bucket_start
       AND ai.s < b.bucket_start + (SELECT bucket_step FROM bounds)
    GROUP BY b.bucket_start, ai.domain
),
bucket_totals AS (
    SELECT
        bucket_start,
        COALESCE(CAST(SUM(domain_seconds) AS BIGINT), 0) AS total_seconds,
        COUNT(*) FILTER (WHERE domain IS NOT NULL AND domain_seconds > 0)::INT AS unique_domains
    FROM bucket_domain
    GROUP BY bucket_start
),
bucket_domains_ranked AS (
    SELECT
        bucket_start,
        domain,
        domain_seconds,
        ROW_NUMBER() OVER (
            PARTITION BY bucket_start
            ORDER BY domain_seconds DESC, domain ASC
        ) AS rn
    FROM bucket_domain
    WHERE domain IS NOT NULL
      AND domain_seconds > 0
),
bucket_domains_top AS (
    SELECT
        bucket_start,
        json_agg(
            json_build_object(
                'domain', domain,
                'total_seconds', domain_seconds
            )
            ORDER BY domain_seconds DESC, domain ASC
        ) AS domains
    FROM bucket_domains_ranked
    WHERE rn <= :top_domains_limit
    GROUP BY bucket_start
),
bucket_result AS (
    SELECT
        b.bucket_start,
        COALESCE(t.total_seconds, 0)::BIGINT AS total_seconds,
        COALESCE(t.unique_domains, 0)::INT AS unique_domains,
        COALESCE(d.domains, '[]'::json) AS domains
    FROM buckets b
    LEFT JOIN bucket_totals t ON t.bucket_start = b.bucket_start
    LEFT JOIN bucket_domains_top d ON d.bucket_start = b.bucket_start
)
SELECT
    bucket_start,
    total_seconds,
    unique_domains,
    domains
FROM bucket_result
ORDER BY bucket_start ASC;
WITH bounds AS (
    SELECT
        :start_ts AS start_ts,
        :end_ts AS end_ts,
        CASE
            WHEN :granularity = 'hour' THEN INTERVAL '1 hour'
            ELSE INTERVAL '1 day'
        END AS bucket_step
),
last_before AS (
    SELECT domain, event_type, timestamp
    FROM attention_events
    WHERE user_id = :user_id
      AND timestamp <= (SELECT start_ts FROM bounds)
    ORDER BY timestamp DESC
    LIMIT 1
),
events_in_range AS (
    SELECT domain, event_type, timestamp
    FROM attention_events
    WHERE user_id = :user_id
      AND timestamp >= (SELECT start_ts FROM bounds)
      AND timestamp <= (SELECT end_ts FROM bounds)
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
        GREATEST(timestamp, (SELECT start_ts FROM bounds)) AS s,
        LEAST(COALESCE(next_ts, (SELECT end_ts FROM bounds)), (SELECT end_ts FROM bounds)) AS e
    FROM ordered
),
active_intervals AS (
    SELECT domain, s, e
    FROM bounded
    WHERE e > s
      AND event_type = 'active'
),
buckets AS (
    SELECT generate_series(
        CASE
            WHEN :granularity = 'hour' THEN date_trunc('hour', (SELECT start_ts FROM bounds))
            ELSE date_trunc('day', (SELECT start_ts FROM bounds))
        END,
        CASE
            WHEN :granularity = 'hour' THEN date_trunc('hour', (SELECT end_ts FROM bounds))
            ELSE date_trunc('day', (SELECT end_ts FROM bounds))
        END,
        (SELECT bucket_step FROM bounds)
    ) AS bucket_start
),
bucket_domain AS (
    SELECT
        b.bucket_start,
        ai.domain,
        COALESCE(
            CAST(SUM(
                EXTRACT(
                    EPOCH FROM (
                        LEAST(ai.e, b.bucket_start + (SELECT bucket_step FROM bounds))
                        - GREATEST(ai.s, b.bucket_start)
                    )
                )
            ) FILTER (
                WHERE ai.e IS NOT NULL
                  AND ai.s IS NOT NULL
                  AND ai.e > b.bucket_start
                  AND ai.s < b.bucket_start + (SELECT bucket_step FROM bounds)
            ) AS BIGINT),
            0
        ) AS domain_seconds
    FROM buckets b
    LEFT JOIN active_intervals ai
        ON ai.e > b.bucket_start
       AND ai.s < b.bucket_start + (SELECT bucket_step FROM bounds)
    GROUP BY b.bucket_start, ai.domain
),
bucket_totals AS (
    SELECT
        bucket_start,
        COALESCE(CAST(SUM(domain_seconds) AS BIGINT), 0) AS total_seconds,
        COUNT(*) FILTER (WHERE domain IS NOT NULL AND domain_seconds > 0)::INT AS unique_domains
    FROM bucket_domain
    GROUP BY bucket_start
),
bucket_domains_ranked AS (
    SELECT
        bucket_start,
        domain,
        domain_seconds,
        ROW_NUMBER() OVER (
            PARTITION BY bucket_start
            ORDER BY domain_seconds DESC, domain ASC
        ) AS rn
    FROM bucket_domain
    WHERE domain IS NOT NULL
      AND domain_seconds > 0
),
bucket_domains_top AS (
    SELECT
        bucket_start,
        json_agg(
            json_build_object(
                'domain', domain,
                'total_seconds', domain_seconds
            )
            ORDER BY domain_seconds DESC, domain ASC
        ) AS domains
    FROM bucket_domains_ranked
    WHERE rn <= :top_domains_limit
    GROUP BY bucket_start
),
bucket_result AS (
    SELECT
        b.bucket_start,
        COALESCE(t.total_seconds, 0)::BIGINT AS total_seconds,
        COALESCE(t.unique_domains, 0)::INT AS unique_domains,
        COALESCE(d.domains, '[]'::json) AS domains
    FROM buckets b
    LEFT JOIN bucket_totals t ON t.bucket_start = b.bucket_start
    LEFT JOIN bucket_domains_top d ON d.bucket_start = b.bucket_start
)
SELECT
    bucket_start,
    total_seconds,
    unique_domains,
    domains
FROM bucket_result
ORDER BY bucket_start ASC;
