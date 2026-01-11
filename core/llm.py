from pathlib import Path
import json
from openai import OpenAI
from config import (
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
)

class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=AZURE_OPENAI_KEY,
            base_url=f"{AZURE_OPENAI_ENDPOINT}/openai/v1/",
        )

        self.model = AZURE_OPENAI_DEPLOYMENT

        base_dir = Path(__file__).parent
        prompt_path = base_dir / "system_prompt.txt"

        with open(prompt_path, "r", encoding="utf-8") as f:
            self.SYSTEM_PROMPT = f.read()

    def normalize_query(self, text: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
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

    def plan_spatial_query(self, nl_query: str, layer_context: str | None = None) -> dict:
        user_content = (
            f"{layer_context}\n\nUSER REQUEST:\n{nl_query}"
            if layer_context
            else nl_query
        )

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
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
            model=self.model,
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
