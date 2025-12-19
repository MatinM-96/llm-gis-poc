# embeddings.py
import os
from openai import OpenAI


from dotenv import load_dotenv
load_dotenv()





AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_KEY"]
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = "text-embedding-3-large"  


client = OpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    base_url=f"{AZURE_OPENAI_ENDPOINT}/openai/v1/"
)

def embed_text(text: str) -> list[float]:
    text = (text or "").strip()
    if not text:
        return []

    response = client.embeddings.create(
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT, 
        input=text
    )

    return response.data[0].embedding
