import re
from typing import Any


# -----------------------------
# Helpers
# -----------------------------
def normalize_where_clause(where: str | None) -> str:
  
    if not where or not where.strip():
        return "TRUE"

    w = where.strip()

    w = re.sub(r"ST_Area\s*\(\s*(?!a\.)geom\s*\)", "ST_Area(a.geom)", w)

    w = re.sub(r"(?<![a-zA-Z0-9_\.])geom(?!\s*\.)", "a.geom", w)

    return w


def _get_table_ref(layer: str) -> str:
    """Hvis schema ikke er gitt: bruk public.<layer>."""
    return layer if "." in layer else f"public.{layer}"


def _limit_sql(limit: int | None) -> str:
    return f"LIMIT {int(limit)}" if limit is not None else ""


def _wkt(alias: str, out_srid: int = 4326) -> str:
    return f"ST_AsText(ST_Transform({alias}.geom, {out_srid})) AS wkt_geom"


# -----------------------------
# SQL builders
# -----------------------------
def sql_select_by_attribute(plan: dict[str, Any]) -> str:
    layer = _get_table_ref(plan["layer"])
    where = normalize_where_clause(plan.get("where_clause"))
    limit = plan.get("limit")
    return f"""
    SELECT a.*, {_wkt("a")}
    FROM {layer} a
    WHERE {where}
    {_limit_sql(limit)}
    """.strip()


def sql_select_limit_only(plan: dict[str, Any]) -> str:
    layer = _get_table_ref(plan["layer"])
    limit = plan.get("limit")
    return f"""
    SELECT a.*, {_wkt("a")}
    FROM {layer} a
    {_limit_sql(limit)}
    """.strip()


def sql_select_buffer(plan: dict[str, Any]) -> str:
    layer = _get_table_ref(plan["layer"])
    target = _get_table_ref(plan["target_layer"])
    buffer_m = plan["buffer_meters"]
    where = normalize_where_clause(plan.get("where_clause"))
    limit = plan.get("limit")

    return f"""
    SELECT a.*, {_wkt("a")}
    FROM {layer} a
    JOIN {target} b
      ON a.geom && ST_Expand(b.geom, {buffer_m})
     AND ST_DWithin(a.geom, b.geom, {buffer_m})
    WHERE {where}
    {_limit_sql(limit)}
    """.strip()


def sql_select_intersect(plan: dict[str, Any]) -> str:
    layer = _get_table_ref(plan["layer"])
    target = _get_table_ref(plan["target_layer"])
    where = normalize_where_clause(plan.get("where_clause"))
    limit = plan.get("limit")

    return f"""
    SELECT a.*, {_wkt("a")}
    FROM {layer} a
    JOIN {target} b
      ON a.geom && b.geom
     AND ST_Intersects(a.geom, b.geom)
    WHERE {where}
    {_limit_sql(limit)}
    """.strip()


def sql_select_nearest(plan: dict[str, Any]) -> str:
    layer = _get_table_ref(plan["layer"])
    target = _get_table_ref(plan["target_layer"])
    limit = plan.get("limit", 1)

    return f"""
    SELECT a.*, {_wkt("a")}
    FROM {layer} a
    JOIN {target} b ON TRUE
    ORDER BY a.geom <-> b.geom
    {_limit_sql(limit)}
    """.strip()


def sql_select_within(plan: dict[str, Any]) -> str:
    layer = _get_table_ref(plan["layer"])
    target = _get_table_ref(plan["target_layer"])
    where = normalize_where_clause(plan.get("where_clause"))
    limit = plan.get("limit")

    return f"""
    SELECT a.*, {_wkt("a")}
    FROM {layer} a
    JOIN {target} b
      ON a.geom && b.geom
     AND ST_Within(a.geom, b.geom)
    WHERE {where}
    {_limit_sql(limit)}
    """.strip()






def sql_select_overlaps(plan: dict[str, Any]) -> str:
    layer = _get_table_ref(plan["layer"])
    target = _get_table_ref(plan["target_layer"])
    where = normalize_where_clause(plan.get("where_clause"))
    limit = plan.get("limit")

    return f"""
    SELECT a.*, {_wkt("a")}
    FROM {layer} a
    JOIN {target} b
      ON a.geom && b.geom
     AND ST_Overlaps(a.geom, b.geom)
    WHERE {where}
    {_limit_sql(limit)}
    """.strip()


def sql_select_multi_target_buffer(plan: dict[str, Any]) -> str:
    layer = _get_table_ref(plan["layer"])
    targets: list[str] = plan["target_layers"]
    buffer_m = plan["buffer_meters"]
    where = normalize_where_clause(plan.get("where_clause"))
    limit = plan.get("limit")
    out_srid = plan.get("output_srid", 4326)

    exists_parts: list[str] = []
    for i, t in enumerate(targets):
        t_ref = _get_table_ref(t)
        exists_parts.append(f"""
        EXISTS (
          SELECT 1
          FROM {t_ref} b{i}
          WHERE a.geom && ST_Expand(b{i}.geom, {buffer_m})
            AND ST_DWithin(a.geom, b{i}.geom, {buffer_m})
        )
        """.strip())

    exists_sql = " AND ".join(f"({p})" for p in exists_parts)

    return f"""
    SELECT a.*, {_wkt("a", out_srid)}
    FROM {layer} a
    WHERE ({where}) AND ({exists_sql})
    {_limit_sql(limit)}
    """.strip()


# -----------------------------
# Plan enrich + dispatch
# -----------------------------
def enrich_plan(plan: dict[str, Any]) -> dict[str, Any]:
    if plan.get("limit") is None:
        plan["limit"] = 200

    op = plan["operation"]

    if op == "select_buffer":
        plan.setdefault("buffer_meters", 100)
        if not plan.get("target_layer"):
            raise ValueError("select_buffer requires target_layer")

    if op in ("select_intersect", "select_nearest", "select_within", "select_contains", "select_touches", "select_overlaps"):
        if not plan.get("target_layer"):
            raise ValueError(f"{op} requires target_layer")

    if op == "select_multi_target_buffer":
        plan.setdefault("buffer_meters", 100)
        if not plan.get("target_layers"):
            raise ValueError("select_multi_target_buffer requires target_layers (list)")

    return plan




def plan_to_sql(plan: dict) -> str:
    op = plan["operation"]

    if op == "select_limit_only":
        return sql_select_limit_only(plan)

    if op == "select_by_attribute":
        return sql_select_by_attribute(plan)

    if op == "select_buffer":
        return sql_select_buffer(plan)

    if op == "select_intersect":
        return sql_select_intersect(plan)

    if op == "select_nearest":
        return sql_select_nearest(plan)

    if op == "select_within":
        return sql_select_within(plan)


    if op == "select_overlaps":
        return sql_select_overlaps(plan)

    if op == "select_multi_target_buffer":
        return sql_select_multi_target_buffer(plan)

    raise ValueError(f"Unsupported operation: {op}")
