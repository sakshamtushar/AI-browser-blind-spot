# Evidence Log — proof artifact per finding (for slide sourcing)
Maps each headline finding to the exact reproducible proof: a saved tool-output file (`reports/…`, `evidence/…`), a raw collection bundle (`collections/…`, gitignored), and/or a screenshot (`screenshots/…`). "Slide" = which deck section it feeds.

| # | Finding (one line) | Proof artifact | Type | Slide |
|---|---|---|---|---|
| C1 | Comet installs machine-wide to `C:\Program Files\Perplexity\Comet\` (3 services incl. ABE elevation) | `reports/delta-10-to-11-comet.md`; lab-findings §Phase1 | text | Triage / native-artifacts |
| C2 | 3 bundled "hidden" extensions (comet-agent debugger/nativeMessaging/`<all_urls>`) | `artifacts/comet-crx/` manifests; lab-findings | text | Native-artifacts |
| C3 | `updater_history.jsonl` = forensic log w/ base64 Omaha req/resp, shipped to Sentry on crash | lab-findings §updater | text | Native-artifacts |
| C4 | Comet assistant prompt text cached locally in perplexity.ai IndexedDB (`thread_latest_entry`) despite "server-side" | `reports/` idb dump; lab-findings §Block1 | text | Native-artifacts (myth-bust) |
| C5 | Comet History logs page trail incl. secret-doc open; agent form values in Web Data autofill | lab-findings §Block1 | text | Attribution |
| C6 | Comet cookies = v20 App-Bound; dead-box DPAPI fails; names leak account-UUID/agent-flag | chromium_decrypt run; lab-findings §headless | text | Triage / decrypt contrast |
| C7 | ABE key minted only in interactive session (session-0 fails 0x8004A005) | lab-findings §22 | text | (caveat) |
| B1 | **Brave Leo `AIChat` fully decrypted (v10, no ABE): verbatim prompts+responses, model, title** | chromium_decrypt output; lab-findings §headless | text (+ screenshot TODO) | The-money-demo |
| B2 | `brave.ai_chat.user_memories` plaintext in Preferences | lab-findings §Block2 | text | Extension/AI-surface artifacts |
| B3 | Brave = per-user install (HKCU, user tasks, no service, no ABE) vs Comet machine-wide | lab-findings §headless | text | Triage |
| X0 | ChatGPT Chrome extension gated on desktop-app install | `screenshots/00-vm-desktop-chatgpt-gated.png` | screenshot | Extension category |
| C2b | comet://extensions does not open (lands on NTP) while 3 ext dirs exist on disk | `screenshots/10-comet-extensions-page.png` + `11-comet-hidden-extensions-ondisk.png` | screenshot pair | Native-artifacts |

## Screenshot backlog (GUI, capture via `scripts/shot.sh` during interactive blocks)
- [ ] Comet sidecar assistant mid-chat (canary page + "Remember codename")
- [ ] Comet agent-mode filling the canary form
- [ ] `comet://extensions` showing NOTHING while 3 extensions are active
- [ ] Brave Leo conversation in-UI (matches the decrypted text)
- [ ] File Explorer: Comet vs Chrome `User Data` side by side (profile delta)
- [ ] ChatGPT sidebar state (gated / or working after decision)
- [ ] Kibana: hunt query results for the activity window (Phase 3)

## Terminal evidence to render as clean "cards" for slides (from saved outputs)
- [ ] ccl_leveldb dump of Comet IndexedDB showing the cached prompt
- [ ] chromium_decrypt.py output: Brave AIChat decrypted vs Comet v20-appbound
- [ ] sqlite3 `.schema` of Brave `AIChat`
- [ ] Comet install delta (services/registry/tasks)
- [ ] `updater_history.jsonl` decoded Omaha request

## Elastic (telemetry) evidence — 2026-09-20 (read-only ES|QL, host thorhq-windows)
| # | Finding | Proof | Slide |
|---|---|---|---|
| E1 | Parent process (explorer vs cmd/python) distinguishes human vs scripted browser launch | elastic-findings.md F1 (tested ES|QL + result table) | Detection/attribution |
| E2 | Assistant page-summary ties comet.exe→canary at exact chat time (07:52:43) | elastic-findings.md F2 | Attribution |
| E3 | Agent form-fill spawned NO process, no distinct net dest (attribution gap) | elastic-findings.md F3 | Attribution (core) |
| E4 | No shipped rule fired; hunts must be self-authored | elastic-findings.md F4 | Closing-the-gap |
