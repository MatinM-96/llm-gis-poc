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

