from __future__ import annotations

from math import ceil


def build_pagination_meta(*, page: int, page_size: int, total: int) -> dict:
    normalized_page = max(int(page), 1)
    normalized_page_size = max(int(page_size), 0)
    normalized_total = max(int(total), 0)

    total_pages = (
        ceil(normalized_total / normalized_page_size) if normalized_page_size > 0 else 1
    )

    return {
        "page": normalized_page,
        "page_size": normalized_page_size,
        "total": normalized_total,
        "total_pages": total_pages,
    }
