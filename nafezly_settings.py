"""
nafezly_settings.py — One-click helper to populate Nafezly settings page
for Salim Muhammad's identity.

Reads salim_profile.json (single source of truth) and prints / writes
each form field value ready to copy-paste into the Nafezly settings UI.

Usage:
  python nafezly_settings.py                 # print all fields to console
  python nafezly_settings.py --write         # write fill.json + fill.txt
  python nafezly_settings.py --platform nafezly   # platform-specific tag list
"""

import json
import argparse
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
PROFILE_PATH = WORKSPACE / "salim_profile.json"


def load_profile():
    with open(PROFILE_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_nafezly_fields(profile):
    """Return ordered dict of (label, value) pairs for Nafezly settings page."""
    identity = profile["identity"]
    return [
        ("الاسم الأول (First name)", identity["first_name"]),
        ("اسم العائلة (Last name)", identity["last_name"]),
        ("الجنس (Gender)", identity["gender_ar"]),
        ("تاريخ الميلاد — يوم (Birth day)", "10"),
        ("تاريخ الميلاد — شهر (Birth month)", "5"),
        ("تاريخ الميلاد — سنة (Birth year)", "2004"),
        ("Industry / المجال", identity["industry"]),
        ("نبذة مختصرة (Short bio)", profile["bio_ar_short"]),
        ("نبذة طويلة (Long bio)", profile["bio_ar_long"]),
        ("المهارات (Skills tags)", profile["skill_tags_for_platforms"]["nafezly"]),
        ("headline_ar (العنوان المهني)", profile["headline_ar"]),
        ("English headline", profile["headline_en"]),
        ("Rates — ساعة (hourly USD)", str(profile["rates"]["hourly_usd"])),
        ("Rates — مهمة صغيرة (small task USD)", str(profile["rates"]["small_task_usd"])),
        ("Rates — باقة n8n", str(profile["rates"]["n8n_workflow_package_usd"])),
        ("Rates — وكيل AI setup", str(profile["rates"]["ai_agent_setup_usd"])),
        ("Rates — اشتراك شهري", str(profile["rates"]["monthly_retainer_usd"])),
        ("البريد الإلكتروني للتواصل", identity["email_primary"]),
    ]


def print_fields(fields):
    sep = lambda label: print(f"\n{'='*60}\n  {label}\n{'='*60}")
    sep("NAFEZLY SETTINGS FIELDS — Salim Muhammad")
    print("\n>> انسخ كل قيمة والصقها في الحقل المناسب في صفحة:\n   https://nafezly.com/profile/personal-data\n")
    for i, (label, value) in enumerate(fields, 1):
        print(f"[{i}] {label}")
        print(f"    {value}")
        print()


def write_files(fields):
    out_dir = WORKSPACE / "Temp" / "nafezly"
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "salim_nafezly_fields.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            [
                {"label": l, "value": v, "copy": True}
                for l, v in fields
            ],
            f, ensure_ascii=False, indent=2,
        )

    txt_path = out_dir / "salim_nafezly_fields.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("NAFEZLY SETTINGS FIELDS — Salim Muhammad\n")
        f.write("=" * 60 + "\n\n")
        for i, (label, value) in enumerate(fields, 1):
            f.write(f"[{i}] {label}\n{value}\n\n")

    print(f"Wrote {json_path}")
    print(f"Wrote {txt_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write Temp/nafezly/salim_*.{json,txt}")
    parser.add_argument("--platform", help="filter by platform tag (nafezly, mostaql, linkedin)")
    args = parser.parse_args()

    profile = load_profile()
    fields = get_nafezly_fields(profile)

    if args.platform:
        fields = [f for f in fields if args.platform in f[0].lower() or args.platform == "all"]
        if not fields:
            print(f"No platform-specific fields for '{args.platform}'")
            return

    if args.write:
        write_files(fields)
        print_fields(fields)
    else:
        print_fields(fields)


if __name__ == "__main__":
    main()
