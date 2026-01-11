
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

def _get_table_ref(layer: str) -> str:
    """Get proper table reference, handling cases where schema is already included."""
    if '.' in layer:     
        return layer
    else:
        return f"public.{layer}"

def sql_select_by_attribute(plan):
    layer = _get_table_ref(plan["layer"]) 
    where = normalize_where_clause(plan.get("where_clause"))
    limit = plan["limit"]
    return f"""
    SELECT
        a.*,
        ST_AsText(ST_Transform(a.geom, 4326)) AS wkt_geom
    FROM {layer} a
    WHERE {where}
    {f"LIMIT {limit}" if limit is not None else ""}
    """.strip()

def sql_select_buffer(plan):
    layer = _get_table_ref(plan["layer"]) 
    target = _get_table_ref(plan["target_layer"])  
    buffer_m = plan["buffer_meters"]
    where = normalize_where_clause(plan.get("where_clause"))
    limit = plan["limit"]
    if not target or buffer_m is None:
        raise ValueError("select_buffer requires target_layer and buffer_meters")
    return f"""
    SELECT
        a.*,
        ST_AsText(ST_Transform(a.geom, 4326)) AS wkt_geom
    FROM {layer} a
    JOIN {target} b
      ON ST_DWithin(a.geom, b.geom, {buffer_m})
    WHERE {where}
    {f"LIMIT {limit}" if limit is not None else ""}
    """.strip()

def sql_select_intersect(plan):
    layer = _get_table_ref(plan["layer"])  
    target = _get_table_ref(plan["target_layer"]) 
    where = normalize_where_clause(plan.get("where_clause"))
    limit = plan["limit"]
    if not target:
        raise ValueError("select_intersect requires target_layer")
    return f"""
    SELECT
        a.*,
        ST_AsText(ST_Transform(a.geom, 4326)) AS wkt_geom
    FROM {layer} a
    JOIN {target} b
      ON ST_Intersects(a.geom, b.geom)
    WHERE {where}
    {f"LIMIT {limit}" if limit is not None else ""}
    """.strip()

def sql_select_nearest(plan):
    layer = _get_table_ref(plan["layer"]) 
    target = _get_table_ref(plan["target_layer"]) 
    limit = plan["limit"]
    if not target:
        raise ValueError("select_nearest requires target_layer")
    return f"""
    SELECT
        a.*,
        ST_AsText(ST_Transform(a.geom, 4326)) AS wkt_geom
    FROM {layer} a
    ORDER BY (
        SELECT MIN(ST_Distance(a.geom, b.geom))
        FROM {target} b
    )
    {f"LIMIT {limit}" if limit is not None else ""}
    """.strip()


def enrich_plan(plan: dict) -> dict:
    if plan["operation"] == "select_buffer":
        plan.setdefault("buffer_meters", 100)

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