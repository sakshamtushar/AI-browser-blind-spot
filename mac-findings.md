# Mac phase — macOS artifacts (2026-09-21)
Source: this Mac (production; Comet + ChatGPT + Claude installed and used). **Read-only, redacted, no destruction**; no raw data copied to the repo; usernames shown as `<user>`. Extension storage was covered separately in `mac-extension-findings.md`; this covers macOS-native browser, desktop-agent apps, Keychain, TCC, LaunchAgents, and web-origin storage.

## M1 — macOS-native Comet (confirms Apple-registry identifiers first-hand)
- `/Applications/Comet.app`, bundle **`ai.perplexity.comet`**, **TeamIdentifier 7S8W4W365S** (matches Apple's password-manager-resources registry — now verified on a live install).
- Profile root `~/Library/Application Support/Comet/` → `Default`, `Profile 1`, `Local State`, `piid`, `Crashpad`, `System Profile`. Prefs `~/Library/Preferences/ai.perplexity.comet.plist`.
- **Default-vs-Chrome delta identical to Windows**: adds `adblock`, `dxt`, `BrowsingTopics*`, `InterestGroups`, `PrivateAggregation`, `SharedStorage`. Same three bundled extensions on disk (`mcjlamohc…`, `mjdcklhep…`, `npclhjbdd…`) + Dark Reader (`ahfpelljb…`) in `Local Extension Settings` — cross-platform consistent.

## M2 — Keychain "Safe Storage" names CONFIRMED (closes stream-05 gap)
`security find-generic-password` (metadata only, secret NOT dumped): **`Comet Safe Storage`** (acct `Comet`) present; `Chrome Safe Storage` present; `Brave Safe Storage` absent (Brave unused on this Mac).

## M1b — cross-platform encryption contrast (slide-worthy)
macOS Comet `Local State.os_crypt` = **empty `{}`** → no App-Bound Encryption; the cookie/password AES key lives **only** in the `Comet Safe Storage` Keychain item (Chromium v10, AES-128-CBC). So the **same browser** encrypts two different ways: **Windows Comet = v20 App-Bound** (dead-box needs the live `CometElevationService`); **macOS Comet = v10 Keychain** (dead-box needs the login Keychain / user password). One matrix row, two OS stories.

## M3 — desktop agent apps & OS-level capability artifacts (novel surface)
### "Zombie Atlas" — a discontinued AI browser that left residue + capabilities (standout)
Atlas was shut down 2026-08-09 and `/Applications/ChatGPT Atlas.app` is gone, **yet the Mac still carries**:
- **A dangling LaunchAgent** `~/Library/LaunchAgents/com.openai.atlas.update-helper.plist` whose `ProgramArguments` points at `/Applications/ChatGPT Atlas.app/Contents/Library/AtlasUpdateHelper` — a broken-path persistence entry a hunter would flag immediately.
- **Preferences** `~/Library/Preferences/com.openai.atlas.plist` + `com.openai.atlas.web.plist`; `~/Library/HTTPStorages/com.openai.atlas`.
- **Live TCC grants** (auth_value=2 allowed) for `com.openai.atlas`: `Microphone`, `BluetoothAlways`, `SystemPolicyDownloadsFolder`, `WebBrowserPublicKeyCredential` — capability grants outliving the app. → Real-world proof of the "AI browser dies, forensic residue + granted capabilities persist" thesis.

### TCC.db — the agentic capability map (`~/Library/Application Support/com.apple.TCC/TCC.db`)
Real grants observed for AI agents (service | client | auth):
- `com.anthropic.claudefordesktop`: Desktop/Documents/Downloads folders + SystemPolicyAppData (broad file access).
- `com.anthropic.claude-code`: Documents/Downloads/AppBundles/MediaLibrary + **AppleEvents** (app automation) + WebBrowserPublicKeyCredential.
- `ai.perplexity.comet`: BluetoothAlways, WebBrowserPublicKeyCredential.
- `com.openai.chat`: Camera, PhotosAdd. `com.openai.atlas`: (zombie, above).
→ On macOS, **TCC.db is the single best "what can this AI agent actually touch" triage source** (Screen Recording / Accessibility / Folder / AppleEvents grants), and it retains entries after uninstall.

### Perplexity "keystone" updater (macOS Sparkle-fork) — persistence
LaunchAgents `ai.perplexity.keystone.agent.plist`, `ai.perplexity.keystone.xpcservice.plist`, `ai.perplexity.CometUpdater.wake.plist` → `~/Library/Application Support/Perplexity/CometUpdater/Current/CometUpdater.app/Contents/MacOS/CometUpdater --wake-all --enable-logging`.

### ChatGPT desktop (Codex) — `~/.codex` (2.8 GB) agent-forensics surface
`auth.json` (creds — NOT read), `config.toml` (+ many dated backups incl. `pre_deepseek`), `history.jsonl`, `sessions/` + `archived_sessions/`, sqlite DBs `memories_1`, `logs_2`, `queue_1`, `thread_history_1`, `goals_1`, `state_5` (+ `-wal/-shm`), `computer-use/`, `browser/`, `chrome-native-hosts.json`, `installation_id`, `skills/`, `plugins/`. Group Containers `2DC432GLL2.com.openai.sky.CUAService` (the Computer-Use agent service needing Screen Recording+Accessibility) and `…com.openai.codex.notifications`.

### Claude desktop (`~/Library/Application Support/Claude`, 13 GB + `~/.claude` 2.1 GB)
Electron app with its **own embedded Chromium profile**: `Cookies`, `IndexedDB/https_claude.ai_0.indexeddb.leveldb`, `Local Storage`, `Service Worker`, `Partitions`, `Session Storage`. Plus agent state: `claude_desktop_config.json` (MCP servers), `bridge-state.json`, `buddy-tokens.json`, `ant-did`/`ant-device-registry.json`, `local-agent-mode-sessions/`, `claude-code-sessions/`, `cowork-enabled-cli-ops.json`, `git-shadow/`, `git-worktrees.json`, `spaces`/`space-memory`. `~/.claude`: `sessions/`, `transcripts/`, `projects/`, `history.jsonl`, `memory/`, `mcp-servers/`, `plans/`, `todos/`, `telemetry/`. → The Claude *desktop app* is a full second browser-forensic surface distinct from Claude-in-Chrome; conversation/agent history is on disk here (contents not inspected).

## M4 — AI web-app origin storage in Chrome Default (presence only, no content)
- IndexedDB: `claude.ai` 24K(+blob), `chatgpt.com` 28K(+blob) — thin (conversation server-side); `www.perplexity.ai` **2.3M**(+blob) — larger client cache (matches the Windows Comet prompt-cache finding).
- **Token attribution corrected/confirmed:** `accessToken`/`refreshToken` key-names in Chrome `Local Storage/leveldb` are co-located with the **`https://claude.ai` and `https://chatgpt.com` web origins** — i.e. the **web-app session tokens** persist in Local Storage (values redacted), distinct from the extensions' `Local Extension Settings`. This refines the earlier note: the on-disk Claude/ChatGPT bearer/refresh tokens are the *web-app* localStorage tokens.
- Service Worker CacheStorage: 531 origin-hashed cache dirs present (content-addressable artifact class; AI web apps cache app shell + responses here).

## Cross-platform takeaways for the deck
1. Same product, OS-specific crypto: Comet v20-ABE (Win) vs v10-Keychain (mac).
2. **macOS adds three artifact sources Windows doesn't foreground**: `TCC.db` (agent capabilities, persist post-uninstall), LaunchAgents (updater persistence + zombie/orphan entries), and Group Containers (agent XPC services).
3. Desktop agent apps (`~/.codex`, `~/.claude`, Claude.app 13G) are *their own* forensic surfaces — bigger than the browser extensions — holding `auth.json`/session/transcript stores and embedded Chromium profiles.
4. "Zombie Atlas" is real on a production Mac: LaunchAgent + prefs + HTTPStorages + TCC grants outlive the deleted app.
