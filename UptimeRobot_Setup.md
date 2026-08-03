# UptimeRobot Setup — Keep Render Engine Awake (5 min)

> **Purpose**: Render's free tier sleeps your service after 15 min of no traffic.
> Cold-starts take 30-60 sec. UptimeRobot pings your engine every 14 min
> so it stays warm. Free tier = 50 monitors, more than enough.

---

## Step 1 — Sign up (2 min)

1. Open https://uptimerobot.com
2. Click **Register for FREE**
3. Use the same email as your Render account (ambdambd200@gmail.com or whatever you used)
4. Verify email
5. Log in

## Step 2 — Add monitor (2 min)

1. Click **+ Add New Monitor**
2. Fill in:
   - **Monitor Type**: `HTTP(s)`
   - **Friendly Name**: `AI Automation Engine`
   - **URL (or IP)**: `https://ai-automation-engine.onrender.com/health`
     - Replace with your actual Render URL (find it in Render dashboard → your service → top of page)
   - **Monitoring Interval**: `14 minutes` (free tier minimum — but this is fine; Render sleeps at 15 min)
3. Click **Create Monitor**

## Step 3 — Confirm (1 min)

1. After 2-3 minutes, the monitor should show **Up** in green
2. Click the monitor → **Logs** tab to see the first ping succeed
3. Done. UptimeRobot will ping your engine every 14 min, forever, for free.

---

## What this does

```
Every 14 min:
  UptimeRobot → GET https://ai-automation-engine.onrender.com/health
  Render      → engine responds 200, "engine: AI Automation Engine"
  Render      → idle timer resets (won't sleep)

If engine crashes:
  UptimeRobot → pings fail
  UptimeRobot → sends you an email alert (after 2-3 failed pings)
  You         → check Render dashboard → restart service
```

## What this does NOT do

- ❌ Doesn't auto-restart Render if it crashes (you'll get an email, restart manually)
- ❌ Doesn't scale Render beyond free tier (512MB RAM, 0.1 CPU — fine for our use case)
- ❌ Doesn't add HTTPS (Render gives you HTTPS by default at `*.onrender.com`)

## Useful URLs after setup

- **Monitor dashboard**: https://uptimerobot.com/dashboard
- **Public status page** (optional, shareable): UptimeRobot → monitor → Settings → "Public Status Page" → enable
  - Use this URL on your Upwork profile / portfolio: shows clients you're reliable
  - Example: `https://stats.uptimerobot.com/xxxxx`

## After deploy — verify

```powershell
# Local check (should return engine JSON)
curl https://ai-automation-engine.onrender.com/health

# From keyhub
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" keyhub_client.py --prompt "ping"
```

If you get a 502 or timeout on first call: it's the cold-start, wait 30-60 sec and retry.
Render spins down the service after 15 min idle, so the first request always takes longer.
