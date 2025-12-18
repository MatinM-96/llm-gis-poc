import os
from openai import OpenAI
from dotenv import load_dotenv
from openai import OpenAI
import json
from pathlib import Path

class LLMClient:
    def __init__(self):

        load_dotenv()

        self.AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
        self.AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.AZURE_OPENAI_DEPLOYMENT = "gpt-4o-mini"

        self.client = OpenAI(
            api_key=self.AZURE_OPENAI_KEY,
            base_url=f"{self.AZURE_OPENAI_ENDPOINT}/openai/v1/",
        )

        
        BASE_DIR = Path(__file__).parent
        PROMPT_PATH = BASE_DIR / "system_prompt.txt"
        
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            self.SYSTEM_PROMPT = f.read()
        

    def normalize_query(self, text: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You understand poorly written Norwegian and English. "
                        "Correct spelling mistakes, interpret the intended meaning, "
                        "and rewrite the sentence clearly without adding new information."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0,
        )
        return resp.choices[0].message.content.strip()

    def plan_spatial_query(self, nl_query: str) -> dict:
        resp = self.client.chat.completions.create(
            model=self.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": nl_query},
            ],
            temperature=0.0,
            max_tokens=300,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()
        return json.loads(raw)

    def extract_municipality(self, text: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract Norwegian municipality names from user input. "
                        "Return ONLY the municipality name. "
                        "If no municipality is mentioned, return an empty string. "
                        "Do not guess."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.0,
        )
        return resp.choices[0].message.content.strip()
