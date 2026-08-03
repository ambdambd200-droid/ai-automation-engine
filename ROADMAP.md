# ROADMAP — الخطة الشاملة من البداية للنهاية

> مستند واحد يجمع كل شيء: يلي سويناه صح ✅ و يلي لسا ناقص □
> نشتغل عليهم بالترتيب تحت لنخلص كل شيء.

---

## 🎯 الهدف النهائي (ما بنحيد عنه أبداً)

**"أقول شيء يلي بدي اياه و في نظام يسويه من دون م المس جهاز"**
- نظام ياخد طلب → يتعلمه → ينفذه → يخزن المهارة
- خصوصية و حماية تامة
- كله مجاني (Skills + Groq + Render)
- خفيف على الجهاز (4GB RAM, i5-4200U)
- متصل بشبكة وحدة (engine + keyhub + skills + أنا AI)

---

# 🟢 المرحلة 0: التأسيس (اكتملت ✅)

| # | الخطوة | الحالة | ملاحظات |
|---|--------|--------|---------|
| 0.1 | GitHub README (3 مشاريع بمقاييس) | ✅ | `README.md` |
| 0.2 | LinkedIn Profile (عربي + إنجليزي) | ✅ | `LinkedIn_Profile_Content.md` |
| 0.3 | LinkedIn Post 1 (Intro) منشور | ✅ | تم النشر يدوي |
| 0.4 | AI Automation Engine (Flask + Python) | ✅ | `ai-automation-engine/`, port :5000 |
| 0.5 | AGENTS.md (هيكل + أمان + أوامر) | ✅ | محدّث ومصادق |
| 0.6 | Auto-start (VBS في Startup) | ✅ | engine يشتغل تلقائياً عند تسجيل الدخول |
| 0.7 | Portfolio Projects (3 مشاريع) | ✅ | dashboard, lead_capture, automation engine |
| 0.8 | السيرة الذاتية CV (عربي + إنجليزي) | ✅ | `Alaa_Fathi_CV.md` |
| 0.9 | Proposal Templates (3 نماذج) | ✅ | `Proposal_Templates.md` |
| 0.10 | Upwork Profile Content | ✅ | `Upwork_Profile_Content.md` |
| 0.11 | LinkedIn Posts Series (3 posts Jun 5/8/12) | ✅ | `LinkedIn_Posts_Series.md` |

# 🟢 المرحلة 1: أول 6 تطبيقات + الأنظمة الداخلية (اكتملت ✅)

| # | الخطوة | الحالة | ملاحظات |
|---|--------|--------|---------|
| 1.1 | 6 تطبيقات (Jun 1): ZY IMMO, Asiacruit, Synergy, n8nera, nocodecreative, Nikolaos | ✅ | كلها أرسلت عبر Gmail SMTP |
| 1.2 | AI-OS-Agent على Groq (meta-llama/llama-4-scout) | ✅ | `app_groq.py` + MCP |
| 1.3 | AI-OS-Agent: تحسينات (mouse, Type, Alt+Tab, coords validation) | ✅ | privacy mode ON |
| 1.4 | النظام الداخلي (Application_Pipeline, Protocols, Job_Queue, Prompt_Library, .gitignore) | ✅ | 10+ ملفات |
| 1.5 | Gmail check (IMAP, per-recipient) | ✅ | `gmail_check.py` + `gmail_log.md` |
| 1.6 | Email follow-ups (Jun 7) — 6 رسائل متابعة | ✅ | عبر `hunt.py --execute` |
| 1.7 | نصميم الكود لكل `gmail_check.py` (fix IMAP `OR` query) | ✅ | كان مكسور، صار per-recipient |
| 1.8 | Playwright Chromium مثبّت | ✅ | `chromium-1223` |
| 1.9 | `gmail_setup_check.py` + GMAIL_APP_PASSWORD | ✅ | بيئة OS-level |

# 🟢 المرحلة 2: 3 منصات عربية (لـسا)

| # | الخطوة | الحالة | ملاحظات |
|---|--------|--------|---------|
| 2.1 | Mostaql_Setup.md (دليل التسجيل + الملف الشخصي) | ✅ | الملف موجود، جاهز |
| 2.2 | Nafezly_Setup.md (دليل التسجيل + خدمة $25) | ✅ | الملف موجود، جاهز |
| 2.3 | Arabic_Bid_Templates.md (5 قوالب عروض) | ✅ | الملف موجود، جاهز |
| 2.4 | `signup_arabic_platforms.py` (Playwright للتسجيل) | ✅ | السكربت موجود |
| | | | |
| □ 2.5 | **التسجيل في مستقل** (mostaql.com) | ⬜ **معلق** | CAPTCHA, user manual |
| □ 2.6 | **التسجيل في نفذلي** (nafezly.com) | ⬜ **معلق** | user manual, timing? |
| □ 2.7 | **تفعيل البريد الإلكتروني** لكل منصة | ⬜ **معلق** | user action |
| □ 2.8 | **إكمال الملف الشخصي** (نصوص جاهزة) | ⬜ **معلق** | user or desktop_runner |
| □ 2.9 | **إضافة معرض الأعمال** (3 مشاريع) | ⬜ **معلق** | user manual |
| □ 2.10 | **أول 3 عروض على مستقل** | ⬜ **معلق** | استخدم `Arabic_Bid_Templates.md` |
| □ 2.11 | **أول 3 عروض على نفذلي** | ⬜ **معلق** | استخدم `Arabic_Bid_Templates.md` |
| □ 2.12 | **نشر أول خدمة على نفذلي** ($25 n8n workflow) | ⬜ **معلق** | استخدم `service_page/nafezly` skill |

# 🟢 المرحلة 3: n8n Community Forum (ناقصة لسا)

| # | الخطوة | الحالة | ملاحظات |
|---|--------|--------|---------|
| 3.1 | 3 مسودات ردود (mkitplug, easybits, Doru_Gradinaru) | ✅ | `Application_N8N_Community_*.md` |
| 3.2 | `post_forum_replies.py` (سكربت Playwright للنشر) | ✅ | مع user confirmation |
| 3.3 | `apply_now.py` (يفتح 3 روابط في Brave) | ✅ | جاهز |
| 3.4 | `hunt.py` فيه forum posting logic | ✅ | عبر `phase_n8n_forum()` + Playwright |
| | | | |
| □ 3.5 | **تسجيل الدخول** في community.n8n.io | ⬜ **معلق** | كان مسجل، بس الجلسة انتهت |
| □ 3.6 | **نشر الردود الثلاثة** | ⬜ **معلق** | المشكلة: Playwright يفتح browser جديد → Google OAuth يعمل reset |
| □ 3.7 | **حل مشكلة Google OAuth** | ⬜ **معلق** | الحل: `--brave-profile` (يقفل Brave أولاً) |

# 🟢 المرحلة 4: Skills Library (اكتملت ✅)

| # | الخطوة | الحالة | ملاحظات |
|---|--------|--------|---------|
| 4.1 | `skills/manager.py` (300+ سطر) | ✅ | read/find/apply/save/learn |
| 4.2 | `skills/index.json` — فهرس 12 مهارة | ✅ | 6 starter + 6 new |
| 4.3 | `try_skill()` في hunt.py (3 مولّدات) | ✅ | يشتغل قبل AI — يقلل API calls ~50% |
| 4.4 | 6 مهارات أساسية: mostaql, nafezly, english_followup, english_reply, technical_n8n, showcase | ✅ | 
| 4.5 | 6 مهارات جديدة: arabic_reply, arabic_followup, linkedin_connect, upwork_cover, service_page, cold_pitch | ✅ | 
| 4.6 | **Autosave hook** (record_learned_skill) | ✅ | كل send ناجح = skill جديد |
| 4.7 | **`--learn` mode** (hunt.py) | ✅ | يقرأ hunt_decisions.md ويحفظ |
| 4.8 | Dedup fix (counter_bodyhash في الملف) | ✅ | نفس الثانية = ما يحذف بعض |

# 🟢 المرحلة 5: AI Gateway + Proxy (اكتملت ✅)

| # | الخطوة | الحالة | ملاحظات |
|---|--------|--------|---------|
| 5.1 | `POST /proxy/ai` في engine | ✅ | Groq first → OpenAI fallback |
| 5.2 | `GET /proxy/stats` في engine | ✅ | إحصائيات الاستخدام |
| 5.3 | جدول proxy_calls في SQLite | ✅ | يسجل كل نداء |
| 5.4 | `keyhub_client.py` — البوابة الداخلية | ✅ | engine → Groq → Ollama fallback |
| 5.5 | GROQ_API_KEY في OS User level | ✅ | engine يرثها تلقائياً |

# 🟢 المرحلة 6: Render.com Deployment (ناقصة لسا)

| # | الخطوة | الحالة | ملاحظات |
|---|--------|--------|---------|
| 6.1 | `render.yaml` (Blueprint) | ✅ | 
| 6.2 | `Procfile` (waitress-serve) | ✅ | gunicorn → waitress (Windows compat) |
| 6.3 | `runtime.txt` (python-3.12.0) | ✅ |
| 6.4 | `DEPLOY_RENDER.md` (8 خطوات) | ✅ |
| 6.5 | `app.py` يقرأ SECRET_KEY من env var | ✅ |
| 6.6 | Habid: waitress على :8000 → /health 200 | ✅ |
| 6.7 | حساب Render.com مسجل | ✅ |
| | | | |
| □ 6.8 | **GitHub Desktop: publish ai-automation-engine/ إلى GitHub** | ⬜ **معلق** | user action |
| □ 6.9 | **Render: ربط GitHub repo + نشر Blueprint** | ⬜ **معلق** | user action |
| □ 6.10 | **إضافة env vars في Render (GROQ_API_KEY, OPENAI_API_KEY, SECRET_KEY)** | ⬜ **معلق** | user action |
| □ 6.11 | **اختبار** `https://ai-automation-engine.onrender.com/health` | ⬜ **معلق** | user action |
| □ 6.12 | **ضبط ENGINE_URL** على الجهاز المحلي | ⬜ **معلق** | بعد ما Render يشتغل |
| □ 6.13 | **Smoke test**: `python keyhub_client.py --stats` | ⬜ **معلق** | بعد Render |

# 🟢 المرحلة 7: Quota System (اكتملت ✅)

| # | الخطوة | الحالة | ملاحظات |
|---|--------|--------|---------|
| 7.1 | `quota.py` (172 سطر) | ✅ | can_send, record_sent, get_remaining |
| 7.2 | 8 حصص يومية (replies, followups, mostaql_bids, nafezly_bids, forum_replies, upwork_applies, linkedin_connects, emails_sent) | ✅ |
| 7.3 | `QUOTA_<ACTION>` env var override | ✅ |
| 7.4 | CLI: --status, --reset, --set, --check | ✅ |
| 7.5 | Auto-reset at midnight | ✅ |

# 🟢 المرحلة 8: UptimeRobot (ناقصة لسا)

| # | الخطوة | الحالة | ملاحظات |
|---|--------|--------|---------|
| 8.1 | `UptimeRobot_Setup.md` (3 خطوات) | ✅ | الدليل جاهز |
| □ 8.2 | **التسجيل في UptimeRobot.com** (مجاني) | ⬜ **معلق** | 5 دقائق |
| □ 8.3 | **إضافة Monitor**: `https://ai-automation-engine.onrender.com/health` | ⬜ **معلق** | بعد ما Render يشتغل |
| □ 8.4 | **اختبار** (يظهر Up خلال 2-3 دقائق) | ⬜ **معلق** | user action |

# 🟢 المرحلة 9: Ollama (مُؤجّل)

| # | الخطوة | الحالة | ملاحظات |
|---|--------|--------|---------|
| 9.1 | كود Ollama في keyhub_client.py | ✅ | جاهز (engine → Groq → Ollama chain) |
| 9.2 | `_ollama_alive()` + `_call_ollama()` | ✅ | جاهز |
| 9.3 | CLI: --ollama-status, --ollama-only, --provider | ✅ | جاهز |
| | | | |
| □ 9.4 | تثبيت Ollama على الجهاز | ⏸️ **مؤجّل** | يحتاج شبكة أسرع (1.4GB installer) |
| □ 9.5 | تحميل موديل صغير (qwen2.5:0.5b = 470MB) | ⏸️ **مؤجّل** | أو phi-3-mini 2.3GB إذا صار في مساحة |

# 🟢 المرحلة 10: الـ 6 تطبيقات المباشرة (فشلت — حُذفت)

| # | الخطوة | الحالة | ملاحظات |
|---|--------|--------|---------|
| 10.1 | Make.com (recruitee) | ❌ فشل | الموقع ما قبل Apply |
| 10.2 | Mindrift (Workable) | ❌ فشل | 403 / ما قبل |
| 10.3 | Hireza | ❌ فشل | يرجع لنفس الصفحة |
| 10.4 | Sagan Recruitment (Typeform) | ❌ محظور | يحتاج فيديو دقيقة — المستخدم رفض |
| 10.5 | 4 ملفات Application_*.md حُذفت | ✅ |

# 🟢 المرحلة 11: الـ 6 متابعات (All sent, zero replies)

| # | الخطوة | الحالة | ملاحظات |
|---|--------|--------|---------|
| 11.1 | Follow-up to: info@zyimmo.de | ✅ | Jun 7 |
| 11.2 | Follow-up to: careers@asiacruit.com | ✅ | Jun 7 |
| 11.3 | Follow-up to: info@s-e.lt | ✅ | Jun 7 |
| 11.4 | Follow-up to: n8nera@gmail.com | ✅ | Jun 7 |
| 11.5 | Follow-up to: wayne@nocodecreative.io | ✅ | Jun 7 |
| 11.6 | Follow-up to: folafoluwaolaneye@gmail.com | ✅ | Jun 7 |
| □ 11.7 | متابعة جديدة (بعد أسبوع من 11.1-6) | ⬜ **معلق** | Jun 14-15 تقريباً |

# 🟢 المرحلة 12: AI-OS-Agent + MCP (لسا محتاج شغل)

| # | الخطوة | الحالة | ملاحظات |
|---|--------|--------|---------|
| 12.1 | app_groq.py (Groq desktop control) | ✅ | مع coordinate validation |
| 12.2 | mcp_server.py (MCP server) | ✅ | يستورد من app_groq |
| 12.3 | opencode.jsonc (MCP entry) | ✅ | لكن MCP tools مش في session الحالي |
| 12.4 | Privacy mode (blur sensitive areas) | ✅ | 
| 12.5 | mouse moveTo (بطيء مرئي), Type (سريع) | ✅ |
| 12.6 | AI_OS_SWITCH_WINDOW (Alt+Tab) | ✅ |
| | | | |
| □ 12.7 | **openCode restart** → MCP tools يظهرون | ⬜ **معلق** | يحتاج المستخدم يقفل ويفتح |
| □ 12.8 | اختبار MCP: screenshot + CLICK فعلي | ⬜ **معلق** | 
| □ 12.9 | حل مشكلة terminal focus (بعد bash يرجع terminal) | ⬜ **معلق** |

---

# 📋 الخطة — من الحين ورايح (تنفيذ متسلسل)

> ترتيب: □ → ✅ → □ → ✅ ... بدون توقف إلا إذا في سؤال

## 🔴 Immediate (المستخدم ينفذها)

```
□ 1. [أنت] Render deploy:
   - GitHub Desktop → Publish ai-automation-engine/ 
   - Render Dashboard → ربط الـ repo
   - إضافة env vars: GROQ_API_KEY, OPENAI_API_KEY, SECRET_KEY
   - انتظر build → اختبر /health
   - قلي لما يشتغل

□ 2. [أنت] UptimeRobot signup (5 دقائق):
   - UptimeRobot_Setup.md → اتبع الخطوات
   - أضف Monitor: https://ai-automation-engine.onrender.com/health

□ 3. [أنت] التسجيل في مستقل + نفذلي:
   - اتبع Mostaql_Setup.md و Nafezly_Setup.md
   - أو شغّل: python signup_arabic_platforms.py signup
   - فعّل البريد الإلكتروني

□ 4. [أنت] n8n Community forum:
   - سجل دخول في community.n8n.io
   - شغّل: python hunt.py --execute
   - (أو: اقفل Brave → شغّل --brave-profile)
```

## 🔵 بعد ما تخلص الـ 4 فوق (أنا أنفذها)

```
□ 5. [أنا] بعد Render يشتغل → أضبط ENGINE_URL env var
     → python keyhub_client.py --stats (اختبار)

□ 6. [أنا] Smoke test كامل:
     → python hunt.py --status
     → python hunt.py --replies --no-ai
     → python hunt.py --gather --no-ai

□ 7. [أنا] Skill analytics (يتتبع أي skill يحوّل لـ hire)
     → analytics.json + python hunt.py --analytics

□ 8. [أنا] Auto-reply to inbound emails
     → إذا رد عميل، hunt.py يقراه ويسوّي رد باستخدام skill

□ 9. [أنا] Promote learned skills → main folder
     → skills/learning/*.json يلي استخدم 3+ مرات → main

□ 10. [أنا] LinkedIn post publishing helper
     → post_2 (Jun 8) و post_3 (Jun 12)
```

## 🟣 بعد ما يخلص كل شيء (الشهر الجاي)

```
□ 11. [أنت] أول 3 عروض على مستقل (استخدم Arabic_Bid_Templates.md)
□ 12. [أنت] أول 3 عروض على نفذلي
□ 13. [أنت] نشر أول خدمة على نفذلي ($25 n8n workflow)
□ 14. [أنت] نشر 3 ردود n8n Community
□ 15. [أنت] متابعة LinkedIn Post 2 (Jun 8) و Post 3 (Jun 12)
□ 16. [أنا] Tracking conversions (أي عرض جاب رد → سجل في analytics)
□ 17. [أنا] تحسين skills بناءً على analytics
```

---

# 💡 اقتراحات مستقبلية مجانية

| الفكرة | التكلفة | القيمة |
|--------|---------|--------|
| **Render cron job** — يفحص Gmail كل 14 دقيقة | $0 | ما يحتاج تشغل daily.py يدوي |
| **Render + n8n webhook** — لو عميل رد، يرسل إشعار لجوالك (Telegram Bot) | $0 | ما تفوت رد |
| **Gist backup** — skill library تنسخ احتياطي على GitHub Gist | $0 | لو ضاع الملفات |
| **Pricing skill** — يحسب السعر المناسب بناءً على مدة المشروع والأدوات | $0 | تقديم أسرع |
| **Multi-language CV** — يختار لغة السيرة حسب لغة العميل | $0 | احترافية أعلى |
| **Auto-fill profile** — يملأ ملف Mostaql/Nafezly بنصوص جاهزة | $0 | توفير وقت |
| **Keyword alert** — يراقب منصات عربية لكلمة "n8n" أو "أتمتة" ويجيب الرابط | $0 | ما يفوتك فرصة |

---

# ❌ موقفنا من "Hermes Agent"

- ❌ "Hermes Agent" كمنتج جاهز **ما موجود** — لا موقع رسمي، لا docs، لا install
- ✅ بنينا **المكافئ** له: Skills library + Render cloud + AI gateway chain
- ✅ النظام الحالي: ياخد طلب → يستخدم skill (أو Groq) → ينفذ → يحفظ المهارة
- ✅ هذا أحسن من Hermes لأني أنا (AI) في الحلقة — أفهم، أقرر، أكتب المحتوى بنفسي

---

# 📊 الوضع النهائي (اليوم)

```
بينات عامة:
- Skills: 28 (12 starter + 16 learned)
- Engine: محلي على :5000 ✓
- Render: مسجل، يحتاج نشر
- إيميلات مرسلة: 6 أولية (Jun 1) + 6 متابعات (Jun 7)
- ردود: 0/6 (لسا)
- منصات عربية: 0/2 مسجل
- n8n Community: 0/3 منشور
- Ollama: مؤجل
- MCP: يحتاج restart
- quota.py: شغال ✓
- --learn mode: شغال ✓
- autosave hook: شغال ✓
```
