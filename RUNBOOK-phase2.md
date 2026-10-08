# Phase 2 Runbook — Activity & Collection (Windows VM `thorhq-windows`)

Legend: 🧑 = you at the VMware console (logged in as `thorh`) · 🤖 = Claude over SSH (automated) · 📦 = collection bundle label.
Canary format: `C0C0N-CANARY-<product>-<nn>` (e.g. `C0C0N-CANARY-COMET-03`). Never type real personal data. Throwaway Gmail + throwaway Perplexity / Claude Pro / ChatGPT accounts only.

## Pre-reqs (once)
1. 🧑 Create the throwaway Gmail; sign up Perplexity (free), Claude (Pro), ChatGPT (Free is enough for the sidebar; Plus if we want browser-control).
2. 🧑 Log in to the VM console as `thorh` and leave the session logged in (lock screen is fine). 🤖 needs an interactive session for headed browsers.
3. 🤖 VM snapshot `c0c0n-01-browsers-installed` (Chrome, Comet, Brave installed; none launched).

## A. Comet
| # | Who | Step | 📦 after |
|---|---|---|---|
| A1 | 🤖 | First launch (`comet.exe --no-first-run`), wait 60 s, close. Confirms external-extension install into `%LOCALAPPDATA%\Perplexity\Comet\User Data\Default\Extensions\`, `Local State` ABE key, first telemetry. | `20-comet-firstrun` |
| A2 | 🧑 | Open Comet, sign in with the throwaway Perplexity account (Google SSO). Skip import. Close Comet. | `21-comet-signedin` |
| A3 | 🧑 | Open Comet. In the **sidecar assistant**, run 3 chats: (1) "Summarise this page" on `http://192.168.1.14:8088/canary-COMET-01.html`; (2) ask "Remember that my project codename is C0C0N-CANARY-COMET-02"; (3) paste the text of `C:\lab\www\secret-COMET-03.txt` and ask for a summary (simulated data exfil). Leave Comet open. | `22-comet-after-chat` (live, VSS) |
| A4 | 🧑 | **Agent mode**: ask the assistant to "open http://192.168.1.14:8088/form.html, fill the form with name C0C0N-CANARY-COMET-04 and submit". Then ask it to "check my Gmail for the newest email and summarise it" (throwaway inbox contains a seeded mail). Close Comet. | `23-comet-after-agent` |
| A5 | 🤖 | Elastic pull for the A3/A4 windows (process/network/file/registry/Sysmon). | — |
| A6 | ~~clear-data~~ | DROPPED (no destruction) — sourced from public docs |
| A7 | ~~uninstall+carve~~ | DROPPED (no destruction) — sourced from public docs |

## B. Chrome + Claude in Chrome (`fcoeoabgfenejglbffodgkkbkcdhcgfn`)
| # | Who | Step | 📦 |
|---|---|---|---|
| B1 | 🤖 | Chrome first launch, no extensions. | `30-chrome-firstrun` |
| B2 | 🧑 | Install Claude in Chrome from the Web Store; sign in (throwaway Claude Pro). | `31-claude-installed` |
| B3 | 🧑 | Side panel: 3 chats with canaries `CLAUDE-01..03` (page summary on canary page; a question; paste `secret-CLAUDE-03.txt`). Then trigger an action on `form.html` and click **"Always allow"** for `192.168.1.14`. | `32-claude-after-chat` |
| B4 | 🤖 | Dump `Local Extension Settings\fcoeoabg…` (ccl_leveldb): enumerate keys (`permissionStorage`, tokens — redacted in reports), IndexedDB presence, Service Worker cache, native-messaging manifest, named pipe. | — |
| B5 | 🧑 | Chrome → Clear browsing data (all time). | `33-claude-cleared` |
| B6 | 🧑 | Remove the extension. | `34-claude-uninstalled` (+ carve) |

## C. Chrome + ChatGPT extension (`hehggadaopoacecdllhhajmbjkdcmajg`) — first public teardown
Same as B (C1–C6), canaries `CHATGPT-nn`, plus 🤖 static grep of the unpacked 20 MiB bundle for telemetry SDKs and the native-host manifest name.

## D. Chrome + HARPA AI (BYOK) and Sider
| D1 | 🧑 | Install HARPA; enter dummy key `sk-C0C0NCANARYHARPA000000000000000000000000000000000` in BYOK settings; 2 chats. Install Sider; 1 chat. | `40-thirdparty-after-chat` |
| D2 | 🤖 | Locate the plaintext key + local chat archive; test `browsingData` behaviour. | — |

## E. Edge Copilot and Brave Leo
| E1 | 🧑 | Edge: Copilot sidebar, 2 chats (`EDGE-01/02`) incl. page summary of the canary page. | `50-edge-after-chat` |
| E2 | 🧑 | Brave: Leo, 2 chats (`BRAVE-01/02`), plus "remember" memory line. | `51-brave-after-chat` |
| E3 | 🤖 | Parse Brave `AIChat` SQLite (cleartext columns vs encrypted), `Preferences` → `brave.ai_chat.*`; Edge web-origin IndexedDB/SW cache for `edgeservices.bing.com` / `copilot.microsoft.com`; `WebCacheV01.dat`. | — |

## F. Control row — scripted automation
| F1 | 🤖 | Playwright-driven Chrome with `--remote-debugging-port` + custom `--user-data-dir` visiting the same canary pages, filling `form.html`. | `60-playwright-control` |
| F2 | 🤖 | Elastic pull; compare process cmdline / parent / network / timing against A4 (Comet agent) and B3 (Claude action) → the "human vs assistant vs agent vs script" table. | — |

## G. Wrap
| G1 | 🤖 | Snapshot `c0c0n-02-phase2-complete`; pull all bundles; produce per-product artifact tables + `Comet.tkape`, `BraveLeo.tkape`, Velociraptor artifact, tested queries. |

## Canary site (🤖 sets up)
`C:\lab\www\` served on `http://192.168.1.14:8088/` by Python `http.server` via a scheduled task: `canary-<PRODUCT>-01.html` (unique text + hidden prompt-injection-style comment for realism, harmless), `form.html` (name/email/notes form → POST logged to `C:\lab\www\form-log.txt`), `secret-<PRODUCT>-03.txt` (fake "confidential" doc with canary). Seeded email in the throwaway Gmail: subject `C0C0N-CANARY-MAIL-01`.
