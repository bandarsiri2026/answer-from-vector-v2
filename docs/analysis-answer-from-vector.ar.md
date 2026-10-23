# تحليل Workflow B — Answer from vector v2 (مساعد RAG متعدد الوسائط)

## 1. البنية العامة للتدفق (25 عقدة)

**تنبيه مهم تم التحقق منه من الملف:** ثلاث عقد مكتوبة `"disabled": true` وهي: `Append row in sheet`، `Send a message` (Gmail)، و`GetUserRecord`. لذلك **لا يتم إرسال بريد ولا تسجيل في Sheets** فعليًا رغم وجود العقد — وهذا مثال على ضرورة عدم الحكم من اسم العقدة.

### 1.1 Telegram Trigger (v1.2)
- `updates: ["message"]`، `additionalFields.download: true` → المرفقات (الصوت/الصورة) تُنزَّل كـ binary داخل مخرجات الـ trigger.
- هذا الإعداد هو ما يجعل `Analyze image` يعمل لاحقًا بدون خطوة تنزيل إضافية.

### 1.2 Switch1 (v3.3، وضع Rules)
ثلاث قواعد تُقيَّم بالترتيب:
| القاعدة | الشرط | الوجهة |
|---|---|---|
| 0 | `message.text` موجود | AI Agent1 مباشرة |
| 1 | `message.voice.mime_type == "audio/ogg"` | Get a file → Transcribe a recording → AI Agent1 |
| 2 | `message.photo[0]` موجود | Analyze image → AI Agent1 |

**لا توجد قاعدة fallback** → لو أرسل المستخدم ملف PDF مثلًا، لا يحدث شيء.

### 1.3 Get a file (Telegram) + Transcribe a recording (OpenAI)
- Get a file: `resource: file`، `fileId = {{ $json.message.voice.file_id }}` باستخدام credential **ثاني** باسم "Telegram account 2". استخدام بوت مختلف عن بوت الاستقبال قد يفشل إذا لم يكن هذا البوت في نفس الدردشة — نقطة خطر مثبتة من الإعدادات.
- Transcribe: `resource: audio`, `operation: transcribe` → مخرجات `{ text: ... }`.

### 1.4 Analyze image (OpenAI, gpt-4o-mini)
`operation: analyze`، `inputType: base64`، prompt ثابت `"Fetch text from image"` → OCR/وصف الصورة.

### 1.5 AI Agent1 (agent v3)
- `promptType: define` والنص:
  ```text
  {{ $json.message.text }} ?? {{ $json.text }} ?? {{ $json['0'].content[0].text }}
  ```
  هذه محاولة لتغطية ثلاثة أشكال مخرجات مختلفة (نص مباشر / نتيجة transcription / بنية content array). **هذه صيغة هشة**: في مسار النص تكون `$json['0']` غير موجودة، والسلوك الدقيق (سلسلة فارغة أو خطأ expression) يعتمد على إصدار n8n ولا يمكن الجزم به من الملف وحده. الأفضل استخدام Code node يوحّد المصدر.
- systemMessage يطلب استدعاء أداة قبل الإجابة عن أسئلة العائلة/البيانات الشخصية، لكنه يذكر أسماء أدوات لا تطابق الأسماء الفعلية (`SearchFamily` مقابل `SearchFamilyInfo`) ويعامل **Postgres Chat Memory** كأداة بينما هي موصولة كذاكرة (`ai_memory`) وليست أداة — أي أن التعليمات غير دقيقة عمليًا.
- المخرجات: `{ output: "..." }`.

### 1.6 العقد الموصولة بالـ Agent (_ai connections_)
- **OpenAI Chat Model** (gpt-4.1-mini) → `ai_languageModel`.
- **Postgres Chat Memory1** → `ai_memory`، بمفتاح جلسة = chat.id و contextWindowLength = 10 → ذاكرة محادثة لكل مستخدم.
- **SearchFamilyInfo** (vectorStoreSupabase، وضع retrieve-as-tool على جدول `documents`) → `ai_tool`.
- **GetUserRecord** (supabaseTool، get من `documents` بشرط `id = 1`) → `ai_tool` لكنها **معطّلة**. الشرط ثابت (`=1`) أي لا يخص المستخدم الحالي — منطق غير دقيق حتى لو فُعّلت.

### 1.7 If بعد الـ Agent
يشترط وجود `message.voice` في الرسالة الأصلية:
- **true** → Generate audio (OpenAI TTS، `input: {{ $json.output }}`، `response_format: opus`) → Send an audio file (`sendAudio`, binaryData).
- **false** → Send a text message (`{{ $json.output }}` إلى chat.id) → ثم Gmail (معطّل).

منطق ذكي: إذا جاء السؤال صوتيًا، يكون الرد صوتيًا. لكن `Send an audio file` يستخدم `message.from.id` بينما العقد الأخرى تستخدم `chat.id` — في الدردشة الفردية القيمتان متطابقتان عمليًا، لكنه تناقض يستحق التصحيح.

### 1.8 فرع "Upload data to database"
`Download file` (Drive: personal_info.pdf) → `Default Data Loader1` (dataType binary) + `Embeddings OpenAI` → `Supabase Vector Store1` بوضع insert في جدول `documents` مع `queryName: data`.
**هذا الفرع غير متصل بأي trigger** — يُنفَّذ فقط عند تشغيل العقدة يدويًا. مهم جدًا لفهم "لماذا لا تُرفع البيانات تلقائيًا".

---

---

## 2. خلاصة القيود المثبتة من الملف

- الفرع الخاص برفع البيانات إلى قاعدة المتجهات **غير متصل بأي trigger**، لذا لا يعمل إلا يدويًا.
- ثلاث عقد معطّلة: `Append row in sheet`، `Send a message` (Gmail)، `GetUserRecord`.
- لا توجد قاعدة fallback في Switch1، ولا retry، ولا Error Trigger.
- صيغة prompt الـ Agent هشة لأنها تجمع ثلاثة مصادر مخرجات مختلفة في expression واحد.
- اسم الأداة المذكور في systemMessage (`SearchFamily`) لا يطابق الاسم الفعلي للعقدة (`SearchFamilyInfo`).

## 3. تحسينات مقترحة

1. إضافة قاعدة fallback في Switch1 وإرسال تنبيه للمستخدم عند عدم التطابق.
2. توحيد مصدر السؤال في Code node بدل expression متعدد المصادر.
3. تشغيل الـ ingestion عبر trigger (Drive new file أو Cron) بدل التشغيل اليدوي.
4. ربط GetUserRecord بشرط ديناميكي يعتمد على معرّف المستخدم الحالي بدل `id = 1`.
5. إضافة Error Trigger يرسل تفاصيل الفشل إلى Telegram.
