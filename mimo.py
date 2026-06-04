import json
from groq import Groq
from config import GROQ_API_KEY,setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

def mimo(system_prompt: str, english_command: str) -> list:
    client = Groq(api_key=GROQ_API_KEY)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": english_command},
        ],
        temperature=0.1,
        max_tokens=512,
    )

    raw   = response.choices[0].message.content
    logger.info(f"[MIMO] {raw}")
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(clean)
        return parsed if isinstance(parsed, list) else [parsed]
    except json.JSONDecodeError:
        results = []
        for line in clean.splitlines():
            line = line.strip()
            if line.startswith("{"):
                results.append(json.loads(line))
        return results
