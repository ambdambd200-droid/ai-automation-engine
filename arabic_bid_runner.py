"""Arabic Bid Runner — unified orchestrator for Nafezly + Mostaql.

Uses nafezly_agent.py and mostaql_agent.py for browser automation,
and the engine's /api/bid/generate endpoint for AI bid generation.

Usage:
    python arabic_bid_runner.py --platform nafezly --search "n8n"
    python arabic_bid_runner.py --platform mostaql --search "telegram bot"
    python arabic_bid_runner.py --platform both --search "automation" --top 5
"""
import os
import sys
import json
import argparse
import requests
from datetime import datetime

ENGINE_URL = os.environ.get("ENGINE_URL", "https://ai-automation-engine.onrender.com")


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def engine_generate_bid(platform, project_title, project_description, budget="", suggested_price=""):
    """Call engine's AI bid generator endpoint."""
    try:
        resp = requests.post(
            f"{ENGINE_URL}/api/bid/generate",
            json={
                "platform": platform,
                "project_title": project_title,
                "project_description": project_description,
                "budget": budget,
                "suggested_price": suggested_price,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log(f"  engine bid generation failed: {e}")
        return None


def run_nafezly(search_keyword, top_n=3):
    """Run Nafezly search + classify + bid generation (no submit)."""
    log(f"=== Nafezly: search='{search_keyword}', top={top_n} ===")
    try:
        sys.path.insert(0, ".")
        from nafezly_agent import cmd_check, search_projects, classify_project, generate_bid
    except ImportError as e:
        log(f"  nafezly_agent not available: {e}")
        return []

    projects = search_projects()
    log(f"  Found {len(projects)} projects")

    bids = []
    for p in projects[:top_n]:
        classification = classify_project(p, {})
        if not classification.get("should_bid"):
            log(f"  Skipping {p.get('title', '?')[:50]} (not worth)")
            continue

        log(f"  Bidding on: {p.get('title', '?')[:60]}")
        engine_bid = engine_generate_bid(
            platform="nafezly",
            project_title=p.get("title", ""),
            project_description=p.get("description", ""),
            budget=p.get("budget", ""),
            suggested_price=str(classification.get("suggested_price", 25)),
        )

        if engine_bid:
            bids.append({
                "platform": "nafezly",
                "project": p,
                "classification": classification,
                "bid": engine_bid,
            })
            log(f"  -> bid generated ({len(engine_bid.get('bid_text', ''))} chars)")

    return bids


def run_mostaql(search_keyword, top_n=3):
    """Run Mostaql search + classify + bid generation (no submit)."""
    log(f"=== Mostaql: search='{search_keyword}', top={top_n} ===")
    try:
        sys.path.insert(0, ".")
        from mostaql_agent import search_projects, classify_project, generate_bid
    except ImportError as e:
        log(f"  mostaql_agent not available: {e}")
        return []

    projects = search_projects()
    log(f"  Found {len(projects)} projects")

    bids = []
    for p in projects[:top_n]:
        classification = classify_project(p, {})
        if not classification.get("should_bid"):
            log(f"  Skipping {p.get('title', '?')[:50]} (not worth)")
            continue

        log(f"  Bidding on: {p.get('title', '?')[:60]}")
        engine_bid = engine_generate_bid(
            platform="mostaql",
            project_title=p.get("title", ""),
            project_description=p.get("description", ""),
            budget=p.get("budget", ""),
            suggested_price=str(classification.get("suggested_price", 30)),
        )

        if engine_bid:
            bids.append({
                "platform": "mostaql",
                "project": p,
                "classification": classification,
                "bid": engine_bid,
            })
            log(f"  -> bid generated ({len(engine_bid.get('bid_text', ''))} chars)")

    return bids


def save_bids(bids, output_path):
    """Save generated bids to file for manual review."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bids, f, ensure_ascii=False, indent=2)
    log(f"Saved {len(bids)} bids to {output_path}")
    log(f"Open this file to review + manually submit each bid")


def main():
    parser = argparse.ArgumentParser(description="Arabic Bid Runner")
    parser.add_argument("--platform", choices=["nafezly", "mostaql", "both"], default="both")
    parser.add_argument("--search", default="automation", help="Search keyword")
    parser.add_argument("--top", type=int, default=3, help="Max projects to bid on")
    parser.add_argument("--output", default="Temp/arabic_bids_generated.json")
    args = parser.parse_args()

    log(f"=== Arabic Bid Runner ===")
    log(f"Platform: {args.platform} | Search: {args.search} | Top: {args.top}")

    all_bids = []
    if args.platform in ("nafezly", "both"):
        all_bids.extend(run_nafezly(args.search, args.top))
    if args.platform in ("mostaql", "both"):
        all_bids.extend(run_mostaql(args.search, args.top))

    if all_bids:
        save_bids(all_bids, args.output)
        log(f"=== Done: {len(all_bids)} bids generated ===")
    else:
        log(f"=== Done: no bids generated ===")


if __name__ == "__main__":
    main()
