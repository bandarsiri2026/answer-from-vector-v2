# Setup guide — Answer from vector v2

## 1. Prerequisites

- n8n (self-hosted Docker/npm or n8n Cloud), version supporting the LangChain agent node v3.
- A Telegram bot you control (BotFather token).
- OpenAI API access: chat completions, embeddings, transcription, text-to-speech.
- Supabase project with a table named `documents` (columns used by the vector store: an embedding column and a `queryName`/content column).
- A Postgres database reachable from n8n for the chat-memory table (n8n creates it automatically on first run).

## 2. Import

1. n8n → **Workflows** → **Import from file** → `workflows/answer-from-vector-v2.sanitized.json`.
2. Do **not** import the raw export; it contains real resource IDs.

## 3. Credentials to attach

| Node | Credential | Notes |
|---|---|---|
| Telegram Trigger | Telegram account A | receiving bot |
| Get a file / Send text / Send audio | Telegram account(s) | the export references two different bots — put them in the same chat or unify to one credential |
| Transcribe / Generate audio / Embeddings / Chat Model / Analyze image | OpenAI | native LangChain nodes handle auth via credentials |
| Supabase Vector Store1 / SearchFamilyInfo / GetUserRecord | Supabase | table `documents` must exist |
| Postgres Chat Memory1 | Postgres | session key = Telegram `chat.id` |
| Download file | Google Drive OAuth2 | replace `<REPLACE_WITH_DRIVE_FOLDER_ID>` and point to your own PDF |

## 4. Placeholders in the sanitized JSON

- `<REPLACE_WITH_SHEET_ID>` — optional logging sheet (the node is disabled by default)
- `<REPLACE_WITH_FILE_ID>` — the Drive file you want to ingest into the vector store
- `<YOUR_EMAIL>` — used by the disabled Gmail node if you enable it

## 5. Seed the vector store

The ingestion branch (`Download file → Default Data Loader1 + Embeddings OpenAI → Supabase Vector Store1`) has **no trigger**. Select those nodes and run them manually once, then verify rows exist in the `documents` table.

## 6. Test

Send the bot:
- a plain text question → agent answers with retrieved context;
- a voice note (`audio/ogg`) → transcribed, answered, and replied with an opus audio file;
- a photo → OCR'd then answered.

Messages of any other type (PDF, sticker) currently do nothing because Switch1 has no fallback rule.

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Agent answers generically | vector store empty or wrong table | run ingestion; check the `documents` table name |
| Voice note ignored | Switch1 rule expects `message.voice.mime_type == "audio/ogg"` | confirm Telegram sends voice (not a file) |
| `Get a file` fails | second bot credential not in the chat | use one bot for receive and fetch |
| No memory between messages | Postgres memory table missing or session key mismatch | verify `sessionKey = {{ $json.chat.id }}` |

## 8. Error handling

The workflow has no error branch of its own. Attach the companion [Error Handler workflow](https://github.com/bandarsiri2026/bewerbung-automation/blob/main/workflows/error-handler.sanitized.json) as this workflow's **Settings → Error Workflow** so failures are reported on Telegram.
