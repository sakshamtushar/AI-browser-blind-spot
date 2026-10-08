# Mac extension teardown — Claude in Chrome & ChatGPT extension (2026-09-20)
Source: this Mac's **Default** Chrome profile (real Claude Max + ChatGPT Plus sessions). Analysis was **keys-only, content-redacted** (`scripts/ext_teardown_redacted.py`): key names, value sizes, numeric timestamps and JSON *skeletons* (every string → `<str:N>`) — no tokens, domains, or message text emitted or committed. Raw profile copies were deleted after analysis; nothing raw is in git. Extension storage layout is identical on Windows, so these transfer to the Windows story (only the profile root differs). Usernames in paths shown as `<user>`.

## Claude in Chrome `fcoeoabgfenejglbffodgkkbkcdhcgfn` (v1.0.94) — `Local Extension Settings/<id>` (chrome.storage.local, 53 records)
Plaintext keys of interest (values redacted):
- **`permissionStorage`** (1,297 B) — the injectable consent store (Origin Technology's vector), **confirmed on a real profile**: `permissions[]` of `{action, createdAt, lastUsed (epoch-ms), duration, id(uuid), scope:{netloc, type}}`. Real per-site grants + timestamps in the clear; unsigned (no HMAC) → same structure Origin injected. (Domains/grants redacted.)
- Identity/bridge (all plaintext): `accountUuid`, `anonymousId`, `bridgeDeviceId`, `permissionConsentOwner`, `tokenOrg`={hybrid,uuid}, `lastActiveOrgHint`.
- OAuth/PKCE: `oauthState`, `codeVerifier` (43 chars). MCP/agent: `mcpConnected:true`, `mcpTabGroupId`, `dismissedTabGroups`, `selectedModel`, `lastPermissionModePreference`.
- `features` (~230 KB) — full server feature-flag payload (`chrome_ext_*`), rewritten repeatedly → many superseded copies in the LevelDB.
- **Tokens:** NOT in chrome.storage.local on v1.0.94. **But** `accessToken`/`refreshToken`/`AccessToken`/`RefreshToken` key-names ARE present in the profile's **Local Storage** LevelDB (`Local Storage/leveldb`) — Claude session/bearer tokens persist on disk there (claude.ai web origin and/or extension; values redacted). So the "plaintext token on disk" exposure still holds; it moved store (chrome.storage.local → Local Storage), not off-disk. Correction to an earlier note.

## ChatGPT extension `hehggadaopoacecdllhhajmbjkdcmajg` (v1.26.901) — first public teardown
- **`chrome.storage.local` holds NO conversation, tokens, prompts, or identity** (SECRET/conversation-shaped keys = NONE). Conversation is server-side; only anonymous device state locally.
- **Dominant artifact: `NATIVE_HOST_STATUS` × 18,848** — a heartbeat row written every few seconds, **never compacted**. Each = `{hostName:"com.openai.codexextension", state:"connected", lastChecked:<epoch-ms>, reconnectAttempt}`. Retained span **2026-05-26 → 2026-07-06 (~40 days)** → an unintended fine-grained "browser+extension running" timeline, and proof of a persistent **native-messaging bridge to the ChatGPT/Codex desktop app**.
- Small config: `extensionInstanceId` (uuid), `TAB_GROUPS` (chromeGroupId+color), `codexToolbarStateTelemetryId` (uuid), `codexToolbarStateLastSnapshot` (ts), `lastSeenExtensionActionCalloutVersion`.
- IndexedDB `codex-browser-host` → store `records`: **0 rows** (empty; nothing cached there).

## NativeMessagingHosts manifests — the AI-agent bridge map (plaintext JSON, cheap high-value pivot)
`~/Library/Application Support/Google/Chrome/NativeMessagingHosts/*.json` names each bridge binary + the extension IDs allowed to drive it:
| Manifest | Bridge binary (`path`) | Allowed extension origins |
|---|---|---|
| `com.perplexity.comet` | `/Applications/Perplexity.app/Contents/MacOS/comet-native-host` | `npclhjbddhklpbnacpjloidibaggcgon` (the hidden **comet-agent**) |
| `com.openai.codexextension` | `/Users/<user>/.codex/plugins/cache/openai-bundled/chrome/latest/extension-host/macos/arm64/ChatGPT for Chrome` | `hehggada…` (+ `odlomjlbamekndcpllcnffbgeohgkmjh`) |
| `com.anthropic.claude_browser_extension` | `/Applications/Claude.app/Contents/Helpers/chrome-native-host` | `fcoeoabg…` (+ beta `dihbgbnd…`, `dngcpimn…`) |
| `com.anthropic.claude_code_browser_extension` | `/Users/<user>/.claude/chrome/chrome-native-host` | `fcoeoabg…` |
DFIR value: one directory of world-readable JSON reveals every installed AI browser-agent bridge, the exact local executable each spawns, and which extension is authorised — a clean triage pivot on both macOS (`~/Library/Application Support/Google/Chrome/NativeMessagingHosts`) and Windows (`HKCU\SOFTWARE\Google\Chrome\NativeMessagingHosts\<name>` → JSON path). On Windows these register under `Software\Google\Chrome\NativeMessagingHosts` (and per-machine HKLM) — re-verify names on the VM.

## Matrix contrast (extension category)
- **Claude in Chrome** = rich local state (injectable `permissionStorage`, identity UUIDs, PKCE, MCP bridge flags) + tokens in Local Storage; two native hosts (desktop app + Claude Code CLI).
- **ChatGPT extension** = near-empty local state EXCEPT a giant native-host heartbeat timeline; conversation & identity server-side; one native host (Codex desktop app).
- Both, plus Comet, prove the **desktop-app native-messaging bridge** pattern — the highest-fidelity on-disk tell that an agentic AI browser-driver is installed.
