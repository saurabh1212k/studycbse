"""
StudyOS - Chapter Deduplicator
Collapses duplicate chapters (same subject + same name) into a single row.

Why duplicates exist: earlier seeding scripts ran while Row-Level Security
hid existing rows from their "does it already exist?" checks, so every run
inserted a fresh copy.

For each duplicate group the most valuable row is kept, in this priority:
  1. status = 'completed'   (never lose progress)
  2. status = 'in_progress'
  3. has AI notes (notes_url)
  4. has a chapter number
Ties keep the oldest row. Everything else in the group is deleted.

Usage:
    .venv/Scripts/python.exe scripts/dedupe_chapters.py
"""
import sys
import os

# Windows consoles default to cp1252; our output uses emoji
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.db import get_db


def rank(chap: dict):
    """Higher = more valuable; the highest-ranked row of a group survives."""
    return (
        1 if chap.get("status") == "completed" else 0,
        1 if chap.get("status") == "in_progress" else 0,
        1 if chap.get("notes_url") else 0,
        1 if chap.get("chapter_no") else 0,
    )


def dedupe() -> int:
    db = get_db()

    try:
        res = db.table("chapters").select("id, subject_id, name, status, notes_url, chapter_no").execute()
    except Exception as e:
        print(f"❌ Could not read chapters: {e}")
        print("   If this is a Row-Level Security error, run disable_rls.sql in the Supabase SQL Editor first.")
        return 1

    chapters = res.data or []
    print(f"📖 Fetched {len(chapters)} chapters. Grouping by (subject, name)...")

    groups: dict = {}
    for c in chapters:
        groups.setdefault((c["subject_id"], c["name"]), []).append(c)

    dupes = {k: v for k, v in groups.items() if len(v) > 1}
    if not dupes:
        print("✅ No duplicate chapters found — database is already clean!")
        return 0

    to_delete: list = []
    print(f"\n🔍 Found {len(dupes)} duplicated chapter names:\n")
    for (subject_id, name), rows in dupes.items():
        # Stable sort: highest rank first; ties keep the earliest inserted row
        rows_sorted = sorted(rows, key=rank, reverse=True)
        keep, rest = rows_sorted[0], rows_sorted[1:]
        statuses = ", ".join(sorted({r.get("status", "?") for r in rows}))
        print(f"  • {name}  [{statuses}]  -> keeping '{keep['status']}', removing {len(rest)}")
        to_delete.extend(r["id"] for r in rest)

    # Delete in batches of 50 to keep URLs small
    deleted = 0
    for i in range(0, len(to_delete), 50):
        batch = to_delete[i:i + 50]
        db.table("chapters").delete().in_("id", batch).execute()
        deleted += len(batch)

    print(f"\n🧹 Removed {deleted} duplicate rows. {len(groups)}/{len(chapters)} chapters remain.")
    print("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(dedupe())
