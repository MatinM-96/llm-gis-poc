import streamlit as st
import pandas as pd
import geopandas as gpd

from IPython.display import display
import binascii
from shapely.wkb import loads

# ---------------------------
# Import your existing functions
# ---------------------------
from your_module import ask_gis_agent  # <-- endre til riktig filnavn
from your_module import execute_gis_plan_db


st.title("GIS–LLM Agent Demo")

query = st.text_input("Skriv inn en GIS-spørsmål:")

if st.button("Kjør spørring"):
    df = ask_gis_agent(query)   # enten DataFrame eller feilmelding

    if df is None:
        st.error("Feil i forespørselen. Sjekk input.")
    else:
        st.success("Forespørsel kjørt!")

        st.subheader("Resultat (tabell)")
        st.dataframe(df)

        # ---- KART ----
        try:
            df["geometry"] = df["geom"].apply(lambda x: loads(binascii.unhexlify(x)))
            gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=4326)

            st.subheader("Kart-visning")
            st.map(gdf)
        except Exception as e:
            st.warning("Kunne ikke vise kart: " + str(e))
