# Phase 3 Runbook: person vs agent, same task (Windows VM `thorhq-windows`)

**Why:** Act 3 of the deck rests on one agent form-fill (`C0C0N-CANARY-COMET-04`) that produced no process and no distinctive disk trace. That is a single negative result with no person-run baseline next to it. This phase runs the **same task as a person, as the browser's agent, and as a script**, three times each, and diffs everything. Either outcome makes the talk stronger:
- **We find a tell** → a new slide: "Here is how to tell them apart," plus a hunt.
- **We find none** → a side-by-side slide: "Three runs each. Byte-for-byte the same on disk." The negative result becomes evidence instead of an assertion.

Legend: 🧑 = you at the VMware console (as `thorh`) · 🤖 = Claude over SSH · 📦 = collection bundle label. Same rules as Phase 2: throwaway accounts only, canary strings only, no destruction.

## Prep status (2026-10-06, done on the Mac)

- **Site:** `www/hva.js` (interaction summary → `POST /telemetry`), `www/form-hva.html` (the Phase 3 form; `form.html` is left untouched so Phase 2 stays reproducible), `www/canary-HVA-01.html` → `canary-HVA-02.html` (one link). `www/server.py` now writes `/telemetry` posts to `hva-telemetry.jsonl` and takes `LAB_PORT` (default 8088). Tested locally end to end.
- **Extractor:** `scripts/hva_compare.py` (run with `.venv/bin/python`). Tested against the Phase 2 bundles `22-comet-live` → `23-comet-after-chat-live`. Includes a workaround for SNSS command id 51, which the installed `ccl_chromium_snss2` predates.
- **Still to do on the VM:** copy the four new files and `server.py` to `C:\lab\www\`, restart the canary server task, and check `marker.ps1` and Sysmon network logging for `comet.exe`.

### What the Phase 2 data already shows (preliminary, n = 1)
- **History:** the `Form.html` visit from the A4 agent task is recorded as `TYPED | FROM_ADDRESS_BAR | CHAIN_START | CHAIN_END`, in the same tab, exactly like the person-typed visits before it. The person's visits include the URL typos `SECRET-COMET-03.html` and `secret-COMET-03.html`, which an agent wouldn't make. No `FROM_API` qualifier and no `visit_source` row. **Confirmed by the operator (2026-10-06):** the agent opened `Form.html`; nobody typed it. So in this run, Comet's agent navigation was recorded exactly like a person typing in the address bar. Phase 3 checks whether that holds in 3 of 3 runs.
- **Timing (H3):** the autofill row was written 55.4 s after the form page loaded. The agent was *not* fast; LLM steps take time. Don't assume "the agent is faster than a person."
- **Agent extension stores:** between the two bundles, only the Comet assistant extension (`mcjlamohc…`) changed (`ppxl_scheduler-history`, `last-user-state`). The `comet-agent` store in `Profile 1` did not.
- **Site-side (local test, browser automation over CDP):** clicks arrive `isTrusted: true` with 0 pointer moves before them. The Name field holds 23 characters from 0 keydown events and one `insertText` input event. A value set directly by script shows up as an untrusted input event. These are the H7 fields to compare against a person typing.

## Session log, 2026-10-06 (trimmed run: T1 only, 3 × P, 3 × A, 3 × S)

**Done autonomously (Claude, over SSH):**
- Site deployed to `C:\lab\www\` (`server.py.phase2.bak` kept), `c0c0n-www` task restarted, `/telemetry` verified, test line removed.
- Baseline collection `20261006-232107-70-hva-baseline` (real Comet profile, before any Phase 3 activity).
- S runs ×3 on a **copy** of the Comet profile (`C:\lab\hva\comet-S\User Data`, `Profile 1`) via `scripts/hva_script.py`, launched in thorh's console session with a `/it` scheduled task. Collection `20261006-233424-73-hva-script`. Two attempts hit a Playwright viewport/restored-tab error on the second launch in a process (17:53 and 17:59 UTC, form filled but not submitted, outside the recorded windows); each run now gets its own process.
- Bundles (caches excluded) pulled to `collections/`; `reports/hva-runs-S.csv`, `reports/hva-telemetry-S.jsonl`, analysis in `reports/hva-S/`.
- Guided console for the P/A runs deployed: `C:\Users\thorh\Desktop\Phase3-HVA-runs.cmd` (→ `C:\lab\scripts\hva_guide.ps1`, writes `C:\lab\hva\runs.csv`).
- **Not done:** VM snapshot `c0c0n-03-pre-hva`. `vmrun -vp` with the shared lab password from Notion fails ("Authentication for encrypted virtual machine failed"), so the VM encryption password has changed since 2026-09-17. Interactive runs used a `/it` scheduled task instead of `insession.sh` (which depends on the same password).
- `windows-host` MagicDNS name doesn't resolve from the Mac; reached it at its Tailscale IP with `HostKeyAlias` (host key verified).

**2026-10-07, A-T1-1 first attempt (not recorded as a run):** Comet 153.0.8010.224, Profile 1, signed in to the throwaway Perplexity account (Free plan; `__Secure-next-auth.session-token` valid to 2026-10-20). The prompt "Open http://192.168.1.14:8088/form-hva.html and fill the form…" sent from the side panel on the Perplexity home tab was answered in **Search** mode ("Researched 1s"): *it can't directly open or interact with pages … on your local network (… is a private/internal address)*, followed by manual steps. Phase 2 (Comet 152, 2026-09-20) completed the same kind of task on the IP URL. Guide switched to `http://thorhq-windows:8088/form-hva.html` (resolves to 192.168.1.14 on the VM, no system change), with a fallback (person opens the page, agent fills it) recorded in `C:\lab\hva\notes.txt`.
**P-T1-1 caveats:** its recorded window (05:35:37–05:35:46 Z) starts after the page load, so label it by canary, not by window; site telemetry shows 2 paste inputs and runs of ~33 ms key gaps (machine-speed key injection, likely the VMware console's paste-as-typing), so treat its keystroke data as not hand-typed. History/autofill for it are still usable. Also: the browser's UTC and PowerShell's `ToUniversalTime()` on the VM differ by ~1 h; reconcile against the server's `serverTime` before trusting windows.

**S results (3 of 3):**
| field | S (Playwright over CDP, Comet 153.0.8010.224) |
|---|---|
| History transition of the form visit | `TYPED \| FROM_API \| CHAIN_START \| CHAIN_END`; **no** `FROM_ADDRESS_BAR` |
| tab | a new tab id per run |
| autofill written after page load | 1.7 s, 6.1 s, 2.2 s |
| site: keystrokes / inputs | 0 keydown; 3 × `insertText` (one per field); name 23 chars |
| site: pointer | 1 pointer move, 1 trusted click |
| site: `navigator.webdriver` | **true** |

Compare with the Phase 2 agent visit (`TYPED | FROM_ADDRESS_BAR`, n = 1). If the A runs repeat that and the P runs show `FROM_ADDRESS_BAR` too, then **`FROM_API` (transition bit `0x08000000`) in History separates CDP/extension-API navigation from address-bar navigation on a dead box, while Comet's own agent hides among the person's typed visits.**

## Hypotheses: where a difference could show up

| # | Layer | Field | Why it might differ | Dead-box? |
|---|---|---|---|---|
| H1 | History | `visits.transition` (core type + qualifiers), `from_visit`, `opener_visit`, `visit_duration`; `urls.typed_count` | A person types the URL or clicks a link (TYPED / LINK). An agent opening a tab through the extension API may record a different core type, or no `from_visit` chain | Yes |
| H2 | Sessions (SNSS) | Tab-group membership and title; navigation entries; `has_post_data` | Agents often work in their own tab group (Claude stores `mcpTabGroupId`; Comet may do the same) | Yes |
| H3 | Web Data | `autofill.date_created`, `date_last_used`, `count` | Seconds between page load (History) and autofill write: a person needs tens of seconds to type, an agent needs a few | Yes |
| H4 | Agent extension storage | `Local Extension Settings/<comet-agent id>/`, extension IndexedDB, Service Worker cache | Task state or step logs without the canary string; our earlier `strings \| grep COMET-04` search would miss these | Yes |
| H5 | Network (Elastic) | `comet.exe` connections to Perplexity backends interleaved with requests to `:8088` | The agent calls home between steps; a person's form-fill has no backend traffic in the middle | No (telemetry) |
| H6 | File events (Sysmon 11 / Elastic file) | Writes in the profile during the task window | The agent extension may write state or screenshots while it works | No (telemetry) |
| H7 | The page itself (site-side) | `isTrusted`, keystroke gaps, paste vs typed, pointer-move count, focus order, load-to-submit time | Shows what a website can see that the endpoint cannot (the FP-Agent point, on our own data) | Server log |

## Design

- **Tasks** (one canary per run, format `C0C0N-CANARY-HVA-<P|A|S>-<task>-<n>`):
  - **T1 Form:** open `form-hva.html`, fill name, email and notes, submit.
  - **T2 Navigate and read:** open `canary-HVA-01.html`, follow its single link to `canary-HVA-02.html`. For agent runs, also ask for a summary.
- **Actors:** **P** = you, by hand. **A** = Comet agent mode (you type the instruction into the sidecar). **S** = Playwright control with `--remote-debugging-port`.
- **Runs:** Comet: T1 and T2 × P and A × 3 = 12 runs. Plus S × T1 × 3 = 3. Optional: Claude in Chrome, T1 × P and A × 3 = 6.
- **Isolation:** close the browser between runs. Leave at least 2 minutes of idle time between runs so the telemetry windows don't overlap. Record each run's start and stop times with `marker.ps1` (writes a timestamped Sysmon/Elastic marker).
- **Collections:** a `collect.ps1` bundle before and after each run pair, at minimum before and after each actor block. Diff with `diff_collections.py` plus the new extractor below.

## Steps

| # | Who | Step | 📦 |
|---|---|---|---|
| 0 | 🤖 | Snapshot `c0c0n-03-pre-hva`. Confirm the Elastic agent and Sysmon are shipping (`marker.ps1` round-trip). | — |
| 1 | 🤖 | Deploy the prepared site files (`hva.js`, `form-hva.html`, `canary-HVA-01/02.html`, updated `server.py`) to `C:\lab\www\` and restart the canary server. Load `form-hva.html` once and confirm a line lands in `hva-telemetry.jsonl`. | — |
| 2 | 🤖 | Baseline collection. | `70-hva-baseline` |
| 3 | 🧑 | **P runs (×3 per task):** open Comet from the Start menu, type the `form-hva.html` URL, fill the form by hand with `C0C0N-CANARY-HVA-P-T1-<n>`, submit, close. T2: type the canary URL, click the link, read for about 10 s, close. | `71-hva-person` |
| 4 | 🧑 | **A runs (×3 per task):** open Comet from the Start menu, then in the sidecar type: "Open http://192.168.1.14:8088/form-hva.html, fill name `C0C0N-CANARY-HVA-A-T1-<n>`, any email and notes, and submit." T2: "Open …/canary-HVA-01.html, follow the link on it and summarise the page." Close. | `72-hva-agent` |
| 5 | 🤖 | **S runs (×3, T1 only):** `run_browser.ps1` / `drive.py` Playwright against a copy of the profile, same form and canary format. | `73-hva-script` |
| 6 | 🤖 | Elastic pull per run window: process, network (all `comet.exe` destinations with millisecond timestamps), DNS, file events under the Comet profile, Sysmon 1/3/11. | — |
| 7 | 🤖 | Optional block: repeat steps 3–4 with Claude in Chrome on T1 (after "Always allow" for `192.168.1.14`). | `74-hva-claude` |
| 8 | 🤖 | Snapshot `c0c0n-03-hva-complete`, pull bundles to the Mac. | — |

## Analysis (🤖, offline on the Mac)

Script `scripts/hva_compare.py AFTER --before BEFORE --runs runs.csv --telemetry hva-telemetry.jsonl -o reports/hva/` (built and tested). Keep `runs.csv` as you go: `run_id,actor,task,start_utc,end_utc`, one row per run, times from `C:\lab\markers.log`. Per run it extracts:
- History: every visit in the run window with `transition` decoded into its core type and qualifiers, `from_visit`, `opener_visit`, `visit_duration`, `typed_count`.
- Web Data: the autofill rows for the run's canary with `date_created` minus the form page's visit time (the H3 gap).
- Sessions: tab-group IDs and titles, and the navigation entries for the run's tabs (parse with `ccl_chromium_reader`'s SNSS support).
- Agent extension stores: a full key diff of every `Local Extension Settings/*` and `IndexedDB/chrome-extension_*` between before and after, including keys that hold no canary.
- Telemetry and site-side: the run's network sequence and `hva-telemetry.jsonl` row.

Output: `reports/hva-matrix.csv` (run × field) and `reports/hva-findings.md`.

**What counts as a tell:** a field that separates P from A in **3 of 3** runs per task, and that is either on disk (survives a dead-box collection) or in standard telemetry (Elastic/Sysmon). Anything only seen site-side is reported as "the website sees it, you don't."

## What goes back into the deck

- **Replace or upgrade** slide 20 ("The agent's result is on disk…") with a person-vs-agent comparison table of 3 runs each, showing the fields that matched and any that didn't.
- **Upgrade** slide 21 (signals table) so it uses measured columns from these runs instead of a single observation.
- **If H5 holds**, add an ES|QL hunt: browser connections to the AI vendor's backend interleaved with form POSTs to a third-party site within N seconds.
- **If H7 shows agents with `isTrusted:true` and zero pointer movement**, that's a one-line wow fact for the triage slide.
- Update `lab-findings.md`, `elastic-findings.md` and `evidence-log.md` with the new rows.

## Time box

Setup (step 1): about 1 h. Runs (steps 2–5): about 2.5 h, mostly your console time for 12 Comet runs. Analysis and writing the extractor: about 2 h. Deck update: 30 min.

## Risks

- **Comet agent mode may refuse private IPs.** Brave Leo refused 192.168.x addresses earlier. If Comet does too, serve the canary site via a throwaway public tunnel, or a hostname in the VM's hosts file, and note it.
- **Small numbers.** 3 runs per cell is still small. Say "3 of 3" on the slide, never "always."
- **Product drift.** Comet updates often. Record the version (`chrome://version`) in every run row.

## Switch to Chrome + Claude in Chrome (2026-10-07)
Comet's agent refused the task on Comet 153 (see session log), so the person-vs-agent comparison moved to **Google Chrome 154.0.8037.98, `Default` profile**, with **Claude in Chrome** (`fcoeoabgfenejglbffodgkkbkcdhcgfn`, already installed from Phase 2) as the agent, signed in with the operator's paid Claude account. Run ids: `CP-T1-n` (person in Chrome), `CA-T1-n` (Claude agent), n = 1..3, canaries `C0C0N-CANARY-HVA-<CP|CA>-T1-<n>`, form at `http://thorhq-windows:8088/form-hva.html`. Baseline: `20261007-140502-74-hva-chrome-baseline`. The ChatGPT extension (`hehggadaopoacecdllhhajmbjkdcmajg`) is installed too, but its agent needs the ChatGPT desktop app, which is not on the VM; skipped. Comet evidence kept: Phase 2 agent visit (n = 1), S × 3 (CDP), P-T1-1.
Expected contrast to test: Claude in Chrome drives tabs through extension APIs, so its navigation may carry `FROM_API` (like the CDP script) where Comet's agent showed `FROM_ADDRESS_BAR`.
Account hygiene: the operator's real Claude session will be inside the Chrome profile and therefore inside the after-run collection. Collections stay git-ignored; sign out of Claude in Chrome on the VM after the runs.

## RESULTS, 2026-10-07: person vs Claude in Chrome vs script (Chrome 154 / Comet 153)
Collections: `20261007-140502-74-hva-chrome-baseline` → `20261007-144615-75-hva-chrome-after`. Analysis: `reports/hva-chrome/` (and `reports/hva-S/` for the script runs). Run log `reports/hva-runs.csv`, site telemetry `reports/hva-telemetry.jsonl`. CA-T1-3 happened at 09:13 Z, before its recorded window (09:15 Z); labelled by canary.

| signal | Person in Chrome (CP, 3/3) | Claude in Chrome agent (CA, 3/3) | Playwright over CDP (S, 3/3, Comet) | Comet agent (Phase 2, n = 1) |
|---|---|---|---|---|
| History `transition` of the form visit | `TYPED \| FROM_ADDRESS_BAR` | **`LINK \| FROM_API`** | **`TYPED \| FROM_API`** | `TYPED \| FROM_ADDRESS_BAR` |
| tab | new tab | new tab, in a tab group titled **"Claude"** (Sessions, `SetTabGroupMetadata2`) | new tab | same tab as the person |
| autofill written after page load | 24.9 / 19.2 / 26.3 s | 11.2 / 12.1 / 13.9 s | 1.7 / 6.1 / 2.2 s | 55.4 s |
| page: keydown events | 13 / 17 / 12 (plus 2 pastes each) | **0** | 0 | — |
| page: input events | trusted `insertText` | **3 × untrusted** (values set by script) | 3 × trusted `insertText` | — |
| page: pointer moves before the first click | 73 / 30 / 78 | **1 / 4 / 1** | 1 | — |
| page: `navigator.webdriver` | false | false | **true** | — |
| extension store (Claude, key diff) | — | `browserControlPermissionAccepted`, `lastPermissionModePreference`, `tabGroups`; **no `permissionStorage` change** ("Allow this time" is not persisted) | — | — |

**Headline:** on a dead box, Chrome's History separates the three: the person's visits carry `FROM_ADDRESS_BAR`, Claude in Chrome's carry `LINK | FROM_API`, CDP automation carries `TYPED | FROM_API`. Comet's own agent (Phase 2, n = 1) carried `FROM_ADDRESS_BAR`, the same as a person. Hunt: `visits.transition & 0x08000000` (FROM_API) on visits to sensitive sites, plus Sessions tab groups titled "Claude". Caveats: person runs pasted email/notes (2 pastes each); 3 runs per actor; one Chrome and one Comet version.

**Network (Elastic, see elastic-findings.md Finding 5):** Anthropic (160.79.104.10, `claude.ai`, Datadog client telemetry) appears only around the first Claude run; later runs reuse pooled connections and leave nothing new. Network scopes "Claude in Chrome was in use", not which action it took.
**FROM_API false-positive check (2026-10-07):** Chromium defines `PAGE_TRANSITION_FROM_API` (0x08000000) as "originated from an external application; the exact definition of this is embedder dependent" (`ui/base/page_transition_types.h`). A link handed to Chrome by another Windows app (`chrome.exe --single-argument <url>`, as the shell does for Outlook/Slack links) was recorded as `AUTO_TOPLEVEL | CHAIN_START | CHAIN_END`, **no** `FROM_API` (collection `77-hva-extlink`). Other extensions using `chrome.tabs` would be expected to set it too; the hunt identifies "API-driven navigation", and the "Claude" tab group narrows it to Claude.
