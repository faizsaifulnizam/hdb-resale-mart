-- Read-only export relations; validate unrounded values before publication.
CREATE OR REPLACE VIEW town_4room_unrounded AS
SELECT town, n_t0, n_t1,
       med_t0 AS med_ppsm_2025q3,
       med_t1 AS med_ppsm_2026q3,
       100 * (med_t1 / med_t0 - 1) AS med_pct_change,
       mean_t0 AS mean_ppsm_2025q3,
       mean_t1 AS mean_ppsm_2026q3,
       w_t0 AS share_2025q3,
       w_t1 AS share_2026q3,
       w_t0 * (mean_t1 - mean_t0) AS rate_effect,
       (w_t1 - w_t0) * mean_t0 AS mix_effect,
       (w_t1 - w_t0) * (mean_t1 - mean_t0) AS interaction
FROM yoy_4room;

CREATE OR REPLACE VIEW town_4room_export AS
SELECT town, n_t0, n_t1,
       round(med_ppsm_2025q3, 2) AS med_ppsm_2025q3,
       round(med_ppsm_2026q3, 2) AS med_ppsm_2026q3,
       round(med_pct_change, 2) AS med_pct_change,
       round(mean_ppsm_2025q3, 2) AS mean_ppsm_2025q3,
       round(mean_ppsm_2026q3, 2) AS mean_ppsm_2026q3,
       round(share_2025q3, 4) AS share_2025q3,
       round(share_2026q3, 4) AS share_2026q3,
       round(rate_effect, 2) AS rate_effect,
       round(mix_effect, 2) AS mix_effect,
       round(interaction, 2) AS interaction
FROM town_4room_unrounded
ORDER BY n_t1 DESC, town;
