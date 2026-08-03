"""Smoke Test — full E2E validation of all engine endpoints.

Tests:
- 6 core endpoints (health, workflows, task-types, /, /review, /api/contacts)
- 4 generator endpoints (bid/generate, n8n/reply, hunt_event, decide)
- 3 workflow triggers (daily_routine, weekly_review, daily_digest)

Usage:
    python smoke_test.py
"""
import os
import sys
import json
import requests
from datetime import datetime

ENGINE_URL = os.environ.get("ENGINE_URL", "https://ai-automation-engine.onrender.com")


def log(msg, status="INFO"):
    color = {
        "PASS": "\033[92m",
        "FAIL": "\033[91m",
        "INFO": "\033[94m",
    }.get(status, "")
    reset = "\033[0m"
    print(f"{color}[{status}]{reset} {msg}", flush=True)


def test(name, fn):
    try:
        result = fn()
        log(f"{name}: {result}", "PASS" if result else "FAIL")
        return result
    except Exception as e:
        log(f"{name}: {e}", "FAIL")
        return False


def main():
    log("=" * 60, "INFO")
    log(f"  Smoke Test — {ENGINE_URL}", "INFO")
    log(f"  {datetime.utcnow().isoformat()}Z", "INFO")
    log("=" * 60, "INFO")

    results = []

    # Core endpoints
    results.append(test("/health", lambda: requests.get(f"{ENGINE_URL}/health", timeout=10).status_code == 200))
    results.append(test("/workflows", lambda: len(requests.get(f"{ENGINE_URL}/workflows", timeout=10).json().get("workflows", [])) > 0))
    results.append(test("/api/task-types", lambda: len(requests.get(f"{ENGINE_URL}/api/task-types", timeout=10).json().get("task_types", [])) > 0))
    results.append(test("/", lambda: "Salim" in requests.get(f"{ENGINE_URL}/", timeout=10).text))
    results.append(test("/review", lambda: "Review" in requests.get(f"{ENGINE_URL}/review", timeout=10).text))
    results.append(test("/api/contacts?pending=true", lambda: "contacts" in requests.get(f"{ENGINE_URL}/api/contacts?pending=true", timeout=10).text))

    # Generator endpoints (POST)
    results.append(test("POST /api/contact", lambda: "contact_id" in requests.post(f"{ENGINE_URL}/api/contact", json={
        "name": "Smoke Test",
        "email": "smoke@test.com",
        "service": "telegram_bot",
        "message": "Smoke test message for engine validation."
    }, timeout=30).text))

    results.append(test("POST /api/decide (contact_form)", lambda: "auto_email_response" in requests.post(f"{ENGINE_URL}/api/decide", json={
        "task_type": "contact_form",
        "input_data": {"name": "x", "email": "y", "service": "z", "message": "w"}
    }, timeout=10).text))

    results.append(test("POST /api/hunt_event", lambda: requests.post(f"{ENGINE_URL}/api/hunt_event", json={
        "type": "smoke_test",
        "recipient": "test@example.com",
        "subject": "Smoke Test Event"
    }, timeout=10).status_code == 201))

    results.append(test("POST /api/bid/generate", lambda: "bid_text" in requests.post(f"{ENGINE_URL}/api/bid/generate", json={
        "platform": "nafezly",
        "project_title": "نبحث عن مهندس n8n لإعداد workflow",
        "project_description": "مشروع يحتاج ربط Gmail مع WhatsApp",
        "suggested_price": "50"
    }, timeout=30).text))

    results.append(test("POST /api/n8n/reply", lambda: "reply_text" in requests.post(f"{ENGINE_URL}/api/n8n/reply", json={
        "thread_title": "How to handle rate limits in n8n HTTP node",
        "thread_author": "test_user",
        "thread_context": "I'm building a workflow that calls an API every minute and getting 429s"
    }, timeout=30).text))

    # Workflow triggers
    results.append(test("webhook daily_routine", lambda: requests.post(f"{ENGINE_URL}/webhook/daily_routine", json={
        "trigger": "smoke_test", "trigger_date": datetime.utcnow().isoformat() + "Z"
    }, timeout=30).status_code == 200))

    results.append(test("webhook weekly_review", lambda: requests.post(f"{ENGINE_URL}/webhook/weekly_review", json={
        "trigger": "smoke_test", "trigger_date": datetime.utcnow().isoformat() + "Z"
    }, timeout=30).status_code == 200))

    results.append(test("webhook arabic_bid_generator", lambda: requests.post(f"{ENGINE_URL}/webhook/arabic_bid_generator", json={
        "platform": "nafezly",
        "project_title": "test",
        "project_description": "test desc",
        "trigger_date": datetime.utcnow().isoformat() + "Z"
    }, timeout=30).status_code == 200))

    # Summary
    passed = sum(results)
    total = len(results)
    log("=" * 60, "INFO")
    log(f"  Results: {passed}/{total} passed", "INFO")
    log("=" * 60, "INFO")

    if passed == total:
        log("ALL TESTS PASSED", "PASS")
        return 0
    else:
        log(f"{total - passed} TESTS FAILED", "FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
