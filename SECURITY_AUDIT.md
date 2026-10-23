# Security Audit — `Answer from vector v2` export (pre-publication review)

**File audited:** `Answer from vector v2.json` (original, not modified) and its sanitized copy `workflows/answer-from-vector-v2.sanitized.json`. The canvas screenshot in `docs/` was reviewed as well.
**Method:** static inspection of the exported JSON only; nothing was executed and no external service contacted.

## 1. Executive summary

| # | Finding | Where | Severity | Status |
|---|---|---|---|---|
| 1 | No plaintext API keys anywhere in this export (all OpenAI/Supabase access goes through n8n credentials) | whole file | — | OK |
| 2 | Real Google resource identifiers embedded: a Sheets document ID and a Drive file ID pointing to `personal_info.pdf` | `Append row in sheet`, `Download file` | **Medium** | replaced with placeholders in the sanitized copy |
| 3 | Internal table name `documents` and fixed filter `id = 1` reveal data model assumptions | Supabase nodes | Low | acceptable; parameterise if you publish real data |
| 4 | Credential metadata (names + internal credential IDs) — no secret values, n8n never exports them | every credentialed node | Low | normal for exports |
| 5 | Instance fingerprint (`meta.instanceId`), workflow/version IDs and five `webhookId` UUIDs | top-level meta | Low | webhookIds regenerated in the sanitized copy |
| 6 | Three nodes are disabled, so their data paths (Sheets logging, Gmail send, Supabase user lookup) never run | node definitions | Informational | documented in README §5 |

**No passwords, tokens, connection strings, private IPs or personal names were found in this export.** The original file's `pinData` was already empty.

## 2. Sanitization applied

- Google Sheets document ID → `<REPLACE_WITH_SHEET_ID>`
- Drive file ID → `<REPLACE_WITH_FILE_ID>`, cached result URLs removed
- Hard-coded personal e-mail → `<YOUR_EMAIL>`
- all `webhookId` values regenerated so the published file carries no instance fingerprint
- node graph, node count (25) and connections preserved — the file still imports cleanly into n8n

Residual by design: generic file name `personal_info.pdf` in the ingestion branch. Replace it with your own document before running.

## 3. Pre-publication checklist

1. Confirm the referenced Drive document is not publicly shared.
2. Create your own Supabase table and Postgres memory schema.
3. Never commit `.env`; keep raw exports out of the repository (see `.gitignore`).
4. Re-check any screenshot for open node panels before publishing.
