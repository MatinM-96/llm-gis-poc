
import re

def normalize_where_clause(where: str) -> str:
    if not where or not where.strip():
        return "TRUE"

    w = where.strip()

    w = re.sub(
        r"ST_Area\s*\(\s*(?!a\.)(geom)\s*\)",
        "ST_Area(a.geom)",
        w
    )

    w = re.sub(
        r"(?<![a-zA-Z0-9_\.])geom(?!\s*\.)",
        "a.geom",
        w
    )

    return w


def sql_select_limit_only(plan):
    layer = plan["layer"]
    limit = plan["limit"]

    return f"""
    SELECT
        a.*,
        ST_AsText(ST_Transform(a.geom, 4326)) AS wkt_geom
    FROM public.{layer} a
    LIMIT {limit};
    """.strip()


def sql_select_by_attribute(plan):
    layer = plan["layer"]
    where = normalize_where_clause(plan.get("where_clause"))
    limit = plan["limit"]

    return f"""
    SELECT
        a.*,
        ST_AsText(ST_Transform(a.geom, 4326)) AS wkt_geom
    FROM public.{layer} a
    WHERE {where}
    LIMIT {limit};
    """.strip()


def sql_select_buffer(plan):
    layer = plan["layer"]
    target = plan["target_layer"]
    buffer_m = plan["buffer_meters"]
    where = normalize_where_clause(plan.get("where_clause"))
    limit = plan["limit"]

    if not target or buffer_m is None:
        raise ValueError("select_buffer requires target_layer and buffer_meters")

    return f"""
    SELECT
        a.*,
        ST_AsText(ST_Transform(a.geom, 4326)) AS wkt_geom
    FROM public.{layer} a
    JOIN public.{target} b
      ON ST_DWithin(a.geom, b.geom, {buffer_m})
    WHERE {where}
    LIMIT {limit};
    """.strip()



def sql_select_intersect(plan):
    layer = plan["layer"]
    target = plan["target_layer"]
    where = normalize_where_clause(plan.get("where_clause"))
    limit = plan["limit"]

    if not target:
        raise ValueError("select_intersect requires target_layer")

    return f"""
    SELECT
        a.*,
        ST_AsText(ST_Transform(a.geom, 4326)) AS wkt_geom
    FROM public.{layer} a
    JOIN public.{target} b
      ON ST_Intersects(a.geom, b.geom)
    WHERE {where}
    LIMIT {limit};
    """.strip()
def sql_select_nearest(plan):
    layer = plan["layer"]
    target = plan["target_layer"]
    limit = plan["limit"]

    if not target:
        raise ValueError("select_nearest requires target_layer")

    return f"""
    SELECT
        a.*,
        ST_AsText(ST_Transform(a.geom, 4326)) AS wkt_geom
    FROM public.{layer} a
    ORDER BY (
        SELECT MIN(ST_Distance(a.geom, b.geom))
        FROM public.{target} b
    )
    LIMIT {limit};
    """.strip()



def enrich_plan(plan: dict) -> dict:
    if plan["operation"] == "select_buffer":
        plan.setdefault("buffer_meters", 100)

        # enkel mapping fra intensjon → lag
        plan.setdefault("target_layer", "rivers")

    if plan.get("limit") is None:
        plan["limit"] = 100

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

    raise ValueError(f"Unsupported operation: {op}")
