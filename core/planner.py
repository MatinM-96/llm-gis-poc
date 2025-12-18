from .llm import LLMClient
from .geo_utils import lookup_kommune, city_bbox_where_clause



FIELD_INFO = {
    
    "layer": (
        "The PRIMARY dataset you want results from.\n"
        "Must match one of the allowed database layers:\n"
        "- buildings\n"
        "- flomsoner\n"
        "- buildings_sample\n"
        "- arealbruk_skogbonitet_sample\n"
        "- flomsoner_sample\n"
        "- sykkelrute_senterlinje_sample\n"
        "- skiloype_senterlinje\n"
        "- annenrute_senterlinje\n"
        "- annenruteinfo_tabell\n"
        "- arealbruk_skogbonitet\n"
        "- fotrute_senterlinje\n"
        "- fotruteinfo_tabell\n"
        "- ruteinfopunkt_posisjon\n"
        "- skiloypeinfo_tabell\n"
        "- sykkelrute_senterlinje\n"
        "- sykkelruteinfo_tabell"
    ),

}

def process_user_input(user_input):
    
        
    llm = LLMClient ()

    clean_text = llm.normalize_query(user_input)

    plan = llm.plan_spatial_query(clean_text)
    if not isinstance(plan, dict):
        return "Invalid plan"

    # --- municipality → bbox filter (kode, ikke LLM) ---
    municipality = llm.extract_municipality(clean_text)
    city_filter = None

    if municipality:
        min_lon, min_lat, max_lon, max_lat = lookup_kommune(municipality)
        city_filter = city_bbox_where_clause(
            min_lon, min_lat, max_lon, max_lat
        )

    # --- combine where clauses ---
    existing = plan.get("where_clause")

    if city_filter:
        if existing and existing.strip():
            plan["where_clause"] = f"({existing}) AND ({city_filter})"
        else:
            plan["where_clause"] = city_filter

    # default limit
    if plan.get("limit") is None:
        plan["limit"] = 100

    # layer validation only
    if not plan.get("layer"):
        return (
            "⚠ Unknown or missing layer.\n\n"
            + FIELD_INFO["layer"]
            + f"\n\nYour input:\n  {user_input}"
        )

    return plan


