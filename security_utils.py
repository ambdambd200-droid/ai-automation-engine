"""
security_utils.py — Input sanitization, rate limiting, and security helpers.

Provides:
- Input sanitization (HTML, SQL, XSS, path traversal)
- API rate limiting (token bucket)
- Request validation
- Secure headers helpers
"""

import html
import re
import time
import threading
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from urllib.parse import quote, unquote

# --- Input Sanitization ---

HTML_ESCAPE_MAP = {
    '&': '&',
    '<': '<',
    '>': '>',
    '"': '"',
    "'": "'",
    '/': '&#x2F;',
}

SQL_INJECTION_PATTERNS = [
    r"(?i)(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
    r"(?i)(--|;|/\*|\*/|@@|char|nchar|varchar|nvarchar)",
    r"(?i)(\bor\b.*=.*)",
    r"(?i)(\band\b.*=.*)",
    r"(?i)(\bwaitfor\s+delay\b)",
]

XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe",
    r"<object",
    r"<embed",
    r"vbscript:",
    r"data:",
]

PATH_TRAVERSAL_PATTERNS = [
    r"\.\./",
    r"\.\.\\",
    r"%2e%2e%2f",
    r"%2e%2e%5c",
    r"\.\.%2f",
    r"\.\.%5c",
]

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
URL_PATTERN = re.compile(
    r"^https?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$", re.IGNORECASE
)


def sanitize_html(text: str) -> str:
    """Escape HTML special characters."""
    if not isinstance(text, str):
        text = str(text)
    return html.escape(text, quote=True)


def sanitize_sql(text: str) -> str:
    """Basic SQL injection pattern detection (returns sanitized)."""
    if not isinstance(text, str):
        text = str(text)
    # Just escape single quotes for basic protection
    return text.replace("'", "''")


def sanitize_filename(text: str) -> str:
    """Sanitize filename to prevent path traversal."""
    if not isinstance(text, str):
        text = str(text)
    # Remove path traversal attempts
    text = re.sub(r'[\.\.\\/]', '', text)
    # Keep only safe characters
    text = re.sub(r'[^\w\-_\.]', '', text)
    return text[:255]


def sanitize_url(text: str) -> str:
    """Validate and sanitize URL."""
    if not isinstance(text, str):
        text = str(text)
    text = text.strip()
    if not URL_PATTERN.match(text):
        raise ValueError(f"Invalid URL: {text}")
    return text


def sanitize_email(text: str) -> str:
    """Validate and sanitize email."""
    if not isinstance(text, str):
        text = str(text)
    text = text.strip().lower()
    if not EMAIL_PATTERN.match(text):
        raise ValueError(f"Invalid email: {text}")
    return text


def sanitize_input(text: str, max_length: int = 10000, allow_html: bool = False) -> str:
    """General purpose input sanitization."""
    if not isinstance(text, str):
        text = str(text)
    text = text[:max_length]
    if not allow_html:
        text = sanitize_html(text)
    return text.strip()


def detect_sql_injection(text: str) -> List[str]:
    """Detect potential SQL injection patterns. Returns list of matched patterns."""
    if not isinstance(text, str):
        return []
    matches = []
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matches.append(pattern)
    return matches


def detect_xss(text: str) -> List[str]:
    """Detect potential XSS patterns. Returns list of matched patterns."""
    if not isinstance(text, str):
        return []
    matches = []
    for pattern in XSS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matches.append(pattern)
    return matches


def detect_path_traversal(text: str) -> List[str]:
    """Detect path traversal attempts."""
    if not isinstance(text, str):
        return []
    matches = []
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matches.append(pattern)
    return matches


def validate_request(data: Dict, required_fields: List[str] = None,
                     max_string_length: int = 10000) -> Dict[str, List[str]]:
    """Validate request data. Returns dict of field -> list of errors."""
    errors = defaultdict(list)
    if not isinstance(data, dict):
        errors["_root"].append("Request body must be a JSON object")
        return dict(errors)

    if required_fields:
        for field in required_fields:
            if field not in data:
                errors[field].append("Required field missing")

    for key, value in data.items():
        if isinstance(value, str):
            if len(value) > max_string_length:
                errors[key].append(f"String too long (max {max_string_length})")
            # Check for injection patterns
            sql_matches = detect_sql_injection(value)
            if sql_matches:
                errors[key].append(f"Potential SQL injection detected")
            xss_matches = detect_xss(value)
            if xss_matches:
                errors[key].append(f"Potential XSS detected")
            path_matches = detect_path_traversal(value)
            if path_matches:
                errors[key].append(f"Path traversal detected")

    return dict(errors)


# --- Rate Limiting (Token Bucket) ---

class TokenBucket:
    """Thread-safe token bucket rate limiter."""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if allowed."""
        with self.lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def wait_for_tokens(self, tokens: int = 1, timeout: float = 30.0) -> bool:
        """Wait until tokens are available or timeout."""
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            if self.consume(tokens):
                return True
            time.sleep(0.1)
        return False

    def get_available(self) -> float:
        with self.lock:
            self._refill()
            return self.tokens


class RateLimiter:
    """Multi-key rate limiter using token buckets."""

    def __init__(self, default_capacity: int = 100, default_refill_rate: float = 10.0):
        self.buckets: Dict[str, TokenBucket] = {}
        self.default_capacity = default_capacity
        self.default_refill_rate = default_refill_rate
        self.lock = threading.Lock()

    def _get_bucket(self, key: str) -> TokenBucket:
        with self.lock:
            if key not in self.buckets:
                self.buckets[key] = TokenBucket(self.default_capacity, self.default_refill_rate)
            return self.buckets[key]

    def allow(self, key: str, tokens: int = 1) -> bool:
        """Check if request is allowed."""
        bucket = self._get_bucket(key)
        return bucket.consume(tokens)

    def wait_allowed(self, key: str, tokens: int = 1, timeout: float = 30.0) -> bool:
        """Wait until request is allowed."""
        bucket = self._get_bucket(key)
        return bucket.wait_for_tokens(tokens, timeout)

    def get_status(self, key: str) -> Dict:
        bucket = self._get_bucket(key)
        return {
            "available": bucket.get_available(),
            "capacity": bucket.capacity,
            "refill_rate": bucket.refill_rate,
        }

    def reset(self, key: str):
        with self.lock:
            if key in self.buckets:
                del self.buckets[key]


# Global rate limiter instances (per service)
_GLOBAL_LIMITERS = {
    "groq": RateLimiter(default_capacity=50, default_refill_rate=5.0),      # 5 req/sec burst
    "resend": RateLimiter(default_capacity=20, default_refill_rate=2.0),    # 2 req/sec
    "gmail": RateLimiter(default_capacity=10, default_refill_rate=1.0),     # 1 req/sec
    "mostaql": RateLimiter(default_capacity=5, default_refill_rate=0.5),    # 1/2 req/sec
    "nafezly": RateLimiter(default_capacity=5, default_refill_rate=0.5),    # 1/2 req/sec
    "n8n": RateLimiter(default_capacity=10, default_refill_rate=1.0),       # 1 req/sec
    "github": RateLimiter(default_capacity=100, default_refill_rate=10.0),  # 10 req/sec
    "default": RateLimiter(default_capacity=100, default_refill_rate=10.0),
}


def get_limiter(service: str = "default") -> RateLimiter:
    """Get rate limiter for a service."""
    return _GLOBAL_LIMITERS.get(service, _GLOBAL_LIMITERS["default"])


def rate_limit(service: str = "default", tokens: int = 1) -> Callable:
    """Decorator for rate limiting function calls."""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            limiter = get_limiter(service)
            if not limiter.allow(service, tokens):
                # Wait for availability
                if not limiter.wait_allowed(service, tokens, timeout=30):
                    raise RuntimeError(f"Rate limit exceeded for {service}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


# --- Secure Headers ---

SECURE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


def get_secure_headers() -> Dict[str, str]:
    """Get standard secure headers."""
    return SECURE_HEADERS.copy()


# --- API Key Management ---

def get_api_key(key_name: str, required: bool = True) -> Optional[str]:
    """Get API key from environment with validation."""
    key = os.environ.get(key_name, "").strip()
    if required and not key:
        raise RuntimeError(f"Required environment variable {key_name} not set")
    return key if key else None


def mask_key(key: str, visible: int = 4) -> str:
    """Mask API key for logging."""
    if not key:
        return "NOT_SET"
    if len(key) <= visible * 2:
        return "*" * len(key)
    return key[:visible] + "*" * (len(key) - visible * 2) + key[-visible:]


# --- Secure File Operations ---

SAFE_EXTENSIONS = {'.json', '.yaml', '.yml', '.txt', '.md', '.py', '.html', '.css', '.js', '.csv'}

def is_safe_file(path: Path) -> bool:
    """Check if file path is safe (no traversal, safe extension)."""
    try:
        path.resolve()
        return path.suffix.lower() in SAFE_EXTENSIONS
    except Exception:
        return False


def safe_read(path: Path, max_size: int = 10 * 1024 * 1024) -> str:
    """Safely read file with size limit."""
    if not is_safe_file(path):
        raise ValueError(f"Unsafe file path or extension: {path}")
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    size = path.stat().st_size
    if size > max_size:
        raise ValueError(f"File too large: {size} bytes (max {max_size})")
    return path.read_text(encoding="utf-8", errors="replace")


def safe_write(path: Path, content: str, max_size: int = 10 * 1024 * 1024) -> None:
    """Safely write file with size limit."""
    if not is_safe_file(path):
        raise ValueError(f"Unsafe file path or extension: {path}")
    if len(content.encode("utf-8")) > max_size:
        raise ValueError(f"Content too large (max {max_size} bytes)")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# --- Exports ---

__all__ = [
    # Sanitization
    "sanitize_html", "sanitize_sql", "sanitize_filename", "sanitize_url",
    "sanitize_email", "sanitize_input", "detect_sql_injection", "detect_xss",
    "detect_path_traversal", "validate_request", "sanitize_input",
    # Rate Limiting
    "TokenBucket", "RateLimiter", "get_limiter", "rate_limit",
    # Headers
    "get_secure_headers",
    # API Keys
    "get_api_key", "mask_key",
    # File Ops
    "is_safe_file", "safe_read", "safe_write",
]