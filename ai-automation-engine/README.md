# AI Automation Engine

Self-hosted automation engine built with Python and Flask.  
Accepts webhooks, runs AI-powered workflows, stores execution history.

## Quick Start

```bash
pip install -r requirements.txt
set OPENAI_API_KEY=sk-your-key-here
python app.py
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Engine status + loaded workflows |
| POST | `/webhook/<workflow>` | Trigger a workflow |
| GET | `/trigger/<workflow>` | Trigger via query params |
| GET | `/workflows` | List all workflows |
| GET | `/executions` | View execution history |

## Workflows

Place `.yaml` files in `workflows/` directory.  
See `workflows/lead_capture.yaml` for an example.
