-- Hunt 03: History visits made through the browser's API, not the address bar
-- Run against a copy of a Chromium History file (Chrome, Edge, Brave, Comet):
--   sqlite3 "History-copy" < 03-history-from-api-visits.sql
-- Signal: the FROM_API qualifier, bit 0x08000000 (134217728) of visits.transition.
-- Lab (Phase 3, 3 runs each): set for Claude in Chrome's agent (LINK | FROM_API) and for
-- Playwright over CDP (TYPED | FROM_API); NOT set for a person typing (TYPED | FROM_ADDRESS_BAR),
-- for a link handed over by another app (AUTO_TOPLEVEL), or for Comet's own agent.
-- Chromium defines the bit only as "originated from an external application; embedder dependent",
-- so treat it as a lead and correlate. Tested on the lab profiles.
-- Velociraptor: Custom.Windows.Applications.AIBrowsers/HistoryFromApiVisits runs this for you.
SELECT datetime(v.visit_time / 1000000 - 11644473600, 'unixepoch') AS visit_utc,
       u.url,
       u.title,
       printf('0x%08X', v.transition)                AS transition_hex,
       CASE v.transition & 0xFF WHEN 0 THEN 'LINK' WHEN 1 THEN 'TYPED'
            WHEN 6 THEN 'START_PAGE' WHEN 8 THEN 'RELOAD' ELSE v.transition & 0xFF END AS core
FROM visits v
JOIN urls u ON u.id = v.url
WHERE (v.transition & 134217728) != 0
--  AND (u.url LIKE '%bank%' OR u.url LIKE '%admin%')   -- narrow to sensitive sites
ORDER BY v.visit_time;
