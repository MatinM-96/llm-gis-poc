from .llm import LLMClient
from .geo_utils import *
from embeddings.retrieve_layers import (
    retrieve_top_layers,
    format_layer_context,
    load_index,
)
from pathlib import Path










def validate_plan(plan, layer_index):
    valid_layers = {item["layer"] for item in layer_index}

    if plan["layer"] not in valid_layers:
        raise ValueError(
            f"Ugyldig lag: {plan['layer']}. "
            f"Gyldige lag er: {list(valid_layers)[:5]}..."
        )

    return plan


def process_user_input(user_input):
    llm = LLMClient()

    INDEX_PATH = (
        Path(__file__).resolve().parents[1]
        / "embeddings"
        / "layer_index.json"
    )

    # Normalize user input
    clean_text = llm.normalize_query(user_input)

    # Load layer index (embedding store)
    layer_index = load_index(INDEX_PATH)

    # Embedding-based context
    top_layers = retrieve_top_layers(clean_text, k=5)
    layer_context = format_layer_context(top_layers)

    # LLM creates plan
    plan = llm.plan_spatial_query(clean_text, layer_context)

    if not isinstance(plan, dict):
        return "Invalid plan"

    # Validate plan (CODE, not LLM)
    plan = validate_plan(plan, layer_index)

    # Municipality → bbox filter (code, not LLM)
    municipality = llm.extract_municipality(clean_text)
    city_filter = None


    if municipality:
        kommune_nr = lookup_kommuneNr(municipality)
        geo = lookup_kommuneGeo(kommune_nr)  
        if geo:
            min_lon, min_lat, max_lon, max_lat = multipolygon_to_bbox(geo)
            bbox_clause = city_bbox_where_clause(min_lon, min_lat, max_lon, max_lat)
            poly_clause = city_polygon_where_clause(geo)  
            
            city_filter = f"({poly_clause})"

    plan["where_clause"] = city_filter or plan.get("where_clause") or "TRUE"
    return plan