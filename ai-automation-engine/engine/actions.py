import requests
import json
import os


class ActionError(Exception):
    pass


def execute_action(action_def, context):
    action_type = action_def.get("type")
    params = action_def.get("params", {})

    handler = _get_handler(action_type)
    if not handler:
        raise ActionError(f"Unknown action type: {action_type}")

    return handler(params, context)


def _get_handler(action_type):
    registry = {
        "http_request": _http_request,
        "ai_prompt": _ai_prompt,
        "log": _log,
        "transform": _transform,
        "condition": _condition,
    }
    return registry.get(action_type)


def _http_request(params, context):
    method = params.get("method", "GET").upper()
    url = _render_template(params.get("url", ""), context)
    headers = params.get("headers", {})
    headers = {k: _render_template(v, context) for k, v in headers.items()}
    body = params.get("body")
    if body:
        body = _render_template(json.dumps(body), context)
        body = json.loads(body)

    resp = requests.request(method, url, headers=headers, json=body, timeout=30)
    resp.raise_for_status()

    result = resp.json() if resp.text else {}
    context["last_response"] = result
    context["last_status"] = resp.status_code
    return result


_PROVIDER_ENDPOINTS = {
    "openai":    "https://api.openai.com/v1/chat/completions",
    "groq":      "https://api.groq.com/openai/v1/chat/completions",
    "openrouter":"https://openrouter.ai/api/v1/chat/completions",
}

_PROVIDER_KEY_ENV = {
    "openai":    "OPENAI_API_KEY",
    "groq":      "GROQ_API_KEY",
    "openrouter":"OPENROUTER_API_KEY",
}

_PROVIDER_DEFAULT_MODEL = {
    "openai":    "gpt-4o-mini",
    "groq":      "llama-3.3-70b-versatile",
    "openrouter":"meta-llama/llama-3.3-70b-instruct:free",
}


def _ai_prompt(params, context):
    provider = params.get("provider", "openai").lower()
    if provider not in _PROVIDER_ENDPOINTS:
        raise ActionError(f"Unknown provider '{provider}'. Supported: {list(_PROVIDER_ENDPOINTS.keys())}")

    env_var = _PROVIDER_KEY_ENV[provider]
    api_key = params.get("api_key") or os.environ.get(env_var)
    if not api_key:
        raise ActionError(f"{env_var} not found. Set the environment variable.")

    model = params.get("model", _PROVIDER_DEFAULT_MODEL[provider])
    system_prompt = params.get("system_prompt", "You are a helpful assistant.")
    user_prompt = _render_template(params.get("user_prompt", ""), context)

    resp = requests.post(
        _PROVIDER_ENDPOINTS[provider],
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": params.get("temperature", 0.3),
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]

    try:
        parsed = json.loads(content)
        context["last_ai_response"] = parsed
        return parsed
    except json.JSONDecodeError:
        context["last_ai_response"] = content
        return {"raw": content}


def _log(params, context):
    message = _render_template(params.get("message", ""), context)
    level = params.get("level", "info")
    return {"logged": message, "level": level}


def _transform(params, context):
    template = params.get("template", "")
    result = _render_template(template, context)
    context["last_transform"] = result
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"value": result}


def _condition(params, context):
    value = _render_template(params.get("value", ""), context)
    equals = params.get("equals")
    contains = params.get("contains")

    if equals and value == _render_template(equals, context):
        return {"matched": True, "value": value}
    if contains and contains in value:
        return {"matched": True, "value": value}
    return {"matched": False, "value": value}


def _render_template(template, context):
    if not template or "${" not in template:
        return template

    result = template
    for key, val in _flatten_context(context).items():
        placeholder = "${" + key + "}"
        if placeholder in result:
            result = result.replace(placeholder, str(val) if val is not None else "")
    return result


def _flatten_context(context, prefix=""):
    items = {}
    for key, val in context.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(val, dict):
            items.update(_flatten_context(val, full_key))
        elif isinstance(val, list):
            items[full_key] = json.dumps(val)
        else:
            items[full_key] = val
    return items
