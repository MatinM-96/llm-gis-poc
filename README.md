# LLM–GIS Agent Proof of Concept (PoC)

This project demonstrates how to integrate a Large Language Model (LLM) with a PostGIS spatial database to answer geographic questions using natural language.  
The system uses Azure OpenAI (for example a `gpt-4o-mini` deployment) to translate user queries into SQL, run those queries on PostGIS, and return the results as an interactive table.

Example query:
> “Find 100 residential houses within 200 meters of a river in Kristiansand.”

The goal is to show an end-to-end pipeline from:
**Natural language → LLM plan → SQL → PostGIS → Tabular result.**

---

## 1. Installation

### 1.1 Clone the project

```bash
git clone https://github.com/MatinM-96/NordKart-MasterOppgave.git
cd NordKart-MasterOppgave
```

### 1.2 Create and activate a virtual environment (optional, but recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows (PowerShell):

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 1.3 Install requirements

All dependencies are listed in `requirements.txt`. Install them with:

```bash
pip install -r requirements.txt
```

Typical contents of `requirements.txt` include:

```text
langchain-openai
langchain_core
langgraph
GeoAlchemy2
geopandas
folium
matplotlib
mapclassify
python-dotenv
openai
psycopg2-binary
pandas
```

---

## 2. Setup: Azure OpenAI and database credentials (.env)

All secrets (keys, endpoints, DB connection string) are stored in a `.env` file that is not committed to Git.

### 2.1 Create `.env` file

In the project root (same folder as `requirements.txt`), create a file named `.env`:

```bash
touch .env
```

Open it in your editor and add:

```env
AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE-NAME.openai.azure.com
AZURE_OPENAI_KEY=YOUR_AZURE_OPENAI_KEY
PGCONN_STRING=postgresql://USERNAME:PASSWORD@HOST:5432/DATABASE
```

Notes:

- Do not put spaces around `=`.
- Replace placeholders with your real values.
- Do not quote the values, just plain text.

### 2.2 Ensure `.env` is ignored by Git

In your `.gitignore` file, make sure you have:

```text
.env
```

This prevents your keys and passwords from being pushed to GitHub.

### 2.3 Load and test the environment variables

In a Python shell or Jupyter notebook:

```python
from dotenv import load_dotenv
import os

load_dotenv()
print("AZURE_OPENAI_ENDPOINT =", os.getenv("AZURE_OPENAI_ENDPOINT"))
print("AZURE_OPENAI_KEY is set:", os.getenv("AZURE_OPENAI_KEY") is not None)
print("PGCONN_STRING is set:", os.getenv("PGCONN_STRING") is not None)
```

---

## 3. Setup: Test OpenAI and database connections

### 3.1 Test Azure OpenAI connection

```python
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = "gpt-4o-mini"

client = OpenAI(
    api_key=AZURE_OPENAI_KEY,
    base_url=f"{AZURE_OPENAI_ENDPOINT}/openai/v1/",
)

resp = client.chat.completions.create(
    model=AZURE_OPENAI_DEPLOYMENT,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Introduce yourself in one short sentence."},
    ],
)

print(resp.choices[0].message.content)
```

If this prints a short sentence, the LLM connection is working.

### 3.2 Test database connection

```python
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()
conn_str = os.getenv("PGCONN_STRING")
print("Using connection string:", conn_str)

with psycopg2.connect(conn_str) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT version();")
        print(cur.fetchone())
```

---

## 4. How the PoC works

The PoC consists of several stages:

1. LLM planner (`plan_spatial_query`): Converts the natural language query into a JSON plan.
2. Plan to SQL (`plan_to_sql`): Converts the JSON plan into a valid PostGIS SQL query.
3. SQL execution (`run_postgis_query` / `execute_gis_plan_db`): Runs the query on PostGIS and returns a DataFrame.
4. High-level helper (`ask_gis_agent`): Combines all steps into one call.

---

## 5. Database assumptions

The PoC assumes your PostGIS database has at least:

- A flood zone / river layer: `public.flomsoner(geom geometry, ...)`
- A buildings layer: `public.buildings(geom geometry, type text, ...)`

If your schema is different, adjust `plan_to_sql()` accordingly.

---

## 6. Using the script

### One-off query

```python
df = ask_gis_agent("Find 100 residential houses within 200 meters of a river in Kristiansand.")
df  # shows a scrollable DataFrame
```

### Interactive chat mode

```python
from IPython.display import display

def chat_loop():
    print("GIS agent chat – type 'quit' to stop.\n")
    while True:
        user_q = input("You: ")
        if user_q.strip().lower() in ("quit", "exit", "q"):
            print("Bye")
            break

        try:
            df = ask_gis_agent(user_q)
            if len(df) == 0:
                print("No results found.\n")
            else:
                display(df)
        except Exception as e:
            print("Error:", e, "\n")

chat_loop()
```


