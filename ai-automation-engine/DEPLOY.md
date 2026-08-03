# Deployment Guide — PythonAnywhere

## Step 1: Upload the code

**Option A — Upload files directly:**
1. Log in to [pythonanywhere.com](https://www.pythonanywhere.com)
2. Go to **Files** tab
3. Create a directory: `ai-automation-engine`
4. Upload all project files into it:
   - `app.py`, `wsgi.py`, `config.yaml`, `requirements.txt`
   - `engine/` (upload as folder)
   - `storage/` (upload as folder)
   - `workflows/` (upload as folder)
   - `.gitignore`

**Option B — Use Git (if repo is pushed):**
1. Open a **Bash console** from the PythonAnywhere dashboard
2. Clone: `git clone https://github.com/alaafathi/ai-workflow-portfolio.git`

## Step 2: Create virtual environment

In the Bash console:
```bash
cd ai-automation-engine
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 3: Configure WSGI

1. Go to **Web** tab
2. Add new web app → **Manual configuration** → Python 3.12
3. In the **Code** section, set:
   - **Source code:** `/home/alaafathi/ai-automation-engine`
   - **Working directory:** `/home/alaafathi/ai-automation-engine`
   - **WSGI configuration file:** Click the link and replace its content with:

```python
import sys
import os

path = '/home/alaafathi/ai-automation-engine'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['OPENAI_API_KEY'] = 'sk-your-actual-key'

from app import app as application
```

## Step 4: Set environment variable

1. In the **Web** tab → **Environment variables** (under Code)
2. Add:
   - **Variable:** `OPENAI_API_KEY`
   - **Value:** `sk-proj-XGPXWzbLUk...your-full-key`

## Step 5: Reload

1. Scroll to top of **Web** tab
2. Click **Reload**
3. Wait 10 seconds

## Step 6: Test

Visit: `https://alaafathi.pythonanywhere.com/health`

Expected response:
```json
{"status":"running","engine":"AI Automation Engine","version":"1.0.0","workflows":["data_pipeline","lead_capture"]}
```

## Trigger a workflow

```bash
curl -X POST https://alaafathi.pythonanywhere.com/webhook/lead_capture \
  -H "Content-Type: application/json" \
  -d '{"name":"Client Name","email":"client@email.com","company":"Company","message":"Need automation"}'
```

---

## Result

Your AI Automation Engine is now live at:
**https://alaafathi.pythonanywhere.com/**
