# Elastic telemetry findings — agent/human/scripted attribution (2026-09-20)
Read-only ES|QL against the lab Elasticsearch (192.168.1.27), host `thorhq-windows`, Elastic Defend (`endpoint.events.*`) + Sysmon (`windows.sysmon_operational`). All queries tested and returning; they double as the talk's hunt content. Datasets present for the host today: sysmon_operational 53k, endpoint.events.file 44k, system.security 27k, endpoint.events.{security 13k, process 7.9k, library 1.5k, network 1.5k, registry 1.2k, api 465}.

## Finding 1 — parent process is the human-vs-scripted tell (network is not)
Top-level browser launches today (parent ≠ browser):
| time (UTC) | process | parent | command line |
|---|---|---|---|
| 05:57:57 | comet.exe | **explorer.exe** | `"…\Comet\Application\comet.exe"` (human) |
| 06:02:33 | chrome.exe | **explorer.exe** | `"…\Chrome\Application\chrome.exe"` (human) |
| 07:59:10 | brave.exe | **explorer.exe** | `"…\Brave-Browser\Application\brave.exe"` (human) |
| 09:35:14 | comet.exe | **cmd.exe** | `"…\comet.exe" comet://extensions` (scripted — the cmd.exe parent is the tell) |

→ A browser whose top-level parent is `cmd.exe`/`python.exe`/`node.exe`/`pwsh.exe` (or that carries `--remote-debugging-*` / `--enable-automation`) is driver-launched; a human launch parents to `explorer.exe`. This is the reliable signal — **not** UA/JA4 (all present as Chrome) and **not** DNS (see Finding 3).

Query (ES|QL):
```esql
FROM logs-endpoint.events.process-*
| WHERE @timestamp > "2026-09-20T00:00:00Z" AND host.name=="thorhq-windows"
  AND event.action=="start" AND process.name IN ("comet.exe","chrome.exe","brave.exe","msedge.exe")
  AND process.parent.name NOT IN ("comet.exe","chrome.exe","brave.exe","msedge.exe","explorer.exe")
| KEEP @timestamp, process.name, process.parent.name, process.command_line | SORT @timestamp
```
(Swap the NOT-IN for `process.command_line LIKE "*remote-debugging*" OR "*--enable-automation*"` to catch CDP/Playwright even when parented to explorer.)

## Finding 2 — the assistant action ties to a network connection, at the exact chat time
When the Comet sidecar summarised the canary page (07:52:43), `comet.exe` connected to the canary server; nothing else did except the server itself:
| conns | first→last (UTC) | process | dest |
|---|---|---|---|
| 2 | 07:52:43.672 → 07:52:43.809 | comet.exe | 192.168.1.14:8088 |
| 1 | 07:52:43.672 | python.exe (the canary server) | 192.168.1.14:8088 |
→ Agentic/assistant activity is reconstructable by **time-correlating the browser's network events with app-layer artifacts** (History row, autofill write, IndexedDB prompt cache) — not from any distinct process.

## Finding 3 — agent form-fill spawned NO new process (the attribution gap, on real telemetry)
The Comet agent-mode form submission (~07:55–07:56, `name=C0C0N-CANARY-COMET-04`) produced **no new process** and **no distinctive network destination** beyond `comet.exe → 192.168.1.14:8088`. On the wire Comet does stock-Chrome TLS; its only attributed DNS all day was `wpad` (40×) — backends are reached over pre-resolved/pooled connections. So "an AI agent did this, not the human" is **invisible at the process/network layer**; the evidence is app-layer (autofill `C0C0N-CANARY-COMET-04`, History, `perplexity.ai` IndexedDB prompt cache) + the server-side POST log. This is the talk's core attribution point, now shown on the SOC's own telemetry.

## Finding 4 — detection-content gap, confirmed against this stack
No shipped rule fired on any of the above (SigmaHQ has 0 AI-browser rules; Elastic/Splunk browser allow-lists exclude these). The working hunts are the two queries above (parent-process + automation-flag; network-time-correlation), which a SOC must author itself.

## "What a hunter sees" — human vs assistant vs agent vs scripted (from this lab)
| Signal | Human click | AI assistant (sidecar) | Agent mode (auto form-fill) | Scripted (CDP/Playwright) |
|---|---|---|---|---|
| New process | no | no | no | no (reuses browser) |
| Parent of top-level browser | explorer.exe | explorer.exe | explorer.exe | **cmd/python/node** |
| Cmdline automation flags | — | — | — | **--remote-debugging-*/--enable-automation** |
| UA / JA4 | Chrome | Chrome | Chrome | Chrome |
| Network dest | site | site + perplexity.ai | site + perplexity.ai | site |
| App-layer trace | History | History + IDB prompt cache | History + **autofill** + IDB | History |
| Highest-fidelity tell | — | time-correlate net+IDB | autofill/IDB + server log | **parent/flags** |

## Finding 5 (2026-10-07, Phase 3) — Claude in Chrome's network trail is session-level, not per action
Read-only ES|QL, `logs-endpoint.events.network-*` and `logs-windows.sysmon_operational-*`, host `thorhq-windows`, `chrome.exe`, 08:40–09:17 Z (3 person runs, 3 Claude-agent runs). Raw: `reports/hva-chrome/elastic-chrome-conns.csv`, `elastic-chrome-dns.csv`.
- **First Claude run only (CA-T1-1, 08:44–08:51 Z):** a burst of 20 new connections, including **160.79.104.10:443 (OrgName Anthropic, PBC)** at 08:44:27, Cloudflare 104.18.12.205/104.18.13.205, Google front ends; DNS for `claude.ai` (16 lookups, 08:49:40–08:50:07) and `browser-intake-us5-datadoghq.com` (8, 08:49:45–08:50:10, client telemetry). `api.anthropic.com` resolved once at 09:08 Z, between runs.
- **CA-T1-2 and CA-T1-3:** **zero** new connections or lookups to Anthropic; Chrome reused pooled HTTP/2 or QUIC connections. The person runs looked the same (0–2 Google connections).
- **The canary site itself (192.168.1.14:8088) never appears**: the browser and the server are the same host, so neither Defend nor Sysmon (which only logged mDNS for chrome.exe here) recorded those connections.
→ Network telemetry says "Claude in Chrome was in use on this host from ~08:44", not "Claude submitted this form at 09:04". For per-action attribution you need History's `FROM_API` and the "Claude" tab group; network only scopes the time window. Same conclusion as Finding 3 for Comet.

## Finding 6 (2026-10-08) — agent extensions: no per-action process, but a desktop bridge is a child of the browser
- **Windows VM, Phase 3 windows** (`reports/hva-chrome/elastic-chrome-procs.csv`, Elastic Defend process starts, parent or process `chrome.exe`, 08:40–09:17 Z): every child Chrome started during both the person runs and the Claude-in-Chrome agent runs was `chrome.exe --type=renderer` (person runs 2–10, Claude runs 6–30 start events), with **identical command-line flag sets**. One `utility --utility-sub-type=video_capture.mojom.VideoCaptureService` appeared once, at 08:44:32 during the first Claude run only (not repeated; not a signal). No native-messaging host: the Claude desktop app is not installed on the VM.
- **Operator's Mac, live read-only `ps`** (2026-10-08): `Google Chrome` (pid 87793) is the direct parent of `/Applications/Claude.app/Contents/Helpers/chrome-native-host` (etime 32 days) and of `~/.codex/plugins/cache/openai-bundled/chrome/latest/extension-host/macos/arm64/ChatGPT for Chrome` (23 days), i.e. the Claude in Chrome and ChatGPT-extension native-messaging hosts.
→ An extension agent's individual actions produce no distinctive process, but a desktop-linked agent extension shows up as the browser parenting an AI vendor's native host. Hunt: browser process → native-messaging host binaries from Anthropic/OpenAI/Perplexity paths. Presence, not per-action attribution.
