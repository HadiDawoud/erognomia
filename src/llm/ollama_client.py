import json
import logging
from functools import lru_cache
from typing import Iterator, Optional

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.timeout = httpx.Timeout(900.0, connect=30.0)

    def check_model_available(self) -> bool:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return any(
                        m["name"] == self.model or m["name"].startswith(f"{self.model}:")
                        for m in models
                    )
        except Exception as e:
            logger.error("Error checking Ollama model: %s", e)
        return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.3) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                return response.json().get("response", "")
        except Exception as e:
            logger.error("Error generating with Ollama: %s", e)
            return f"Error: {str(e)}"

    def stream_generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.3) -> Iterator[str]:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line:
                            continue
                        chunk = json.loads(line)
                        if "response" in chunk:
                            yield chunk["response"]
                        if chunk.get("done"):
                            break
        except Exception as e:
            logger.error("Error streaming from Ollama: %s", e)
            yield f"Error: {str(e)}"


@lru_cache(maxsize=1)
def get_ollama_client() -> OllamaClient:
    return OllamaClient()
