# Lab Findings — Windows 11 (THORHQ `thorhq-windows`)
Original research for "The AI Browser Blind Spot" (c0c0n 2026). Every row below was observed on the lab VM; collection bundles in `collections/`, unpacked artifacts in `artifacts/`. VM snapshots: `c0c0n-00-baseline-clean` → (more added per phase).

Environment: Windows 11 26200.9168, user `thorh` (local admin), Elastic Agent + Elastic Defend + Sysmon64 → Elasticsearch 192.168.1.27. Marker events: Application log, source `C0C0NLAB`, EIDs 900/901 (collect start/end), 902 (manual marker).

## Phase 0 — Instrumentation (2026-09-17)
- Telemetry confirmed flowing: `endpoint.events.{process,file,network,registry,library,api,security}`, `windows.sysmon_operational` EIDs 1,2,3,5,7,8,10,11,12,13,15,17,22,26,29, `system.security` incl. **4663 object access** (file reads are auditable on this box — rare in the field, note as lab advantage).
- Tooling at `C:\lab\tools`: Python 3.12.7, MinGit, `ccl_chromium_reader` (master), `pyhindsight` 2026.06, Playwright. Collector `C:\lab\scripts\collect.ps1` (FS listings, registry exports, hives, Prefetch, Amcache/SRUM/WebCache via `esentutl /vss`, live state, native-messaging hosts, browser profiles via VSS shadow + robocopy). Baseline bundle: `20260917-135714-00-baseline`.

## Phase 1 — Install wave

### Chrome 153.0.8010.48 (control) — `googlechromestandaloneenterprise64.msi /qn` → `C:\Program Files\Google\Chrome\Application\`. Bundle `20260917-140600-10-chrome-installed`.

### Perplexity Comet 152.0.7977.199 — installed 2026-09-17 14:08 IST
**Acquisition**
- `https://www.perplexity.ai/rest/browser/download?platform=win_x64&channel=stable` → 302 → **Cloudflare R2**: `https://pplx-browser-binaries.a0adf9b772aecba4fa8883581f3c9180.r2.cloudflarestorage.com/152.0.7977.199/comet_latest_intel_system.exe?X-Amz-…` (presigned, 1 h expiry). Note `_system` = machine-level installer is what the public endpoint serves by default.
- Installer: 233,806,568 bytes, SHA-256 `B27496E3ABE165C5029201607A4619DAC856A991926D1DE92058A093E7A0B985`, `OriginalFilename=UpdaterSetup.exe`, `ProductName=Comet Installer (x64)`, Authenticode valid, signer `CN="PERPLEXITY AI, INC."` (**cert E= field carries an individual employee email**), SERIALNUMBER=6909743.
- Silent switches that worked: `--install --silent` (exit 0). Spawns nothing visible; leaves two `updater.exe` processes.

**Install fingerprint (machine-level)** — contradicts published research that puts Comet under `%LOCALAPPDATA%`; that is the per-user installer variant.
| Artifact | Value |
|---|---|
| Browser | `C:\Program Files\Perplexity\Comet\Application\comet.exe` (4,422,528 B, signed PERPLEXITY AI, INC.), `chrome_proxy.exe`, `chrome.VisualElementsManifest.xml`, `SetupMetrics\*.pma` |
| Version dir | `…\Application\152.0.7977.199\` — `chrome.dll` (302 MB), `chrome_elf.dll`, `elevation_service.exe`, `elevated_tracing_service.exe`, `notification_helper.exe`, `import_assistant.exe`, `chrome_pwa_launcher.exe`, `Installer\setup.exe` (+ `chrmstp.exe`, identical size), `default_apps\`, `Extensions\external_extensions.json` (empty map), `language_detector.tflite` |
| Updater | `C:\Program Files (x86)\Perplexity\CometUpdater\152.0.7977.199\updater.exe` (+ `Crashpad\`), `…\CometUpdater\crx_cache\`, `C:\Program Files (x86)\Perplexity\Update\` |
| **Services (auto)** | `CometUpdaterService152.0.7977.199` → `updater.exe --system --windows-service --service=update`; `CometUpdaterInternalService152.0.7977.199` → `--service=update-internal` |
| **Service (manual)** | `CometElevationService` → `elevation_service.exe` — **App-Bound Encryption elevator is present** (resolves the "does Comet do ABE?" unknown; confirm `os_crypt.app_bound_encrypted_key` in `Local State` after first run) |
| Registry | `HKLM\SOFTWARE\WOW6432Node\Perplexity\Update\{Clients,ClientState,ClientStateMedium}\42e10078-e377-4166-965f-c14ad958a146` (Comet app GUID; `name=Comet`, `pv`, `UninstallString`, `InstallerSuccessLaunchCmdLine="…\comet.exe" --from-installer`, `Commands\on-os-upgrade`); updater GUIDs `{A6B9C7D4-8E9F-4A6B-9C8D-9F8A6B9C7D5E}`, `{D9E5A6B7-F2C3-4E8F-A0B1-5C6D7E8F9A0B}`; `HKLM\SOFTWARE\WOW6432Node\Perplexity\Update\UninstallCmdLine = "…updater.exe" --wake --system`. No `HKLM\SOFTWARE\Perplexity` (64-bit view) key. |
| Uninstall entry | `HKLM\…\Uninstall\Perplexity Comet`: DisplayName `Comet`, Publisher **`The Comet Authors`**, `InstallLocation=C:\Program Files\Perplexity\Comet\Application`, `UninstallString="…\152.0.7977.199\Installer\setup.exe" --uninstall --system-level` |
| Processes post-install | 2× `updater.exe` (PIDs 6132, 6520) |

**Bundled ("hidden") extensions** — mechanism is Chromium *external extensions*: `…\152.0.7977.199\default_apps\external_extensions.json` maps ID → CRX; installed into the user profile on first run.
| ID | CRX (sha256) | Name / version | Notable |
|---|---|---|---|
| `npclhjbddhklpbnacpjloidibaggcgon` | `agents.crx` (d62cdee7…49e75, 1.3 MB, 60 files) | **comet-agent** 0.0.226, MV3 | perms: `debugger`, `webRequest`, `webNavigation`, `cookies`, `history`, `sessions`, `tabs`, `scripting`, `storage`, `offscreen`, `nativeMessaging`, `clipboardRead/Write`, `downloads`, `downloads.ui`, `tabGroups`, `declarativeNetRequestWithHostAccess`, `file://*/`; host `<all_urls>`; content scripts `content.js` + `events.js` on `<all_urls>`, `google_docs_cs.js` on docs.google.com; `overlay.{html,js,css}`, `pdf_worker.js`, `offscreen.html`; `managed_schema.json` = `BlockedDomains[]`, `OrganizationUUID`; `externally_connectable` from perplexity.ai/.com (+testing/staging); `update_url=https://www.perplexity.ai/rest/browser/update-crx?channel=stable`; `OWNERS.yaml` |
| `mcjlamohcooanphmebaiigheeeoplihb` | `perplexity.crx` (0bed42cf…c12, 0.9 MB) | **Comet** 1.0.80, MV3 | perms: `debugger`, `identity`, `processes`, `proxy`, `management`, `settingsPrivate`, `contentSettings`, `search`, `bookmarks`, `history`, `sessions`, `cookies`, `webRequest`, `unlimitedStorage`, `declarativeNetRequest{,Feedback,WithHostAccess}`, `notifications`, `idle`, `alarms`; hosts `*://*/*`, `file://*/*.pdf`; content script on Chrome Web Store; ships `_sentry-release-injection-file` |
| `mjdcklhepheaaemphcopihnmjlmjpcnh` | `comet_web_resources.crx` (54 MB) | **Comet Web Resources** 2026.6.29.323 | no perms; web-accessible `sidecar/*`, `spa/*`, `voice-assistant/*`, `inline-assistant/*` to `https://www.perplexity.ai/*` — the assistant UI is served *from the extension* into the perplexity.ai origin |

(On the speaker's macOS Comet 145 profile, `Local Extension Settings/` holds `mcjlamohc…`, `npclhjbdd…` and a third ID `ahfpelljbenimhohmgdbgpcgmmahcbkn` not present in the v152 Windows bundle — version drift; to check.)

**Endpoints / SDKs found statically in the extensions**
- Telemetry: `https://irontail.perplexity.ai/v1/bulk/event`, `https://www.perplexity.ai/rest/event/analytics`, Datadog RUM (`www.datadoghq-browser-agent.com`, `www.datad0g-browser-agent.com`), Sentry, **Eppo** feature flags (`fscdn.eppo.cloud`, `fs-edge-assignment.eppo.cloud`), CloudFront asset hosts `d3uc069fcn7uxw.cloudfront.net`, `d20xtzwzcl0ceb.cloudfront.net`.
- Product: `https://www.perplexity.ai/rest/browser/update`, `https://suggest.perplexity.ai/search/v3/navigate`.
- **Private API surface `chrome.perplexity.*`** (v152): `mcp.{addStdioServer,removeStdioServer,updateStdioServer,getStdioServers,getTools,callTool,…}` (still present after SquareX disclosure), `dxt.{install,uninstall,getInstalledPackages,requestPermission,hasPermission}` (desktop-extension packages → explains the `Default\dxt` profile dir), `system.{getMachineId,getInstallationId,getHistograms,getStartupMetrics,getUserCountry,isPerplexityDefaultBrowser,getChannel}`, `signature.signPayload`, `views.{createWebOverlay,loadUrlInWebOverlay,…}`, `sidecar.{open,close}`, `blacklist.isDomainInBlacklist`, `features.getFlagValue`, `analytics.recordEvent`, `pdf.getText`, `inlineAssistant.*`, `mission`, `explanation`, `themes`, `update.FailureReason`.

**Updater persistence & its own forensic log (Chromium open-source updater, "Omaha 4" protocol)**
- Scheduled task `\PerplexitySystem\CometUpdater\CometUpdaterTaskSystem152.0.7977.199{B60D0A74-2E0B-4750-AF0F-117B5BACB5FC}` (file under `C:\Windows\System32\Tasks\PerplexitySystem\CometUpdater\`).
- `C:\Program Files (x86)\Perplexity\Update\PerplexityUpdate.exe` (copy of updater.exe, 9,590,656 B) — the "legacy" entry point; `…\CometUpdater\152.0.7977.199\uninstall.cmd`.
- **`C:\Program Files (x86)\Perplexity\CometUpdater\updater_history.jsonl`** — every updater process START/END with full command line, PID/parent PID, `scope`, `processToken`, WebKit-epoch `timestamp` (µs since 1601), `deviceUptime`; `ACTIVATE`, `LOAD_POLICY` (shows `LastCheckPeriod` default), `PERSISTED_DATA` (registered app IDs), and **`POST_REQUEST` with base64 request + response bodies**. Decoded update-check request carries `domainjoined`, `ismachine`, `hw.physmemory`, CPU flags, `os.version` (10.0.26200.9457), `installsource: offline`, `requestid`, `sessionid`. Response `)]}'` + JSON `updatecheck.status`. Also `updater.log` (69 KB verbose) and `prefs.json` (`last_checked`, `last_started`, `server_starts`, registered apps). Installer temp path pattern: `C:\WINDOWS\SystemTemp\Perplexity<pid>_<rand>\bin\updater.exe --install --silent --install=appguid={42e10078-…}&appname=Comet&needsadmin=true --offlinedir={guid}`.
- Crash telemetry: `updater.exe --crash-handler --url=https://o4504136533147648.ingest.us.sentry.io/api/4510911807750144/minidump/?sentry_key=<redacted>` with `updater.log` + `updater_history.jsonl` **attached to every crash report** — i.e. the updater history ships to Sentry on crash.
- Timeline from the log: services first started 2026-09-17 08:39:34 UTC (install), restarted 08:51:30 UTC (`--wake --system`) — updater wakes periodically even before the browser has ever run.
- Install delta vs Chrome baseline (`reports/delta-10-to-11-comet.md`): +128 files (92 under `Program Files\Perplexity\Comet`, 14 under `CometUpdater`), +3 services, +1 scheduled task tree, +1 Uninstall entry. No `%LOCALAPPDATA%` footprint yet (browser not launched).

Bundle: `20260917-141235-11-comet-installed`. Unpacked CRXs: `artifacts/comet-crx/`. Delta report: `reports/delta-10-to-11-comet.md`.

### Brave — DEFERRED: both the online and standalone-silent installers hang inside `BraveUpdate.exe` (Omaha) when launched from a non-interactive SSH/SYSTEM session — no log, no progress, killed after 10+ min twice. Install interactively at the console during Phase 2 (E2).

## Phase 2 (partial, from SSH session 0) — Comet first run & canary drive

### A1 — Comet first run (headed, session 0, 60 s) → bundle `20260917-230902-20-comet-firstrun`
- **`--headless=new` exits immediately** (0 processes after 90 s, no profile created). Headed launch works even without a desktop session (11 processes).
- Profile root `%LOCALAPPDATA%\Perplexity\Comet\User Data\` (248 MB after first run). Root additions vs Chrome: **`piid`** (plain-text install UUID `00000000-dfcc-444c-b44a-54da7839f236` — the `chrome.perplexity.system.getInstallationId` value), `ActorSafetyLists`, `CaptchaProviders`, `AmountExtractionHeuristicRegexes`, `hyphen-data`; `Local State` gains a top-level **`perplexity`** object (`adblock.*_last_update`, `crashed_during_startup`, `per_profile_account_info_mapping`, **`features`** = base64(gzip(JSON)) cache of **157 Eppo feature flags**).
- `Default\` additions: `adblock`, **`dxt`** (desktop-extension packages), `Extension Rules/Scripts/State`, `Sync Extension Settings`, `Google Profile.ico`. **No `Sessions\` directory** was created in either run.
- Bundled extensions are installed into `Default\Extensions\<id>\<ver>_0\` on first run and recorded in `Secure Preferences` as `location=1` **`from_webstore=true`** (they never came from the store). Component extensions (location=5, loaded from `Application\152.…\resources\`): **`ahfpelljbenimhohmgdbgpcgmmahcbkn` = "Dark Reader (Comet)" 4.9.111.13** (`settingsPrivate`, `*://*/*`), Chromium PDF Viewer, Google Hangouts. → resolves the unknown 3rd ID seen on the macOS profile.
- `Local Extension Settings\`: Dark Reader writes 24 config records on install; `mcjlamohc…` (Comet) writes `ppxl_scheduler-history = {}`; `npclhjbdd…` (comet-agent) writes **`asi_relay_restart_boundary` = epoch-ms** on each launch (and tombstones the previous value → a launch timeline recoverable from LevelDB tombstones).
- `Preferences`: `perplexity.adblock.daily_*_request_counts[30]`, adblock exceptions for `[*.]perplexity.ai` and **`[*.]perplexity.omniapp.co`**; Chromium sync data types `perplexity_workspace` and **`gemini_thread`** present (upstream glic sync type compiled in).
- Feature flags worth quoting (`Local State.perplexity.features`): `luna-ai`, **`luna-computer-enabled`**, `browser-agent-qwen35vl-precompaction-enabled`, `comet_native_messaging`, `comet_remote_control_window_hours`, `enable-local-mcp-user-approval`, `enable-dxt`, `enable-enterprise-telemetry`, `auto-fetch-tab-content`, `hide-screenshots-in-sidecar`, `nav-logging-add-urls-prefixes`, `native-analytics`, `browser-analytics-event-blacklist`, `external-search-*` (Google-SERP scraping: `External-Search-Lynx-Selectors` CSS selectors, `external-search-lite-user-agents`, `external-search-anonymity`), `google-docs-inline-assistant-enabled`, `help-me-with-text-*`, `mx-sdk-soniox-stt-model`, `adblock-whitelist` (pre-exempts datadog, sentry.io, snowplow.io, browser-intake-datadoghq.com, stripe, facebook, x.com …).
- **`os_crypt` is empty** after both runs: ABE key creation fails in a non-interactive session (Chrome control run logged `app_bound_encryption_provider_win.cc:102 Unable to encrypt key … 0x8004A005 GetLastError: 5` → `Encryption is not available`). Cookie/password artifacts therefore need an interactive desktop session.

### A1b — Playwright drive of Comet (extensions left enabled) → bundle `20260917-231302-21-comet-after-canary`
- **UA/Client Hints observed first-hand:** `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36`; `navigator.userAgentData.brands` = `Chromium 152 / Not?A_Brand 24 / Google Chrome 152`. Web-server access log shows the same — no Comet token anywhere.
- Canary residue: `Default\Local Storage\leveldb\000003.log` (`c0c0n_canary = C0C0N-CANARY-COMET-01-LS`) and `Default\IndexedDB\http_192.168.1.14_8088.indexeddb.leveldb\000003.log` — both **only in the LevelDB write-ahead `.log`**, no `.ldb` yet: an examiner who copies only `*.ldb` gets nothing.
- **History stayed empty** (file mtime unchanged) — Chromium's History write did not occur in the session-0 Playwright run; force-kill on the first run left `History-journal` (hot journal, 0 rows committed). Re-test in the interactive session before drawing conclusions.
- Form POST reached the canary server: `name=C0C0N-CANARY-COMET-FORM` with the Chrome UA — proves the server-side log is the only place a *scripted* submission is distinguishable from a human one (by timing/UA join), not by the browser artifacts.

### Session-0 limits hit (why the rest moves to the console)
Omaha-based installers (Brave) hang; ABE cannot mint keys (no cookies/passwords persisted); Playwright close hangs on Chrome; no `Sessions\` written. Next: user logs in at the VMware console as `thorh`, then automation runs *inside* that session via `schtasks /IT`.

## Phase 2 — interactive session (2026-09-20, user logged in at console)

### Comet after Perplexity sign-in (live VSS collection while Comet was running) → bundle `20260920-114121-22-comet-live`
- **ABE confirmed.** `Local State.os_crypt` now holds `app_bound_encrypted_key` (`APPB…`), `encrypted_key` (`DPAPI…`) and `audit_enabled=true` — minted only once a real desktop session existed (session-0 attempts logged `app_bound_encryption_provider_win.cc:102 … 0x8004A005`). Comet cookies/passwords are therefore ABE-protected exactly like Chrome 127+; dead-box decryption needs the `CometElevationService` COM path (ChromElevator has no Comet target yet).
- **Sign-in creates a second Chromium profile.** `Profile 1` appeared at sign-in; both profiles are named `thorhq` in `Local State.profile.info_cache`; `last_used = Profile 1`. `Local State.perplexity.per_profile_account_info_mapping[<profile path>] = {email, id, image}` — each value **`v20`-prefixed = ABE-encrypted**. So the account identity *is* on disk in `Local State`, but only readable with the live elevation service.
- **History captures the whole OAuth dance** (Profile 1): `accounts.google.com/o/oauth2/v2/auth … client_id=60244564555-30175ip7vg79fobh0rk1sur3pdutj9l1.apps.googleusercontent.com` → Google "Verify it's you" challenge pages → `www.perplexity.ai/api/auth/callback/google?…&code=[OAUTH-CODE-REDACTED] (**authorization code persisted in History**) → `www.perplexity.ai/onboarding?pplx_account=[ACCT-UUID]` (**Perplexity account UUID persisted in History**). Default's History stayed at 0 rows through all runs (only journal writes) — Comet appears to route the signed-in user to Profile 1 and leaves Default idle.
- **Bundled extensions self-updated in the interactive session** (`comet-agent` 0.0.226→0.0.227, `Comet` 1.0.80→1.0.82; `Default\Extensions\<id>\<ver>_0`) via `/rest/browser/update-crx` — artifact versions drift within days; `Managed Extension Settings\` appeared (enterprise blocklist channel).
- **Sessions (SNSS)**: `Default\Sessions\Session_13434357530639225` (10 KB) and `Profile 1\Sessions\Session_13434357550302903` (230 KB) — tab/navigation state incl. the OAuth URLs; absent in every session-0 run.
- **perplexity.ai IndexedDB is a per-account REST cache, not a chat store** (`ccl_chromium_indexeddb`):
  - `keyval-store` → store `keyval`, keys `["pplx-query-cache-3dbbae4","/rest/<endpoint>",…]` caching JSON responses: `/rest/billing/asi-access-decision` (`can_use_computer:false`, `is_out_of_credits`, `budget_type:"free_turn"`), `/rest/billing/ubb-config` (credit/refill config), `/rest/sources` (connector catalogue), `/rest/visitor/information`, `/rest/academic/check-edu-institution`, `/rest/homepage-widgets/upsell`.
  - After sign-in: **`pplx-query-cache-<account-uuid>`** and **`eppo-sdk-<account-uuid>`** databases (720 flag records) alongside the anonymous `eppo-sdk` (1440) — the **account UUID is embedded in IndexedDB database names**, giving user attribution from a directory listing. `/rest/onboarding/computer-v2` cached the connector list offered (Gmail+Calendar, Outlook, Drive, Notion, GitHub, Slack, Dropbox, SharePoint, Box, Sheets, Excel, Slides, Docs, Teams, Asana, Jira, Snowflake).
  - No thread/conversation records exist yet (no chats run) — to re-check after A3.
- Profile size 566 MB after sign-in (248 MB after first run).

### Block 1 — Comet after 3 assistant chats + agent task (bundle `20260920-133549-23-comet-after-chat-live`)
**Comet's "server-side" conversation is cached locally after all.** `Profile 1\IndexedDB\https_www.perplexity.ai_0.indexeddb.leveldb` store `keyval` (`keyval-store`, now 100 records) holds, in cleartext JSON:
- `["pplx-query-cache-…","thread_latest_entry","<backend_uuid>"]` and `["…","all_results","<backend_uuid>"]` → the **full prompt text** (`query_str` = "Remember that my project codename is C0C0-CANARY-COMET-02" — typed without the N; verified against raw LevelDB bytes 2026-09-26, 277 occurrences), **thread_title**, `backend_uuid` (thread id `3e3e71d3-4cdc-4e5b-ad7d-157b9b210a4b`), `query_source`, status. So the assistant query is recoverable from disk even though Perplexity stores the thread server-side.
- `["…","/rest/thread/list_recent","<user-email>"]`, `["…","/rest/rate-limit/all"]`, `["…","/rest/tasks/shortcuts/mentions"]` (built-in "teach-me-comet" task prompt) — and the **account email is embedded in cache keys**.
- Assistant `query_str` also lands in **`Local Storage\leveldb`** and the IDB `.log`.
- **Comet `Profile 1\History` (real session) recorded the whole activity trail**: `canary-COMET-01.html` (Project Ostrich), the `secret-COMET-03.txt` open (the "exfil" doc), `Form.html`, `POST /submit` — i.e. even the pasted-secret workflow leaves a History row here (contrary to the CFP's "queries not logged in History"; the *pages the user opened around the assistant* are).
- **`Profile 1\Web Data` autofill** stores the agent-mode form values `name=C0C0N-CANARY-COMET-04`, `email=comet04@lab.local` with created/last-used timestamps — the agent's form submission is autofilled and persisted like a human's.
- Agent-mode form POST reached the canary server with the stock Chrome UA (`name=C0C0N-CANARY-COMET-04`) — server log is again the only place to time-correlate it.
- Note: the free account is `is_out_of_credits / budget_type:free_turn` and `can_use_computer:false`, so agent mode ran in a limited tier; queries showed `status:PENDING` in cache (answer streamed but the *prompt* persisted regardless).

### Block 2 — Brave Leo (bundle same, Brave profile) — the one local conversation DB, confirmed on Windows
- **`Default\AIChat` SQLite** exists (94 KB) with tables `conversation`, `conversation_entry`, `associated_content`, `conversation_entry_event_{completion,search_queries,web_sources,tool_use,inline_search}`, `conversation_entry_uploaded_files`, `ai_chat_sync_metadata`.
  - `conversation`: rows with `uuid`, `model_key`, `total_tokens`, `title` **BLOB (encrypted)**.
  - `conversation_entry`: cleartext **`date`** (2026-09-20 07:59–08:01), **`character_type`** (0=human / 1=assistant), **`action_type`**, **`model_key` = `chat-qwen`** (the actual model leaks in the clear), token counts; `entry_text` is a BLOB whose first bytes are hex `76 31 30` = **`v10`** → OSCrypt-encrypted with the same key class as cookies. So the *timeline, model, turn structure and token counts are recoverable without any key*; only the message text needs the OSCrypt/DPAPI/ABE key.
- **`Default\Preferences` → `brave.ai_chat.user_memories` = `["my codename is C0C0N-CANARY-BRAVE-02"]` in PLAINTEXT** — the memory feature writes to prefs unencrypted (matches the source-code finding, now confirmed on a real box). Also `last_accepted_disclaimer`, `user_dismissed_storage_notice`.
- Confirms the matrix: six of seven keep chat server-side; **Brave is the exception with a local DB, and it leaks the timeline in clear even though it encrypts the text — and leaks memories entirely in clear.**

### Data-handling note for our own slides
Comet signup stored the operator's **real phone/email in `Web Data` autofill** (`identifier`, `phoneNumberId`) — redacted in all committed reports; analysis scripts now scrub `+91…`, 10-digit numbers, and the throwaway address before anything is quoted on a slide.

## Headless deep-dive (2026-09-20) — decryption + Brave install fingerprint

### Credential-encryption contrast (decryptor run as `thorh` on the box, `chromium_decrypt.py`)
- **Brave 153.1.95.104 = classic v10 OSCrypt, no App-Bound Encryption.** `Local State.os_crypt` has only `encrypted_key` (DPAPI-wrapped) + `audit_enabled`; **no `app_bound_encrypted_key`**. The AES-256 key unwraps with a single user-DPAPI `CryptUnprotectData` call — i.e. Brave's Leo DB and cookies are **dead-box decryptable** from a disk image + the user hive, no elevation service needed.
- **Comet 152 = full App-Bound Encryption (v20).** All **81** `Network\Cookies` rows are `v20`; DPAPI-only decryption fails on every one. Recovery needs the live `CometElevationService` COM path (or a ChromElevator-style bypass, which has no Comet target today). Same posture as Chrome 127+/Edge.
- **Even undecrypted, Comet cookie *names* (cleartext columns) leak state**: `__Secure-pplx.session.<account-uuid>` (session cookie **named with the Perplexity account UUID**), `pplx.browser.always-allow-browser-agent`, `pplx.browser.device-id`, `pplx.browser.is-local-search-enabled`, `pplx.browser.temporary-threads-enabled`, `comet_browser` (on both perplexity.ai and perplexity.com), `__stripe_mid`, `next-auth.session-token`, `singular_device_id` → account identity, agent-permission and device-id all inferable from a listing.

### Brave Leo `AIChat` fully decrypted (the money demo)
Decrypting `conversation_entry.entry_text` (v10) recovered the **verbatim conversation**:
- HUMAN "What is C0C0N-CANARY-BRAVE-01?" → ASSISTANT (`model=chat-qwen`) "I don't have specific information about **C0C0N-CANARY-BRAVE-01**…"
- HUMAN "summarize http://192.168.1.14:8088/canary-BRAVE-01.html" → ASSISTANT "I cannot access local network addresses…"
- Conversation `title` (also v10-encrypted) → "C0C0N CANARY BRAVE Device Information".
So Brave Leo yields **full prompt+response text, model name, per-turn timestamps and title** from a disk image with only the user's DPAPI key — the strongest "AI chat recovered from disk" demo in the set. (`brave.ai_chat.user_memories` was already plaintext in Preferences.)

### Brave install fingerprint (per-user, Omaha-style updater)
| Artifact | Value |
|---|---|
| Browser | `%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe` 153.1.95.104, Publisher "Brave Software Inc" |
| Updater | `%LOCALAPPDATA%\BraveSoftware\Update\BraveUpdate.exe` (v1.3.361.151) — **per-user, no Windows service** (unlike Comet's 3 machine services) |
| Scheduled tasks | `\BraveSoftwareUpdateTaskUserS-1-5-21-…-1001Core{C8CA5C04-…}` and `…UA{35A1D458-…}` (per-SID Core + UA pair) |
| Registry | `HKCU\SOFTWARE\BraveSoftware\Update\Clients\{…}`: `name=Brave`, `pv=153.1.95.104`, `ap=release`, `LastInstallerSuccessLaunchCmdLine="…\brave.exe" --from-installer`, `Commands\on-os-upgrade`, `DowngradeCleanupCommand`; **`google.services.last_username` / `last_signed_in_username` stored as SHA-256 hashes** (not plaintext). |
| Uninstall | `HKCU\…\Uninstall\BraveSoftware Brave-Browser` → `setup.exe --uninstall` |
| Contrast with Comet | Brave = **per-user** (HKCU, user scheduled tasks, no service, no ABE); Comet = **machine-wide** (HKLM updater keys under WOW6432Node\Perplexity\Update, 3 machine services = 2 auto updater + 1 on-demand `CometElevationService`, ABE). Two different Chromium-updater deployment models to fingerprint. |

## Scope decision (2026-09-20): no destructive ops
Per operator instruction, **no clear-browsing-data / uninstall / carve** is performed on the VM or the Mac (Mac Claude/GPT are production tools; VM is resettable but not worth it). Those two talk points are sourced from public documentation instead:
- "Extension storage survives *Clear browsing data*" — Chrome developer docs (chrome.storage: persists across cache/history clears; removed only on uninstall).
- "Uninstall leaves carvable LevelDB `.ldb` residue (magic `57 fb 80 8b 24 75 47 db`)" — forensics.wiki LevelDB format; CCL.
Remaining lab work is **non-destructive only**: (1) Elastic telemetry pull for the recorded activity windows (agent-vs-human detection section), (2) optional Playwright "scripted control" browsing row, (3) read-only re-verify of Windows `NativeMessagingHosts` registry paths.

## Gap-closure pass (2026-09-20)

### L1 — Gemini-in-Chrome `glic` storage partition CONFIRMED (was INFERRED)
On a real Chrome profile: `Default/Storage/ext/glic/66A834677761/` exists (1.9 MB). `66A834677761` = first 12 hex of **SHA-256("glicpart")** (verified). It is a **separate StoragePartition** with its own `Cookies`, `Local Storage`, `Session Storage`, `SharedStorage`, caches — Local Storage origins are `gemini.google.com` + `accounts.google.com`. Prefs in `Default/Preferences` → `glic.{completed_fre,onboarding_status,partition_needs_cookie_sync,window,previously_not_allowed}`. **A DFIR tool that parses only `Default/` (History/Cookies/Local Storage) never opens this** — Gemini-in-Chrome's on-disk residue lives one directory level sideways, in a hash-named partition. (Also seen: `Storage/ext/nmmhkkegccagdldgiimedpiccmgmieda` = Google Docs Offline, non-AI.)

### L4 — Execution artifacts (Windows), from collected hives
- **Prefetch** (`C:\Windows\Prefetch`): **10 distinct `COMET.EXE-<hash>.pf`** and **7 `BRAVE.EXE-<hash>.pf`** (each hash = a unique full-path+command-line launch → normal vs headless vs agent vs scripted runs are separable), plus `COMET`'s `UPDATER.EXE-*.pf`, `BRAVEUPDATE.EXE-*.pf`, `BRAVE_INSTALLER-DELTA-X64.EXE.pf`, `BRAVESTANDALONESILENT.EXE.pf`. Prefetch captures AI-browser execution **immediately**.
- **Amcache** (`Amcache.hve\Root\InventoryApplicationFile`, 679 entries): **0** reference Comet/Brave/Perplexity — the appraiser (`Microsoft Compatibility Appraiser` scheduled task) had not ingested the days-old installs yet. Forensic nuance: **Amcache lags; Prefetch + EDR process telemetry are the timely execution evidence for AI browsers.**
- Hives/artifacts collected for offline parsing: `Amcache.hve`, `SRUDB.dat` (per-app network usage), `SYSTEM/SOFTWARE/NTUSER/UsrClass` hives, `WebCacheV01.dat` (Edge/IE metadata), Prefetch set — in each `execution/` bundle.

### L7 — native-messaging bridge is OS-specific
Windows VM: **no** `NativeMessagingHosts` registry entries under Chrome/Edge/Brave/Comet (desktop apps not installed) — on Windows, Comet's agent bridge is the *bundled extensions* in-browser, not a stdio native host. macOS (this Mac): `com.perplexity.comet`, `com.openai.codexextension`, `com.anthropic.claude_browser_extension` manifests all present (Comet.app / ChatGPT desktop / Claude.app installed). Triage implication: on macOS the `NativeMessagingHosts` JSON directory is a one-glance AI-agent-bridge inventory; on Windows you rely on the bundled-extension dirs + registry `Policies` + services instead.

### Extractor-surfaced extra: Comet built-in "Comet" extension holds local secrets
`extract_ai_browser_artifacts.py` over the collected profile flagged the built-in **Comet** extension (`mcjlamohc…`) chrome.storage.local (32–37 records) with sensitive-shaped keys **`key-pair`**, **`partners-tokens-v2`**, `partners-tokens-last-fetch` — a local key-pair and partner tokens persisted in extension LevelDB (values not inspected). Worth a slide line: the "hidden" Comet extensions don't just automate — they cache credential-shaped material locally.

### Deliverables authored (`deliverables/`)
`Comet.tkape`, `BraveLeo.tkape` (KAPE targets — none existed), `Windows.Applications.AIBrowsers.yaml` (Velociraptor artifact — none existed), `extract_ai_browser_artifacts.py` (cross-platform read-only AI-layer extractor; smoke-tested on the collected Comet+Brave profiles). Closes the "no tool covers AI browsers" gap and gives the talk a shippable artifact.

### Addendum 2026-10-06 — agent navigation is recorded as address-bar typing (n = 1)
Re-read of bundle `20260920-133549-23-comet-after-chat-live`, `Profile 1\History` (via `scripts/hva_compare.py`): the A4 agent task's visit to `http://192.168.1.14:8088/Form.html` (07:55:57 UTC; operator confirms the agent opened it, nobody typed it) has `transition` = `TYPED | FROM_ADDRESS_BAR | CHAIN_START | CHAIN_END`, `from_visit` 0, no `visit_source` row, same `tab_id` (63571932) as the operator's own typed visits, which include human URL typos (`SECRET-COMET-03.html`, `secret-COMET-03.html`). No `FROM_API` qualifier. The `/submit` visit is `FORM_SUBMIT` chained to it, and the autofill row was written 55.4 s after the form page loaded. → On History alone, Comet's agent navigation is indistinguishable from a person typing a URL. Repeat-run confirmation planned in `RUNBOOK-phase3-human-vs-agent.md`.

### Addendum 2026-10-07 — Phase 3 person vs agent (3 runs each), see RUNBOOK-phase3-human-vs-agent.md "RESULTS"
History `visits.transition` for the same form task: person in Chrome `TYPED|FROM_ADDRESS_BAR` (3/3); Claude in Chrome agent `LINK|FROM_API` (3/3), tabs placed in a Sessions tab group titled "Claude"; Playwright/CDP `TYPED|FROM_API` (3/3); Comet agent (Phase 2) `TYPED|FROM_ADDRESS_BAR` (n = 1). Claude's "Allow this time" leaves no `permissionStorage` entry. Comet 153's assistant refused a private-IP URL that Comet 152's agent had completed.
