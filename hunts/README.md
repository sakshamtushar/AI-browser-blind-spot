# Hunts

Six hunts from the talk. None of these existed as public rules in SigmaHQ, Elastic or Splunk when we checked (Sep 2026).

| # | Hunt | Finds | Platform · data | Status |
|---|---|---|---|---|
| 01 | [Browser started by a script](01-browser-started-by-script.esql) | Browsers launched by cmd, PowerShell, python or node instead of a person | Windows · Elastic Defend | Tested in lab |
| 02 | [Browser automation flags](02-browser-automation-flags.esql) | `--remote-debugging-*` or `--enable-automation` on a browser launch (CDP, Playwright) | Windows · Elastic Defend | Untested query |
| 03 | [History visits with FROM_API](03-history-from-api-visits.sql) | Navigation by an extension agent or CDP script (Claude in Chrome, Playwright) | Any OS · Chromium `History` file | Tested in lab |
| 04 | [Comet installed](04-comet-installed.esql) | comet.exe, its updater, or the `WOW6432Node\Perplexity\Update` key | Windows · Elastic Defend | Untested query |
| 05 | [Browser runs an AI native host](05-browser-runs-ai-native-host.esql) | A desktop-linked agent bridge (Claude, ChatGPT) started by the browser | Windows/macOS · Elastic Defend | Untested query; seen with `ps` |
| 06 | [Orphaned Atlas updater](06-macos-orphaned-atlas-updater.sh) | ChatGPT Atlas LaunchAgent left after the app was removed | macOS · shell | Tested on a Mac |

## How to run

- **`.esql`:** paste into Kibana → Discover (ES|QL mode), or `POST _query`. Index names assume Elastic Defend; change `FROM` for your data. Each file says what it looks for and what noise to expect.
- **`.sql`:** run on a *copy* of the browser's `History` file: `sqlite3 History-copy < 03-history-from-api-visits.sql`. The Velociraptor artifact in [`../deliverables`](../deliverables) runs the same query across every profile on a host.
- **`.sh`:** `sh 06-macos-orphaned-atlas-updater.sh` (read-only).

## Read the results carefully

- These find **leads, not proof**. FROM_API and the parent process show that software drove the browser. They don't show who asked it to.
- **Comet's own agent is not caught by any of these.** In our lab its visits looked exactly like a person typing (`TYPED | FROM_ADDRESS_BAR`). For Comet, correlate its prompt cache and Elastic timing instead.
- "Tested in lab" means the query returned the expected hits on our test VM or Mac. "Untested query" means the behaviour was observed in the lab but this exact query wasn't run.
