"""
healing_orchestrator.py — Self-Healing Orchestrator for freelance automation.

Wraps platform operations with automatic:
- Selector recovery (auto-discovery on SelectorExtractionError)
- Session recovery (auto-reauth on AuthenticationError)
- Retry with exponential backoff
- Telegram notifications on critical failures
"""

import os
import sys
import time
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Callable, Any, Optional, Dict, Type
from functools import wraps
from enum import Enum

from telegram_notifier import notify_error, notify

BASE_DIR = Path(__file__).parent.resolve()


class ErrorType(Enum):
    """Classification of errors for healing strategies."""
    SELECTOR_EXTRACTION = "selector_extraction"      # CSS selector failed
    AUTHENTICATION = "authentication"                 # Session expired/invalid
    NETWORK = "network"                               # Connection/timeout
    RATE_LIMIT = "rate_limit"                         # Platform rate limit
    VALIDATION = "validation"                         # Input validation failed
    UNKNOWN = "unknown"


class HealingError(Exception):
    """Error with healing metadata."""
    def __init__(self, platform: str, error_type: ErrorType, message: str, 
                 original_error: Exception = None, recoverable: bool = True):
        self.platform = platform
        self.error_type = error_type
        self.message = message
        self.original_error = original_error
        self.recoverable = recoverable
        super().__init__(f"[{platform}] {error_type.value}: {message}")


def classify_error(error: Exception, platform: str) -> ErrorType:
    """Classify an exception into a healing error type."""
    error_str = str(error).lower()
    
    if any(kw in error_str for kw in ["selector", "locator", "element not found", "no such element", 
                                       "timeout", "waiting for selector", "strict mode violation"]):
        return ErrorType.SELECTOR_EXTRACTION
    elif any(kw in error_str for kw in ["login", "session", "unauthorized", "401", "403", 
                                         "expired", "authentication", "redirect to login"]):
        return ErrorType.AUTHENTICATION
    elif any(kw in error_str for kw in ["connection", "timeout", "network", "dns", "refused", 
                                         "reset", "unreachable"]):
        return ErrorType.NETWORK
    elif any(kw in error_str for kw in ["rate limit", "429", "too many requests", "quota"]):
        return ErrorType.RATE_LIMIT
    elif any(kw in error_str for kw in ["validation", "invalid", "required", "format"]):
        return ErrorType.VALIDATION
    return ErrorType.UNKNOWN


class HealingOrchestrator:
    """
    Orchestrates self-healing for platform operations.
    
    Usage:
        orchestrator = HealingOrchestrator("mostaql")
        
        @orchestrator.healable
        def my_operation():
            # Your code that might fail
            pass
    """
    
    def __init__(self, platform: str, max_retries: int = 3, 
                 base_delay: float = 2.0, max_delay: float = 60.0):
        self.platform = platform
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._lock = threading.Lock()
        self._healing_stats = {
            "total_calls": 0,
            "successes": 0,
            "failures": 0,
            "healing_attempts": 0,
            "healing_successes": 0,
            "by_error_type": {},
        }
    
    def _record_stat(self, key: str, increment: int = 1):
        with self._lock:
            self._healing_stats[key] = self._healing_stats.get(key, 0) + increment
    
    def get_stats(self) -> Dict:
        with self._lock:
            return dict(self._healing_stats)
    
    def _calculate_delay(self, attempt: int) -> float:
        """Exponential backoff with jitter."""
        import random
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter
    
    def _attempt_selector_healing(self, error: Exception) -> bool:
        """Attempt to heal selector extraction failure via auto-discovery."""
        try:
            log(f"[{self.platform}] Attempting selector healing via auto-discovery...")
            self._record_stat("healing_attempts")
            
            from auto_selectors import discover_selectors
            result = discover_selectors(self.platform, keyword="n8n")
            
            if result and "error" not in result and result.get("card"):
                self._record_stat("healing_successes")
                log(f"[{self.platform}] Selector healing successful: {len(result['card'])} card selectors found")
                notify(f"🔧 Selector Healing OK\nPlatform: {self.platform}\nNew selectors: {len(result['card'])}")
                return True
            else:
                log(f"[{self.platform}] Selector healing failed: {result.get('error', 'No selectors found')}")
                return False
        except Exception as e:
            log(f"[{self.platform}] Selector healing exception: {e}")
            return False
    
    def _attempt_auth_healing(self, error: Exception) -> bool:
        """Attempt to heal authentication failure via re-auth."""
        try:
            log(f"[{self.platform}] Attempting auth healing via re-auth...")
            self._record_stat("healing_attempts")
            
            from auto_reauth import reauth_platform
            success = reauth_platform(self.platform, headless=True)
            
            if success:
                self._record_stat("healing_successes")
                log(f"[{self.platform}] Auth healing successful")
                notify(f"🔐 Auth Healing OK\nPlatform: {self.platform}\nSession refreshed")
                return True
            else:
                log(f"[{self.platform}] Auth healing failed")
                return False
        except Exception as e:
            log(f"[{self.platform}] Auth healing exception: {e}")
            return False
    
    def _attempt_network_healing(self, error: Exception) -> bool:
        """Attempt to heal network failure (wait and retry)."""
        log(f"[{self.platform}] Network error - waiting before retry...")
        self._record_stat("healing_attempts")
        time.sleep(10)  # Wait for network recovery
        self._record_stat("healing_successes")
        notify(f"🌐 Network Healing OK\nPlatform: {self.platform}\nRetrying after wait")
        return True
    
    def _attempt_rate_limit_healing(self, error: Exception) -> bool:
        """Attempt to heal rate limit (longer wait)."""
        log(f"[{self.platform}] Rate limit hit - waiting longer...")
        self._record_stat("healing_attempts")
        time.sleep(60)  # Wait 1 minute for rate limit reset
        self._record_stat("healing_successes")
        notify(f"⏱️ Rate Limit Healing OK\nPlatform: {self.platform}\nWaited 60s")
        return True
    
    def _heal(self, error: Exception, attempt: int) -> bool:
        """Attempt healing based on error type."""
        error_type = classify_error(error, self.platform)
        
        # Record error type stats
        with self._lock:
            et_key = f"by_error_type.{error_type.value}"
            self._healing_stats[et_key] = self._healing_stats.get(et_key, 0) + 1
        
        log(f"[{self.platform}] Error classified as: {error_type.value} (attempt {attempt + 1}/{self.max_retries})")
        
        # Notify on first healing attempt
        if attempt == 0:
            notify_error(f"🔧 Self-Healing Triggered\n"
                        f"Platform: {self.platform}\n"
                        f"Error: {error_type.value}\n"
                        f"Message: {str(error)[:200]}\n"
                        f"Attempt: {attempt + 1}/{self.max_retries}")
        
        healers = {
            ErrorType.SELECTOR_EXTRACTION: self._attempt_selector_healing,
            ErrorType.AUTHENTICATION: self._attempt_auth_healing,
            ErrorType.NETWORK: self._attempt_network_healing,
            ErrorType.RATE_LIMIT: self._attempt_rate_limit_healing,
            ErrorType.VALIDATION: lambda e: False,  # Validation errors not recoverable
            ErrorType.UNKNOWN: lambda e: False,
        }
        
        healer = healers.get(error_type)
        if healer:
            return healer(error)
        return False
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with self-healing retries."""
        self._record_stat("total_calls")
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                self._record_stat("successes")
                return result
            except Exception as e:
                last_error = e
                self._record_stat("failures")
                
                if attempt < self.max_retries:
                    # Check if error is recoverable
                    error_type = classify_error(e, self.platform)
                    if error_type in (ErrorType.VALIDATION, ErrorType.UNKNOWN):
                        log(f"[{self.platform}] Non-recoverable error: {error_type.value}")
                        break
                    
                    # Attempt healing
                    healed = self._heal(e, attempt)
                    if not healed:
                        log(f"[{self.platform}] Healing failed, retrying anyway...")
                    
                    # Wait before retry
                    delay = self._calculate_delay(attempt)
                    log(f"[{self.platform}] Waiting {delay:.1f}s before retry...")
                    time.sleep(delay)
                else:
                    log(f"[{self.platform}] Max retries exceeded")
        
        # All retries failed
        notify_error(f"❌ Self-Healing Exhausted\n"
                    f"Platform: {self.platform}\n"
                    f"Error: {classify_error(last_error, self.platform).value}\n"
                    f"Message: {str(last_error)[:300]}\n"
                    f"Retries: {self.max_retries}")
        raise HealingError(
            platform=self.platform,
            error_type=classify_error(last_error, self.platform),
            message=str(last_error),
            original_error=last_error,
            recoverable=False
        )
    
    def healable(self, func: Callable = None, *, max_retries: int = None):
        """Decorator for making functions self-healing."""
        if func is None:
            return lambda f: self.healable(f, max_retries=max_retries)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use per-call max_retries if provided
            old_max = self.max_retries
            if max_retries is not None:
                self.max_retries = max_retries
            try:
                return self.execute(func, *args, **kwargs)
            finally:
                self.max_retries = old_max
        return wrapper


# Global orchestrator instances per platform
_ORCHESTRATORS = {}


def get_orchestrator(platform: str, **kwargs) -> HealingOrchestrator:
    """Get or create orchestrator for platform."""
    if platform not in _ORCHESTRATORS:
        _ORCHESTRATORS[platform] = HealingOrchestrator(platform, **kwargs)
    return _ORCHESTRATORS[platform]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


if __name__ == "__main__":
    # Test the orchestrator
    orch = HealingOrchestrator("test")
    
    @orch.healable
    def failing_func():
        raise Exception("selector not found: .project-card")
    
    try:
        failing_func()
    except HealingError as e:
        print(f"Healing failed as expected: {e}")
    
    print("Stats:", orch.get_stats())