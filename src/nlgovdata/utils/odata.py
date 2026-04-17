"""Small helpers for Tweede Kamer OData queries."""

from __future__ import annotations

from collections.abc import Sequence


def _join(value: str | Sequence[str] | None, separator: str = ",") -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    items = [item for item in value if item]
    return separator.join(items) if items else None


def build_entity_url(base_url: str, entity: str, entity_id: str | None = None) -> str:
    if entity_id:
        return f"{base_url.rstrip('/')}/{entity}({entity_id})"
    return f"{base_url.rstrip('/')}/{entity}"


def build_query_params(
    *,
    filter_value: str | None = None,
    select: str | Sequence[str] | None = None,
    expand: str | Sequence[str] | None = None,
    orderby: str | None = None,
    top: int | None = None,
    skip: int | None = None,
    include_count: bool = True,
) -> dict[str, str]:
    params: dict[str, str] = {}
    if filter_value:
        params["$filter"] = filter_value
    joined_select = _join(select)
    joined_expand = _join(expand)
    if joined_select:
        params["$select"] = joined_select
    if joined_expand:
        params["$expand"] = joined_expand
    if orderby:
        params["$orderby"] = orderby
    if top is not None:
        params["$top"] = str(top)
    if skip is not None:
        params["$skip"] = str(skip)
    if include_count:
        params["$count"] = "true"
    return params
