# Changelog

All notable changes to this repository are recorded here.

## v1.1.0 — hardening (2026-10-23)

- `retryOnFail` + `maxTries: 3` + `waitBetweenRetries: 2` on the seven active network nodes
  (`Get a file`, `Transcribe a recording`, `Analyze image`, `Generate audio`,
  `Send an audio file`, `Send a text message`, `Download file`).
- Added `scripts/validate_workflows.py`: parses the export, scans for secret-like tokens and
  checks that every connection points to an existing node.
- CI (`.github/workflows/validate.yml`) runs that check on every push.
- Split out of the combined `bewerbung-automation` repository so each workflow has its own repo.

## v1.0.0 — initial public release (2026-10-23)

- Sanitized export with all resource IDs replaced by placeholders and regenerated webhook IDs.
- README with architecture diagram, verified limitations and setup guide.
- `SECURITY_AUDIT.md`, `docs/analysis-answer-from-vector.ar.md` (Arabic node-by-node analysis),
  `.env.example`, `.gitignore`, MIT license.
