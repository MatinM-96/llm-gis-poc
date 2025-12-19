import requests

def lookup_kommune(name: str):
    url = "https://api.kartverket.no/kommuneinfo/v1/sok"
    params = {"knavn": name}

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    avgrensningsboks = data["kommuner"][0]["avgrensningsboks"]
    coords = avgrensningsboks["coordinates"][0]

    lons = [pt[0] for pt in coords]
    lats = [pt[1] for pt in coords]

    return min(lons), min(lats), max(lons), max(lats)



def city_bbox_where_clause(min_lon, min_lat, max_lon, max_lat):
    return f"""
a.geom && ST_Transform(
    ST_MakeEnvelope(
        {min_lon}, {min_lat},
        {max_lon}, {max_lat},
        4326
    ),
    ST_SRID(a.geom)
)
""".strip()



# def city_bbox_where_clause(min_lon, min_lat, max_lon, max_lat):
#     return f"""
# ST_Transform(a.geom, 4326) && ST_MakeEnvelope(
#     {min_lon}, {min_lat},
#     {max_lon}, {max_lat},
#     4326
# )
# """.strip()
