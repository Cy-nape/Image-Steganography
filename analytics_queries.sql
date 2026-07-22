-- 1. Month-Over-Month Growth Rate of Encoding Jobs
-- Business Question: Are we seeing accelerating adoption of our steganography service over time?
-- This query calculates the total encoding jobs per month and uses the LAG() window function
-- to compute the percentage growth compared to the previous month.
WITH MonthlyJobs AS (
    SELECT 
        strftime('%Y-%m', created_at) AS month,
        COUNT(id) AS job_count
    FROM encode_jobs
    WHERE is_synthetic = 1
    GROUP BY month
)
SELECT 
    month,
    job_count,
    LAG(job_count) OVER (ORDER BY month) AS prev_month_count,
    ROUND(
        (job_count - LAG(job_count) OVER (ORDER BY month)) * 100.0 / 
        NULLIF(LAG(job_count) OVER (ORDER BY month), 0), 2
    ) AS mom_growth_percentage
FROM MonthlyJobs
ORDER BY month;


-- 2. Top 10% Power Users by Volume
-- Business Question: Who are our most active users that we should target for premium features?
-- This query uses the NTILE() window function to divide users into deciles based on their
-- total encoding volume, filtering only for the top 10% (Decile 1).
WITH UserVolumes AS (
    SELECT 
        user_id,
        COUNT(id) AS total_jobs
    FROM encode_jobs
    WHERE is_synthetic = 1
    GROUP BY user_id
),
RankedUsers AS (
    SELECT 
        user_id,
        total_jobs,
        NTILE(10) OVER (ORDER BY total_jobs DESC) AS decile
    FROM UserVolumes
)
SELECT 
    u.email,
    r.total_jobs
FROM RankedUsers r
JOIN users u ON r.user_id = u.id
WHERE r.decile = 1
ORDER BY r.total_jobs DESC
LIMIT 20; -- Show top 20 from the top 10%


-- 3. API Key Mapping and Usage Aggregation
-- Business Question: Do users who generate API keys perform more encoding jobs than those who don't?
-- This query uses JOINs to map API keys to users and aggregates their activity, 
-- demonstrating complex relational mapping.
SELECT 
    u.id AS user_id,
    u.email,
    COUNT(DISTINCT ak.id) AS num_api_keys,
    COUNT(DISTINCT ej.id) AS total_encoding_jobs
FROM users u
LEFT JOIN api_keys ak ON u.id = ak.user_id AND ak.is_synthetic = 1
LEFT JOIN encode_jobs ej ON u.id = ej.user_id AND ej.is_synthetic = 1
WHERE u.is_synthetic = 1
GROUP BY u.id, u.email
HAVING num_api_keys > 0
ORDER BY total_encoding_jobs DESC
LIMIT 20;


-- 4. Average Processing Time per Algorithm
-- Business Question: Which steganography algorithm provides the best performance for our users?
-- This queries the experimental data runs to rank the algorithms by encoding and decoding speeds.
SELECT 
    algorithm,
    COUNT(id) as total_runs,
    ROUND(AVG(compression_ratio), 4) AS avg_compression_ratio,
    ROUND(AVG(encode_time_ms), 2) AS avg_encode_time_ms,
    ROUND(AVG(decode_time_ms), 2) AS avg_decode_time_ms,
    ROUND(AVG(psnr), 2) AS avg_psnr
FROM experiment_runs
GROUP BY algorithm
ORDER BY avg_encode_time_ms ASC;


-- 5. Identifying Churned Users (CTE & Subqueries)
-- Business Question: Which users registered more than 3 months ago but haven't encoded anything in the last 30 days?
-- Uses Common Table Expressions (CTEs) to isolate active users and filters the main user base against it.
WITH ActiveUsersLast30Days AS (
    SELECT DISTINCT user_id
    FROM encode_jobs
    WHERE is_synthetic = 1 
      AND created_at >= date('now', '-30 days')
)
SELECT 
    u.email,
    u.created_at,
    (SELECT MAX(created_at) FROM encode_jobs WHERE user_id = u.id AND is_synthetic = 1) AS last_job_date
FROM users u
LEFT JOIN ActiveUsersLast30Days a ON u.id = a.user_id
WHERE u.is_synthetic = 1
  AND u.created_at <= date('now', '-90 days')
  AND a.user_id IS NULL
ORDER BY last_job_date DESC
LIMIT 20;
