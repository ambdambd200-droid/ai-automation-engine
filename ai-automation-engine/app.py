from flask import Flask, request, jsonify, render_template
import yaml
import os
import requests
from engine.workflow import WorkflowEngine
from storage.database import Database

app = Flask(__name__)

with open("config.yaml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

app.secret_key = (
    os.environ.get("SECRET_KEY")
    or config.get("engine", {}).get("secret_key")
    or "dev-key-change-in-production"
)
engine = WorkflowEngine(config)
engine.load_workflows()
db = engine.db


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "running",
        "engine": config.get("engine", {}).get("name"),
        "version": config.get("engine", {}).get("version"),
        "workflows": engine.list_workflows(),
    })


@app.route("/webhook/<workflow_name>", methods=["POST"])
def webhook(workflow_name):
    data = request.get_json(silent=True) or {}
    query = request.args.to_dict()
    payload = {**query, **data}

    try:
        result = engine.run_workflow(workflow_name, payload)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/workflows", methods=["GET"])
def list_workflows():
    return jsonify({"workflows": engine.list_workflows()})


@app.route("/executions", methods=["GET"])
def list_executions():
    wf = request.args.get("workflow")
    limit = request.args.get("limit", 20, type=int)
    rows = db.get_executions(wf, limit)
    return jsonify({"executions": rows})


@app.route("/trigger/<workflow_name>", methods=["GET"])
def trigger_get(workflow_name):
    data = request.args.to_dict()
    try:
        result = engine.run_workflow(workflow_name, data)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _call_groq(prompt, system, model, max_tokens, temperature):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None, "GROQ_API_KEY not set"
    model = model or "meta-llama/llama-4-scout-17b-16e-instruct"
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        return {
            "result": content,
            "provider": "groq",
            "model": model,
            "tokens_used": tokens,
        }, None
    except Exception as e:
        return None, f"Groq error: {e}"


def _call_openai(prompt, system, model, max_tokens, temperature):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None, "OPENAI_API_KEY not set"
    model = model or "gpt-4o-mini"
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        return {
            "result": content,
            "provider": "openai",
            "model": model,
            "tokens_used": tokens,
        }, None
    except Exception as e:
        return None, f"OpenAI error: {e}"


@app.route("/proxy/ai", methods=["POST"])
def proxy_ai():
    """Internal AI gateway — exposes Groq/OpenAI behind localhost:5000.

    Request:
        POST /proxy/ai
        {
            "prompt": "...",
            "system": "...",          # optional, default below
            "model": "...",            # optional, provider default
            "max_tokens": 1024,        # optional
            "temperature": 0.4,        # optional
            "provider": "auto",        # auto | groq | openai
            "caller": "hunt.py"        # optional, for log tracking
        }

    Response:
        {"result": "...", "provider": "groq", "model": "...", "tokens_used": 0}
    """
    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "prompt required"}), 400
    system = data.get("system", "You are a helpful assistant.")
    model = data.get("model")
    max_tokens = int(data.get("max_tokens", 1024))
    temperature = float(data.get("temperature", 0.4))
    provider = (data.get("provider") or "auto").lower()
    caller = data.get("caller", "unknown")

    last_err = None
    providers_to_try = []
    if provider == "groq":
        providers_to_try = ["groq"]
    elif provider == "openai":
        providers_to_try = ["openai"]
    else:
        providers_to_try = ["groq", "openai"]

    for p in providers_to_try:
        if p == "groq":
            result, err = _call_groq(prompt, system, model, max_tokens, temperature)
        else:
            result, err = _call_openai(prompt, system, model, max_tokens, temperature)
        if result:
            try:
                db.log_proxy_call(
                    result["provider"],
                    result["model"],
                    result.get("tokens_used", 0),
                    caller,
                )
            except Exception:
                pass
            return jsonify(result)
        last_err = err

    return jsonify({
        "error": f"All AI providers failed. Last error: {last_err}",
        "available_providers": [
            p for p in providers_to_try
            if os.environ.get(f"{p.upper()}_API_KEY")
        ] or ["none — set GROQ_API_KEY or OPENAI_API_KEY"],
    }), 503


@app.route("/proxy/stats", methods=["GET"])
def proxy_stats():
    days = request.args.get("days", 7, type=int)
    return jsonify({"stats": db.get_proxy_stats(days), "days": days})


@app.route("/", methods=["GET"])
def portfolio():
    return render_template("portfolio.html")


@app.route("/dashboard", methods=["GET"])
def dashboard():
    return render_template("dashboard.html")


@app.route("/review", methods=["GET"])
def review():
    return render_template("review.html")


@app.route("/demos/<filename>", methods=["GET"])
def serve_demo(filename):
    from flask import send_from_directory
    demos_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demos")
    return send_from_directory(demos_dir, filename)


@app.route("/api/contact", methods=["POST"])
def api_contact():
    """Contact form submission — writes to DB, generates AI reply, queues for review."""
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    service = data.get("service", "").strip()
    message = data.get("message", "").strip()

    if not all([name, email, service, message]):
        return jsonify({"error": "All fields required"}), 400

    if "@" not in email or "." not in email:
        return jsonify({"error": "Invalid email"}), 400

    contact_id = db.create_contact(name, email, service, message)

    # Generate AI reply immediately so it appears in review queue
    try:
        from engine.decision import decide
        decision = decide("contact_form", {
            "contact_id": contact_id,
            "name": name,
            "email": email,
            "service": service,
            "message": message,
        })
        # Run the workflow synchronously
        result = engine.run_workflow(decision["workflow"], decision["payload"])
        # Extract AI reply and save to contact
        last_exec = db.get_executions(workflow="auto_email_response", limit=1)
        if last_exec:
            exec_output = last_exec[0].get("output_data")
            if exec_output:
                import json as _json
                try:
                    parsed = _json.loads(exec_output)
                    if isinstance(parsed, dict) and ("body" in parsed or "ai_body" in parsed):
                        subj = parsed.get("subject") or parsed.get("ai_subject") or "Re: Your inquiry"
                        body = parsed.get("body") or parsed.get("ai_body") or ""
                        # Save as JSON for clean extraction in review UI
                        ai_reply_json = _json.dumps({"subject": subj, "body": body})
                        db.save_ai_response(contact_id, ai_reply_json)
                except (_json.JSONDecodeError, TypeError):
                    pass
    except Exception as e:
        # Don't fail the contact submission if AI generation fails
        print(f"[contact] AI generation failed: {e}", flush=True)

    return jsonify({
        "contact_id": contact_id,
        "message": "Message received. AI reply queued for review at /review"
    }), 201


@app.route("/api/contacts/<int:contact_id>/regenerate", methods=["POST"])
def regenerate_contact(contact_id):
    """Re-generate AI reply for a contact."""
    contact = db.get_contact(contact_id)
    if not contact:
        return jsonify({"error": "Contact not found"}), 404

    try:
        from engine.decision import decide
        decision = decide("contact_form", {
            "contact_id": contact_id,
            "name": contact["name"],
            "email": contact["email"],
            "service": contact["service"],
            "message": contact["message"],
        })
        engine.run_workflow(decision["workflow"], decision["payload"])
        last_exec = db.get_executions(workflow="auto_email_response", limit=1)
        if last_exec:
            exec_output = last_exec[0].get("output_data")
            if exec_output:
                import json as _json
                try:
                    parsed = _json.loads(exec_output)
                    if isinstance(parsed, dict) and ("body" in parsed or "ai_body" in parsed):
                        subj = parsed.get("subject") or parsed.get("ai_subject") or "Re: Your inquiry"
                        body = parsed.get("body") or parsed.get("ai_body") or ""
                        ai_reply_json = _json.dumps({"subject": subj, "body": body})
                        db.save_ai_response(contact_id, ai_reply_json)
                        return jsonify({"status": "regenerated", "ai_response": {"subject": subj, "body": body}})
                except (_json.JSONDecodeError, TypeError):
                    pass
        return jsonify({"status": "regenerated", "note": "AI response generated but extraction failed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/contacts", methods=["GET"])
def list_contacts():
    """List contact submissions — for the dashboard review queue."""
    pending_only = request.args.get("pending", "true").lower() == "true"
    contacts = db.list_contacts(pending_only=pending_only)
    return jsonify({"contacts": contacts})


@app.route("/api/contacts/<int:contact_id>/approve", methods=["POST"])
def approve_contact(contact_id):
    """Approve a contact's auto-generated response and send it."""
    data = request.get_json(silent=True) or {}
    response_text = data.get("response", "").strip()

    if not response_text:
        return jsonify({"error": "Response text required"}), 400

    contact = db.get_contact(contact_id)
    if not contact:
        return jsonify({"error": "Contact not found"}), 404

    try:
        from engine.send_email_lib import send_email
        send_email(
            to=contact["email"],
            subject=contact.get("subject") or f"Re: Your message",
            body=response_text,
            dry_run=False,
        )
        db.mark_contact_sent(contact_id, response_text)

        # Fire-and-forget notification to n8n webhook (Telegram bridge)
        n8n_webhook = os.environ.get("N8N_NOTIFY_WEBHOOK")
        if n8n_webhook:
            try:
                requests.post(
                    n8n_webhook,
                    json={
                        "type": "contact_sent",
                        "status": "sent",
                        "contact": {
                            "name": contact["name"],
                            "email": contact["email"],
                            "service": contact["service"],
                            "message": contact["message"],
                        },
                    },
                    timeout=5,
                )
            except Exception as notify_err:
                print(f"[notify] n8n webhook failed: {notify_err}", flush=True)

        return jsonify({"status": "sent", "contact_id": contact_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/decide", methods=["POST"])
def api_decide():
    """Decision Engine — map a task_type to a workflow + payload."""
    from engine.decision import decide, decide_from_email, decide_for_followup

    data = request.get_json(silent=True) or {}
    task_type = data.get("task_type", "").strip()

    if not task_type:
        return jsonify({"error": "task_type required"}), 400

    if task_type == "from_email":
        result = decide_from_email(
            subject=data.get("subject", ""),
            body=data.get("body", ""),
            sender=data.get("sender", ""),
        )
    elif task_type == "for_followup":
        result = decide_for_followup(data.get("contact", {}))
    else:
        result = decide(task_type, data.get("input_data", {}))

    return jsonify(result)


@app.route("/api/task-types", methods=["GET"])
def api_task_types():
    """List all registered task types."""
    from engine.decision import list_task_types
    return jsonify({"task_types": list_task_types()})


@app.route("/api/hunt_event", methods=["POST"])
def api_hunt_event():
    """Receive notifications from hunt.py when items are sent.

    Stores in DB for stats. Future: trigger skill auto-learning.
    """
    data = request.get_json(silent=True) or {}
    item_type = data.get("type", "unknown")
    recipient = data.get("recipient", "")
    subject = data.get("subject", "")
    source = data.get("source", "")

    try:
        db.log_hunt_event(item_type, recipient, subject, source, data.get("body", ""))
        return jsonify({"status": "logged"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/bid/generate", methods=["POST"])
def api_bid_generate():
    """Generate an Arabic bid for Nafezly/Mostaql from a project description."""
    data = request.get_json(silent=True) or {}
    platform = data.get("platform", "").strip()
    project_title = data.get("project_title", "").strip()
    project_description = data.get("project_description", "").strip()
    budget = data.get("budget", "").strip()
    suggested_price = data.get("suggested_price", "").strip()

    if not platform or platform not in ("nafezly", "mostaql"):
        return jsonify({"error": "platform must be 'nafezly' or 'mostaql'"}), 400
    if not project_title or not project_description:
        return jsonify({"error": "project_title and project_description required"}), 400

    try:
        from datetime import datetime
        result = engine.run_workflow("arabic_bid_generator", {
            "platform": platform,
            "project_title": project_title,
            "project_description": project_description,
            "budget": budget,
            "suggested_price": suggested_price,
            "trigger_date": datetime.utcnow().isoformat() + "Z",
        })
        last_exec = db.get_executions(workflow="arabic_bid_generator", limit=1)
        if last_exec and last_exec[0].get("output_data"):
            import json as _json
            parsed = _json.loads(last_exec[0]["output_data"])
            return jsonify(parsed)
        return jsonify({"status": "generated", "execution_id": result["execution_id"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/n8n/reply", methods=["POST"])
def api_n8n_reply():
    """Generate an n8n Community forum reply draft."""
    data = request.get_json(silent=True) or {}
    thread_url = data.get("thread_url", "").strip()
    thread_title = data.get("thread_title", "").strip()
    thread_author = data.get("thread_author", "").strip()
    thread_context = data.get("thread_context", "").strip()

    if not thread_title or not thread_context:
        return jsonify({"error": "thread_title and thread_context required"}), 400

    try:
        from datetime import datetime
        result = engine.run_workflow("n8n_community_publisher", {
            "thread_url": thread_url,
            "thread_title": thread_title,
            "thread_author": thread_author,
            "thread_context": thread_context,
            "trigger_date": datetime.utcnow().isoformat() + "Z",
        })
        last_exec = db.get_executions(workflow="n8n_community_publisher", limit=1)
        if last_exec and last_exec[0].get("output_data"):
            import json as _json
            parsed = _json.loads(last_exec[0]["output_data"])
            return jsonify(parsed)
        return jsonify({"status": "generated", "execution_id": result["execution_id"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/hunt_events", methods=["GET"])
def api_hunt_events():
    """List recent hunt events."""
    limit = request.args.get("limit", 50, type=int)
    events = db.list_hunt_events(limit)
    return jsonify({"events": events})


if __name__ == "__main__":
    port = config.get("server", {}).get("port", 5000)
    host = config.get("server", {}).get("host", "0.0.0.0")
    app.run(host=host, port=port, debug=False)
