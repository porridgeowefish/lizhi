from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.application.classification import classify_categories, effective_primary_category, normalize_category_list
from app.core.config import Settings
from app.db.models import Post, PostCategory
from app.db.session import build_session_factory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synchronize post primary categories and category tags.")
    parser.add_argument(
        "--reclassify",
        action="store_true",
        help="Recompute every post category with the current rule engine before syncing tags.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env()
    _, session_factory = build_session_factory(settings)
    db = session_factory()
    checked = 0
    updated = 0
    try:
        posts = db.query(Post).all()
        for post in posts:
            checked += 1
            stored_categories = [category.category_code for category in post.categories]
            if args.reclassify:
                primary_category = classify_categories(post.title, post.summary, post.content_text_snapshot)[0]
            else:
                projection_category = post.projection.primary_category if post.projection else ""
                primary_category = effective_primary_category(projection_category, stored_categories)
            desired_categories = normalize_category_list([primary_category])

            changed = False
            if post.projection and post.projection.primary_category != primary_category:
                post.projection.primary_category = primary_category
                changed = True

            if stored_categories != desired_categories:
                db.query(PostCategory).filter(PostCategory.post_id == post.id).delete()
                db.flush()
                for category_code in desired_categories:
                    db.add(
                        PostCategory(
                            post_id=post.id,
                            category_code=category_code,
                            category_source="sync",
                        )
                    )
                changed = True

            if changed:
                updated += 1

        db.commit()
    finally:
        db.close()

    print(f"checked={checked} updated={updated}")


if __name__ == "__main__":
    main()
