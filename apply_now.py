"""
Apply to 3 n8n Community forum threads — opens URLs in Brave, you paste the replies.

These 3 are PUBLIC forum replies (not direct email). Public replies stay
visible and serve as a portfolio piece. No forms, no email deliverability
risk. The community is n8n-aware, so no context needed.

Run:
  python apply_now.py
"""

import webbrowser
import time
from pathlib import Path

WORKSPACE = Path(r"C:\Users\A\Desktop\Money")

POSTS = [
    {
        "file": "Application_N8N_Community_mkitplug.md",
        "url": "https://community.n8n.io/t/i-built-a-free-figma-plugin-that-sends-design-data-to-n8n-looking-for-agencies-to-build-real-workflows-with/297696",
        "author": "mkitplug (Michael)",
        "thread_title": "Figma plugin → n8n, looking for agencies",
    },
    {
        "file": "Application_N8N_Community_easybits.md",
        "url": "https://community.n8n.io/t/recruiter-friend-was-losing-half-her-day-to-manually-typing-linkedin-profiles-into-a-sheet-built-her-a-workflow-that-ends-the-retyping/297970",
        "author": "easybits",
        "thread_title": "Recruiter LinkedIn workflow",
    },
    {
        "file": "Application_N8N_Community_Doru_Gradinaru.md",
        "url": "https://community.n8n.io/t/built-an-importable-guard-workflow-for-costly-ai-tool-calls-looking-for-n8n-feedback/296302",
        "author": "Doru_Gradinaru",
        "thread_title": "Guard workflow for AI tool costs",
    },
]


def main():
    print("=" * 60)
    print("APPLY NOW — 3 n8n Community forum posts")
    print("=" * 60)
    print()
    print("Opening all 3 thread URLs in your default browser.")
    print("For each tab:")
    print("  1. Log in to community.n8n.io (Discourse) if not already")
    print("  2. Scroll to the bottom of the original post")
    print("  3. Click 'Reply' (NOT 'Create New Topic')")
    print("  4. Open the corresponding Application_N8N_Community_*.md file")
    print("  5. Copy the reply text (between the ``` fences)")
    print("  6. Paste into the reply box")
    print("  7. Click 'Reply to Topic'")
    print("  8. Copy the new reply URL from your browser")
    print("  9. Update Application_Pipeline.md with the post URL + date")
    print()
    input("Press ENTER when ready to open all 3 tabs...")
    print()

    for i, post in enumerate(POSTS, 1):
        print(f"[{i}/3] Opening: {post['author']} — {post['thread_title']}")
        print(f"      URL: {post['url']}")
        print(f"      Reply draft: {post['file']}")
        webbrowser.open_new_tab(post["url"])
        time.sleep(2)  # Don't hammer the browser

    print()
    print("=" * 60)
    print("All 3 tabs opened. Post in each, then come back here.")
    print("=" * 60)
    print()
    print("Tip: Open all 3 .md files in Notepad++ tabs first, so you can")
    print("     Alt+Tab between browser and editor to copy/paste quickly.")


if __name__ == "__main__":
    main()
