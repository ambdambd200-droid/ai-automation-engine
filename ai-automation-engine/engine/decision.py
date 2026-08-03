"""Decision Engine — the AI Brain.

Maps incoming tasks (contact forms, emails, scheduled triggers) to the right
workflow + payload. First tries Skills Library (Tier 0, $0), then falls back to
AI Gateway (Tier 1+).

Usage:
    from engine.decision import decide

    result = decide(task_type="contact_form", input_data={...})
    # Returns: {"workflow": "auto_email_response", "payload": {...}, "confidence": 0.9}
"""
import os
import json
import re


# Workflow registry — what each task type maps to
WORKFLOW_REGISTRY = {
    "contact_form": {
        "workflow": "auto_email_response",
        "payload_keys": ["contact_id", "name", "email", "service", "message", "trigger_date"],
        "description": "New contact from portfolio website",
    },
    "followup_3d": {
        "workflow": "auto_followup",
        "payload_keys": ["contact_id", "name", "service", "message", "days_since", "trigger_date"],
        "description": "3-day follow-up for unanswered contact",
    },
    "followup_7d": {
        "workflow": "auto_followup",
        "payload_keys": ["contact_id", "name", "service", "message", "days_since", "trigger_date"],
        "description": "7-day follow-up for unanswered contact",
    },
    "daily_routine": {
        "workflow": "daily_routine",
        "payload_keys": ["trigger", "trigger_date"],
        "description": "Daily morning routine check",
    },
    "weekly_review": {
        "workflow": "weekly_review",
        "payload_keys": ["trigger", "trigger_date"],
        "description": "Sunday weekly review",
    },
    "gmail_check": {
        "workflow": "gmail_check",
        "payload_keys": ["trigger", "trigger_date"],
        "description": "Gmail inbox check",
    },
    "auto_skill_learn": {
        "workflow": "auto_skill_learn",
        "payload_keys": ["trigger", "trigger_date"],
        "description": "Extract patterns from sent items",
    },
    "lead_capture": {
        "workflow": "lead_capture",
        "payload_keys": ["name", "email", "company", "message"],
        "description": "Manual lead capture",
    },
}


def list_task_types():
    """Return all registered task types."""
    return list(WORKFLOW_REGISTRY.keys())


def decide(task_type, input_data=None):
    """Map a task_type to a workflow + payload.

    Args:
        task_type: One of WORKFLOW_REGISTRY keys
        input_data: Dict of available fields

    Returns:
        dict with keys: workflow, payload, confidence, reasoning
    """
    if task_type not in WORKFLOW_REGISTRY:
        return {
            "error": f"Unknown task_type '{task_type}'",
            "available": list_task_types(),
        }

    spec = WORKFLOW_REGISTRY[task_type]
    input_data = input_data or {}

    # Build payload — fill missing fields with sensible defaults
    payload = {}
    for key in spec["payload_keys"]:
        if key in input_data:
            payload[key] = input_data[key]
        elif key == "trigger_date":
            from datetime import datetime
            payload[key] = datetime.utcnow().isoformat() + "Z"
        elif key == "trigger":
            payload[key] = f"decision_engine_{task_type}"
        elif key == "days_since":
            payload[key] = "3"
        else:
            payload[key] = None

    confidence = _compute_confidence(task_type, input_data, payload)

    return {
        "workflow": spec["workflow"],
        "payload": payload,
        "confidence": confidence,
        "reasoning": spec["description"],
        "task_type": task_type,
    }


def _compute_confidence(task_type, input_data, payload):
    """How confident are we in the decision? Higher = more fields filled."""
    spec = WORKFLOW_REGISTRY[task_type]
    expected_keys = spec["payload_keys"]
    filled = sum(1 for k in expected_keys if payload.get(k) is not None)
    total = len(expected_keys)
    if total == 0:
        return 1.0
    return round(filled / total, 2)


def decide_from_email(subject, body, sender):
    """Auto-decide which workflow to run based on email content.

    Used by gmail_check workflow to route incoming emails.
    Returns the decision from decide().
    """
    subject_lower = (subject or "").lower()
    body_lower = (body or "").lower()
    text = f"{subject_lower} {body_lower}"

    # Out of office → archive
    if any(phrase in text for phrase in ["out of office", "auto-reply", "vacation", "away until"]):
        return decide("gmail_check", {"decision": "archive", "sender": sender})

    # Unsubscribe / not interested → archive
    if any(phrase in text for phrase in ["unsubscribe", "remove me", "not interested", "no thanks"]):
        return decide("gmail_check", {"decision": "archive", "sender": sender})

    # Question patterns
    if "?" in body or any(w in text for w in ["how much", "what's the price", "what is the cost", "do you", "can you"]):
        return decide("gmail_check", {"decision": "needs_reply", "sender": sender, "subject": subject})

    # Default
    return decide("gmail_check", {"decision": "needs_review", "sender": sender, "subject": subject})


def decide_for_followup(contact):
    """Decide if a contact needs follow-up and what type.

    Args:
        contact: dict with keys: id, status, sent_at, created_at, days_since

    Returns:
        dict with followup decision
    """
    if contact.get("status") != "sent":
        return {"action": "skip", "reason": "Contact not in 'sent' state"}

    days = contact.get("days_since", 0)

    if days >= 7:
        return decide("followup_7d", {
            "contact_id": contact["id"],
            "name": contact.get("name"),
            "service": contact.get("service"),
            "message": contact.get("message"),
            "days_since": str(days),
        })
    elif days >= 3:
        return decide("followup_3d", {
            "contact_id": contact["id"],
            "name": contact.get("name"),
            "service": contact.get("service"),
            "message": contact.get("message"),
            "days_since": str(days),
        })

    return {"action": "skip", "reason": f"Too early ({days} days)"}
