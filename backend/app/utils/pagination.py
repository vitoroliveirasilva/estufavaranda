from __future__ import annotations

from math import ceil


def build_pagination_meta(*, page: int, page_size: int, total: int) -> dict:
    total_pages = ceil(total / page_size) if page_size else 1
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
    }
