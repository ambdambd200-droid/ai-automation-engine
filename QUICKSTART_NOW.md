# Daily Freelance — Quick Start

## الآن (Now) — نسخة جاهزة للتشغيل

كل شي مكتوب جاهز — أنت تنفّذ 3 أوامر وكل واحدة تاخذ 5-15 دقيقة.

### 1. سجل في n8n Community (5-10 دقائق)

```powershell
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" signup_n8n_community.py
```

**ما يصير:**
- يفتح Chromium
- يفتح community.n8n.io
- يطلب منك: "Sign Up" → "Sign in with Google" → اختار `salim.muhammad.work0@gmail.com` (مع zero)
- كمّل Google OAuth (CAPTCHA يدوي)
- أكّد البريد (verification email)
- اضغط ENTER في التيرمينال → الـ session يتحفط في `sessions/n8n_community.json`

### 2. بعد التأكيد، انشر 3 ردود في n8n Community

```powershell
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" post_n8n_replies.py
```

**ما يصير:**
- يحمّل الـ session
- يفتح community.n8n.io (مسجّل دخول تلقائياً)
- يدخل 3 مواضيع → يلصق الـ 3 ردود من `Temp/n8n_replies/`
- يأخذ screenshot بعد كل رد

### 3. سجل في Mostaql + Nafezly (15-20 دقيقة)

```powershell
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" signup_arabic_platforms.py signup
```

**ما يصير:**
- Mostaql: يفتح mostaql.com/register → عبّي الاسم/الإيميل/الباسورد → اضغط ENTER → Submit يدوي → أكّد البريد → ENTER لحفظ الـ session
- Nafezly: نفس الشي لـ nafezly.com/register
- 2 sessions منفصلة: `sessions/mostaql.json` و `sessions/nafezly.json`

### 4. بعد التأكيد، عبّي الـ profile

```powershell
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" signup_arabic_platforms.py profile
```

**ما يصير:**
- يفتح Mostaql profile → عبّي bio + skills + rate → اضغط Save يدوي
- نفس الشي لـ Nafezly profile

### 5. أول جولة bids (3 عروض لكل منصة)

```powershell
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" run_daily_freelance.py
```

**ما يصير:**
- Mostaql: يبحث عن مشاريع → يولّد 3 عروض بـ AI → يلصقها في forms → Submit يدوي
- Nafezly: نفس الشي
- n8n: ينشر 1 رد من الـ 3 (يدوي)

---

## يومياً (Daily) — Routine

```powershell
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" run_daily_freelance.py
```

هذا يعمل كل شي تلقائياً:
- 3 عروض Mostaql
- 3 عروض Nafezly
- 1-2 رد في n8n Community

**حدود يومية:**
- Mostaql: 3 bids
- Nafezly: 3 bids
- n8n Community: 2 replies

---

## أسبوعياً (Weekly) — Portfolio

```powershell
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" create_portfolio.py portfolio nafezly
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" create_portfolio.py service nafezly
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" create_portfolio.py portfolio mostaql
```

كل واحد يفتح صفحة الإنشاء، يولّد الـ copy بالـ AI، يلصقها، يطلب منك ترفع الصورة → اضغط Save يدوي.

---

## ⚠️ مهم — لازم تعمل هالأشياء أولاً

### A. تأكد Render عنده آخر نسخة

بعد ما عدّلت workflows في `ai-automation-engine/workflows/`، لازم Render يدير Manual Deploy عشان يحمّل الجديد. ادخل:
https://dashboard.render.com → ai-automation-engine → Manual Deploy → Deploy latest commit

### B. تأكد GROQ_API_KEY موجود

```powershell
$key = [System.Environment]::GetEnvironmentVariable("GROQ_API_KEY", "User")
Write-Output "GROQ key length: $($key.Length)"
```

لو 0، شغّل:
```powershell
[System.Environment]::SetEnvironmentVariable("GROQ_API_KEY","gsk_your_key","User")
```

### C. تأكد Playwright + Chromium مثبّتين

```powershell
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" -c "import playwright; print('playwright OK')"
Test-Path "C:\Users\A\AppData\Local\ms-playwright\chromium-1223\chrome-win\chrome.exe"
```

---

## 📁 الملفات المهمة (أسماء وحفظ)

```
C:\Users\A\Desktop\Money\
├── session_manager.py            ← يحفظ الـ sessions
├── signup_n8n_community.py       ← signup n8n
├── post_n8n_replies.py           ← publish 3 n8n replies
├── signup_arabic_platforms.py    ← signup Mostaql + Nafezly
├── post_arabic_bids.py           ← bids Mostaql + Nafezly
├── run_daily_freelance.py        ← master daily orchestrator
├── create_portfolio.py           ← weekly portfolio/service
├── AGENT_QUICKREF.md             ← reference
├── sessions/                     ← storage states
│   ├── mostaql.json
│   ├── nafezly.json
│   └── n8n_community.json
├── Temp/n8n_replies/             ← 3 ready drafts
│   ├── reply_1_mkitplug_figma_plugin.txt
│   ├── reply_2_easybits_linkedin_scraper.txt
│   └── reply_3_doru_gradinaru_guard_workflow.txt
└── salim_profile.json            ← identity source
```

---

## 🎯 بعد التشغيل الأول

لما تخلص signup + 3 bids + 3 n8n replies، النظام يصير تلقائي بالكامل:

- كل يوم شغّل `run_daily_freelance.py`
- كل أسبوع شغّل `create_portfolio.py portfolio nafezly` (وأي منصة ثانية)
- Engine كل يوم 4:00 UTC (7:00 Gaza) يشغّل `daily_routine` تلقائياً عبر GitHub Actions

إذا صار خطأ، شغّل `python status.py --watch` أو ارجع للـ engine dashboard:
https://ai-automation-engine.onrender.com/review
