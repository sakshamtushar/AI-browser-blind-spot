# AI Browser Blind Spot

Forensics for AI browsers and browser agents: what Perplexity Comet, Brave Leo, Gemini in Chrome, Claude in Chrome and ChatGPT for Chrome leave on disk, how to collect it, and how far it tells you **who acted**: the person, or the agent.

From the c0c0n 2026 talk *"The AI Browser Blind Spot"* by Saksham Tushar. Everything here comes from lab runs on a Windows 11 VM and a Mac.

## Start here

| I want to… | Go to |
|---|---|
| Collect AI-browser evidence from an endpoint | [`deliverables/`](deliverables): Velociraptor artifact, KAPE targets, extractor |
| Hunt for AI browsers and agents in my telemetry | [`hunts/`](hunts): ES\|QL, SQLite and shell hunts |
| See what each product writes to disk | [`lab-findings.md`](lab-findings.md) (Windows) · [`mac-findings.md`](mac-findings.md) (macOS) |
| Tell a person from an agent | [`RUNBOOK-phase3-human-vs-agent.md`](RUNBOOK-phase3-human-vs-agent.md) |
| See what EDR and network telemetry showed | [`elastic-findings.md`](elastic-findings.md) |
| Check the raw evidence behind a claim | [`captures/`](captures) · [`reports/`](reports) · [`evidence-log.md`](evidence-log.md) |

## Key findings

1. **Standard collection misses the AI layer.** Prompts, chat history and agent permissions live in places browser triage doesn't collect: Comet's prompt cache (IndexedDB), Brave's `AIChat` database, extension storage, and Gemini's separate `glic` storage partition.
2. **Comet ships its own agent.** It installs three extensions on first run, one with `debugger` access. Chrome's `Secure Preferences` records them as Web Store installs; they weren't.
3. **History can flag some agents.** Claude in Chrome's agent and Playwright scripts set the `FROM_API` bit on History visits; a person typing doesn't. **Comet's agent can't be told apart from a person** this way.
4. **Process and network telemetry show presence, not actions.** Agents run inside the browser's normal processes. You can see that an agent was connected and roughly when, not which click was the agent's.
5. **Comet's Windows cookies only decrypt on the original machine** (App-Bound Encryption). Collect live.

## What's in the repo

```
deliverables/   Collectors: Velociraptor artifact, KAPE targets, Python extractor
hunts/          Hunt queries (ES|QL, SQLite, shell), with test status
captures/       Short evidence snippets referenced by the talk
reports/        Profile analyses, before/after diffs, Phase 3 results, Velociraptor test output
screenshots/    Lab screenshots
scripts/        Lab tooling: parsers, decryptors, comparison and run scripts
www/            Canary pages and test server used in the lab
*.md            Findings, runbooks and the evidence log
```

## How the lab was run

- **Phase 2:** each product was installed on a clean Windows 11 VM, used against canary pages, and its profile collected before and after. Reports in [`reports/`](reports).
- **Phase 3:** the same form was filled by a person, by Claude in Chrome's agent, by a Playwright script, and by Comet's agent, three runs each where possible, then compared on History, Sessions, the website's own telemetry, and Elastic. See the [runbook](RUNBOOK-phase3-human-vs-agent.md).
- **macOS:** read-only checks on a working Mac (Keychain, TCC permissions, native-messaging hosts, extension storage), with personal details redacted.

## Caveats

- Small samples: three runs per driver, one Comet agent run. Treat the findings as leads to test in your own environment.
- Versions matter: Chrome 154, Comet 152–153, Brave 1.95, Claude in Chrome 1.0.94. Storage layouts change between releases.
- All accounts, form values and "secrets" here are throwaway lab data. Raw profile collections are not included.
- Scripts that drive the lab VM read its password from the `LAB_PW` environment variable.

## Links

- Talk notes: [sakshamtushar.com](https://sakshamtushar.com) · YouTube: THOR-HQ · [topmate.io/saksham_tushar](https://topmate.io/saksham_tushar)
