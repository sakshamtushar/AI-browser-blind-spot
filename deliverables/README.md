# Collectors

Collectors for the AI layer that standard browser collection skips. All are read-only.

| File | Tool | Collects | Status |
|---|---|---|---|
| [`Windows.Applications.AIBrowsers.yaml`](Windows.Applications.AIBrowsers.yaml) | Velociraptor | AI browsers present, Comet prompt cache, Brave Leo chats and memories, AI extensions and their storage, Gemini `glic` partition, native-messaging bridges, History visits with FROM_API | Tested (Velociraptor 0.77.3) |
| [`Comet.tkape`](Comet.tkape) | KAPE | Comet profiles, prompt cache, bundled agent extensions, updater log | Paths checked |
| [`BraveLeo.tkape`](BraveLeo.tkape) | KAPE | Brave Leo `AIChat` database, memories, profile | Paths checked |
| [`extract_ai_browser_artifacts.py`](extract_ai_browser_artifacts.py) | Python | Parses a collected profile: AIChat, prompt cache, extension storage, glic partition | Tested on lab collections |

## Velociraptor

Import the YAML into your server (*View Artifacts → Upload*), or run it locally:

```
velociraptor.exe --definitions <folder-with-yaml> artifacts collect Custom.Windows.Applications.AIBrowsers --args UploadArtifacts=Y --output out.zip
```

Each source returns its own table. `UploadArtifacts=Y` also copies the files (Local State, Preferences, History, Web Data, Sessions, prompt cache, extension storage).

## KAPE

Copy both `.tkape` files into `KAPE\Targets\Browsers\`, then:

```
kape.exe --tsource C: --tdest D:\out --target Comet,BraveLeo
```

For Comet on Windows, collect **live, before shutdown**: its cookies use App-Bound Encryption (`v20`) and only decrypt on the original machine.

## Extractor

```
pip install chromium-reader cryptography
python extract_ai_browser_artifacts.py "<path to User Data>"            # string values redacted
python extract_ai_browser_artifacts.py "<path to User Data>" --unsafe   # raw values (contains PII)
```

Works on Chrome, Edge, Brave and Comet profiles from any OS. To decrypt Brave Leo chat text on the owning Windows host, use [`../scripts/decrypt_leo.py`](../scripts/decrypt_leo.py); for cookies, [`../scripts/chromium_decrypt.py`](../scripts/chromium_decrypt.py) (v10 only; it flags v20 as needing the live host).

Generic parsers work too: Hindsight parsed 6,899 records from a Comet profile ([notes](hindsight-comet-demo/README.md)). What they miss is the AI-specific fields, which is what the extractor adds.

## Test notes

Tested 8 Oct 2026 on the lab VM (Windows 11, Comet 153, Brave, Chrome 154):

- **Velociraptor:** `artifacts verify` passes. Every source returned data except `GeminiGlicPartition` (Gemini in Chrome wasn't enabled on that VM; the partition was seen on macOS). It found Comet's three bundled extensions, Claude in Chrome and ChatGPT, 36 extension-storage files, 17 prompt-cache files, 5 native-messaging hosts, and all three Claude in Chrome agent runs as FROM_API visits. Output: [`../reports/velo-test`](../reports/velo-test).
- **KAPE:** every path and file mask matched files on the VM, except Comet `Storage\ext` (not present on that install). Not yet run through KAPE itself.
