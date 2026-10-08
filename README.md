# AI Browser Blind Spot

Lab notes, captures and collectors from the c0c0n 2026 talk *"The AI Browser Blind Spot"*: what AI-native browsers (Perplexity Comet, Brave Leo, Gemini in Chrome) and browser agents (Claude in Chrome, ChatGPT for Chrome) leave on disk, and how much of it can say who acted.

## Collectors (`deliverables/`)

| File | What it is | Tested |
|---|---|---|
| `Windows.Applications.AIBrowsers.yaml` | Velociraptor artifact: AI browsers, Comet prompt cache, Brave Leo AIChat and memories, AI extensions and their stores, Gemini `glic` partition, native-messaging hosts (registry), History visits with FROM_API | Velociraptor 0.77.3 on the lab VM |
| `Comet.tkape`, `BraveLeo.tkape` | KAPE targets for Comet and Brave Leo | Paths resolved on the lab VM; not yet run in KAPE |
| `extract_ai_browser_artifacts.py` | Read-only extractor for a collected profile | Phase 2 collections |

See `deliverables/README.md` for details and test results.

## Lab write-ups

- `lab-findings.md`: Windows findings (Comet, Brave, Chrome)
- `mac-findings.md`, `mac-extension-findings.md`: macOS, Claude in Chrome, ChatGPT for Chrome, TCC, native hosts
- `elastic-findings.md`: Elastic network and process telemetry
- `RUNBOOK-phase2.md`, `RUNBOOK-phase3-human-vs-agent.md`: how the runs were done; Phase 3 compares a person, Claude in Chrome, Playwright and the Comet agent
- `captures/`, `reports/`, `screenshots/`: evidence behind the slides
- `scripts/`, `www/`: lab tooling and the canary pages

All accounts, form values and canaries are throwaway lab data. Raw profile collections are not included. Scripts that drive the lab VM read its password from the `LAB_PW` environment variable.
