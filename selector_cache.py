"""
selector_cache.py — Persistent Selector Cache with auto-expiry and versioning.

Manages CSS selectors discovered by auto_selectors.py with:
- File-based persistence (JSON)
- Automatic expiry (configurable TTL)
- Version tracking
- Platform-specific namespaces
"""

import json
import os
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field

BASE_DIR = Path(__file__).parent.resolve()
CACHE_DIR = BASE_DIR / "selectors"
CACHE_DIR.mkdir(exist_ok=True)


@dataclass
class SelectorEntry:
    """Single selector entry with metadata."""
    selector: str
    element_type: str  # card, title, link, budget, etc.
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[str] = None
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_validated: Optional[str] = None
    source: str = "auto_discovery"  # auto_discovery, manual, fallback


@dataclass
class PlatformSelectors:
    """All selectors for a platform."""
    platform: str
    version: int = 1
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    card: List[SelectorEntry] = field(default_factory=list)
    title: List[SelectorEntry] = field(default_factory=list)
    link: List[SelectorEntry] = field(default_factory=list)
    budget: List[SelectorEntry] = field(default_factory=list)
    description: List[SelectorEntry] = field(default_factory=list)
    client_name: List[SelectorEntry] = field(default_factory=list)
    client_rating: List[SelectorEntry] = field(default_factory=list)
    meta: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "version": self.version,
            "updated_at": self.updated_at,
            "card": [asdict(s) for s in self.card],
            "title": [asdict(s) for s in self.title],
            "link": [asdict(s) for s in self.link],
            "budget": [asdict(s) for s in self.budget],
            "description": [asdict(s) for s in self.description],
            "client_name": [asdict(s) for s in self.client_name],
            "client_rating": [asdict(s) for s in self.client_rating],
            "meta": self.meta,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PlatformSelectors":
        obj = cls(platform=data.get("platform", ""))
        obj.version = data.get("version", 1)
        obj.updated_at = data.get("updated_at", datetime.now().isoformat())
        obj.meta = data.get("meta", {})
        
        for field_name in ["card", "title", "link", "budget", "description", 
                          "client_name", "client_rating"]:
            entries = []
            for entry_data in data.get(field_name, []):
                if isinstance(entry_data, dict):
                    entries.append(SelectorEntry(**entry_data))
                elif isinstance(entry_data, str):
                    # Legacy format: just a string
                    entries.append(SelectorEntry(selector=entry_data, element_type=field_name))
            setattr(obj, field_name, entries)
        return obj


class SelectorCache:
    """
    Thread-safe persistent selector cache with auto-expiry.
    """
    
    def __init__(self, cache_dir: Path = None, default_ttl_days: int = 30):
        self.cache_dir = cache_dir or (Path(__file__).parent / "selectors")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = timedelta(days=default_ttl_days)
        self._lock = threading.RLock()
        self._cache: Dict[str, PlatformSelectors] = {}
        self._load_all()
    
    def _get_cache_file(self, platform: str) -> Path:
        return self.cache_dir / f"{platform}.json"
    
    def _load_all(self):
        """Load all cached selectors on init."""
        for cache_file in self.cache_dir.glob("*.json"):
            if cache_file.name.endswith(".meta.json"):
                continue
            platform = cache_file.stem
            try:
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                self._cache[platform] = PlatformSelectors.from_dict(data)
            except Exception as e:
                print(f"[SelectorCache] Failed to load {cache_file}: {e}")
    
    def _save(self, platform: str):
        """Save platform selectors to disk."""
        if platform not in self._cache:
            return
        cache_file = self._get_cache_file(platform)
        data = self._cache[platform].to_dict()
        cache_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    
    def get(self, platform: str) -> Optional[PlatformSelectors]:
        """Get platform selectors (thread-safe)."""
        with self._lock:
            return self._cache.get(platform)
    
    def get_selectors(self, platform: str, element_type: str = "card", 
                      min_success: int = 0, max_age_days: int = 30) -> List[str]:
        """
        Get working selectors for platform and element type.
        Filters by success rate and age.
        """
        with self._lock:
            platform_data = self._cache.get(platform)
            if not platform_data:
                return []
            
            entries = getattr(platform_data, element_type, [])
            cutoff = datetime.now() - timedelta(days=max_age_days)
            
            valid_selectors = []
            for entry in entries:
                # Check age
                try:
                    discovered = datetime.fromisoformat(entry.discovered_at)
                    if discovered < cutoff:
                        continue
                except Exception:
                    pass
                
                # Check success rate
                total = entry.success_count + entry.failure_count
                if total > 0:
                    success_rate = entry.success_count / total
                    if success_rate < 0.3:  # Less than 30% success
                        continue
                
                if total >= min_success or entry.success_count > 0:
                    valid_selectors.append(entry.selector)
            
            return valid_selectors
    
    def record_success(self, platform: str, element_type: str, selector: str):
        """Record a successful use of a selector."""
        with self._lock:
            if platform not in self._cache:
                self._cache[platform] = PlatformSelectors(platform=platform)
            
            entries = getattr(self._cache[platform], element_type, [])
            for entry in entries:
                if entry.selector == selector:
                    entry.success_count += 1
                    entry.last_used = datetime.now().isoformat()
                    self._save(platform)
                    return
            
            # New selector
            new_entry = SelectorEntry(
                selector=selector,
                element_type=element_type,
                success_count=1,
                last_used=datetime.now().isoformat(),
            )
            entries.append(new_entry)
            self._save(platform)
    
    def record_failure(self, platform: str, element_type: str, selector: str):
        """Record a failed use of a selector."""
        with self._lock:
            if platform not in self._cache:
                self._cache[platform] = PlatformSelectors(platform=platform)
            
            entries = getattr(self._cache[platform], element_type, [])
            for entry in entries:
                if entry.selector == selector:
                    entry.failure_count += 1
                    entry.last_used = datetime.now().isoformat()
                    self._save(platform)
                    return
            
            # New selector with failure
            new_entry = SelectorEntry(
                selector=selector,
                element_type=element_type,
                failure_count=1,
            )
            entries.append(new_entry)
            self._save(platform)
    
    def add_selectors(self, platform: str, element_type: str, 
                      selectors: List[str], source: str = "auto_discovery"):
        """Add new selectors to cache."""
        with self._lock:
            if platform not in self._cache:
                self._cache[platform] = PlatformSelectors(platform=platform)
            
            platform_data = self._cache[platform]
            entries = getattr(platform_data, element_type, [])
            
            existing = {e.selector for e in entries}
            added = 0
            for selector in selectors:
                if selector not in existing:
                    new_entry = SelectorEntry(
                        selector=selector,
                        element_type=element_type,
                        source=source,
                    )
                    entries.append(new_entry)
                    existing.add(selector)
                    added += 1
            
            if added > 0:
                platform_data.version += 1
                platform_data.updated_at = datetime.now().isoformat()
                self._save(platform)
                print(f"[SelectorCache] Added {added} new {element_type} selectors for {platform}")
    
    def remove_selector(self, platform: str, element_type: str, selector: str):
        """Remove a selector from cache."""
        with self._lock:
            if platform not in self._cache:
                return
            entries = getattr(self._cache[platform], element_type, [])
            entries[:] = [e for e in entries if e.selector != selector]
            self._save(platform)
    
    def get_stats(self, platform: str) -> Dict:
        """Get cache statistics for platform."""
        with self._lock:
            data = self._cache.get(platform)
            if not data:
                return {"platform": platform, "exists": False}
            
            stats = {"platform": platform, "version": data.version, 
                     "updated_at": data.updated_at, "elements": {}}
            
            for field_name in ["card", "title", "link", "budget", "description",
                              "client_name", "client_rating"]:
                entries = getattr(data, field_name, [])
                stats["elements"][field_name] = {
                    "total": len(entries),
                    "successful": sum(1 for e in entries if e.success_count > e.failure_count),
                    "failed": sum(1 for e in entries if e.failure_count > e.success_count),
                    "never_tested": sum(1 for e in entries if e.success_count == 0 and e.failure_count == 0),
                }
            return stats
    
    def cleanup_expired(self, max_age_days: int = 30):
        """Remove expired entries."""
        with self._lock:
            cutoff = datetime.now() - timedelta(days=max_age_days)
            for platform, data in self._cache.items():
                for field_name in ["card", "title", "link", "budget", "description",
                                  "client_name", "client_rating"]:
                    entries = getattr(data, field_name, [])
                    entries[:] = [
                        e for e in entries
                        if datetime.fromisoformat(e.discovered_at) > cutoff
                    ]
                self._save(platform)
    
    def export_for_platform(self, platform: str) -> Dict:
        """Export selectors in format compatible with post_arabic_bids.py."""
        with self._lock:
            data = self._cache.get(platform)
            if not data:
                return {}
            
            result = {}
            for field_name in ["card", "title", "link", "budget", "description",
                              "client_name", "client_rating"]:
                entries = getattr(data, field_name, [])
                result[field_name] = [e.selector for e in entries 
                                     if e.success_count >= e.failure_count]
            
            return result


# Global cache instance
_GLOBAL_CACHE = None


def get_selector_cache() -> SelectorCache:
    """Get global selector cache instance."""
    global _GLOBAL_CACHE
    if _GLOBAL_CACHE is None:
        _GLOBAL_CACHE = SelectorCache()
    return _GLOBAL_CACHE


# Backward compatibility functions
def load_cached_selectors(platform: str) -> dict:
    """Load cached selectors (backward compatible with auto_selectors.py)."""
    cache = get_selector_cache()
    platform_data = cache.get(platform)
    if not platform_data:
        return {}
    
    # Convert to old format
    result = {"platform": platform, "card": [], "title": [], "link": [], "budget": []}
    for field_name in ["card", "title", "link", "budget"]:
        entries = getattr(cache.get(platform), field_name, [])
        result[field_name] = [e.selector for e in entries]
    
    return {"selectors": result}


def save_selectors_to_cache(platform: str, selectors: dict, source: str = "auto_discovery"):
    """Save selectors to cache (backward compatible)."""
    cache = get_selector_cache()
    for field_name in ["card", "title", "link", "budget", "title", "link", "budget"]:
        if field_name in selectors:
            cache.add_selectors(platform, field_name, selectors[field_name], source=source)


if __name__ == "__main__":
    # Quick test
    cache = SelectorCache()
    cache.add_selectors("mostaql", "card", ["article.project-card", ".project-item"], "test")
    cache.add_selectors("mostaql", "title", ["h3.title", "h2 a"], "test")
    
    print("Card selectors:", cache.get_selectors("mostaql", "card"))
    print("Stats:", cache.get_stats("mostaql"))