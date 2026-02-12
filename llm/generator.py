"""
LLM generator — single Ollama call with timeout & error handling.
"""

import logging
import requests
from config import OLLAMA_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS, LLM_TIMEOUT_SEC

logger = logging.getLogger(__name__)


def call_llm(prompt: str) -> str:
    """Send a prompt to the Ollama API and return the response text."""
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": LLM_TEMPERATURE,
                    "num_predict": LLM_MAX_TOKENS,
                },
            },
            timeout=LLM_TIMEOUT_SEC,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")
    except requests.exceptions.Timeout:
        logger.error("Ollama request timed out after %ss", LLM_TIMEOUT_SEC)
        return "[error: LLM request timed out]"
    except requests.exceptions.ConnectionError:
        logger.error("Cannot reach Ollama at %s — is it running?", OLLAMA_URL)
        return "[error: cannot reach LLM service]"
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        return "[error: LLM call failed]"
