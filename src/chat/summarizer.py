import asyncio
import logging
import re
from typing import List

from src.chat.history import get_chat_history
from src.llm.ollama_client import get_ollama_client

logger = logging.getLogger(__name__)

SUMMARY_INTERVAL_SECONDS = 5 * 60
MAX_TITLE_WORDS = 3
MAX_MESSAGES_FOR_SUMMARY = 12

SUMMARY_SYSTEM_PROMPT = (
    "Du erstellst extrem kurze Titel für Chat-Unterhaltungen. "
    "Antworte mit HÖCHSTENS 3 Wörtern, die das Thema beschreiben. "
    "Keine Anführungszeichen, keine Satzzeichen, keine Erklärung."
)


def _build_prompt(messages: List[dict]) -> str:
    recent = messages[-MAX_MESSAGES_FOR_SUMMARY:]
    lines = []
    for m in recent:
        role = "Nutzer" if m["role"] == "user" else "Assistent"
        content = (m["content"] or "").strip().replace("\n", " ")
        if content:
            lines.append(f"{role}: {content}")
    conversation = "\n".join(lines)
    return (
        "Fasse das Thema dieser Unterhaltung in höchstens 3 Wörtern zusammen.\n\n"
        f"{conversation}\n\nTitel:"
    )


def enforce_title(raw: str) -> str:
    """Reduce arbitrary model output to a clean title of at most 3 words."""
    if not raw:
        return ""
    text = raw.strip()
    # Take the first non-empty line only.
    for line in text.splitlines():
        if line.strip():
            text = line.strip()
            break
    # Drop a leading "Titel:" style label if the model echoes it.
    text = re.sub(r"^\s*titel\s*:\s*", "", text, flags=re.IGNORECASE)
    # Strip surrounding quotes/brackets and trailing punctuation.
    text = text.strip(" \t\"'`*_[](){}.,;:!?-")
    words = text.split()
    if not words:
        return ""
    return " ".join(words[:MAX_TITLE_WORDS])


def summarize_once() -> int:
    """Summarize all sessions with new activity. Returns number updated."""
    history = get_chat_history()
    client = get_ollama_client()
    sessions = history.get_sessions_needing_summary()
    updated = 0
    for session in sessions:
        session_id = session["id"]
        messages = history.get_messages(session_id)
        if not messages:
            continue
        try:
            raw = client.generate(
                _build_prompt(messages),
                system_prompt=SUMMARY_SYSTEM_PROMPT,
                temperature=0.2,
            )
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("Summarization failed for session %s: %s", session_id, e)
            continue
        if raw.startswith("Error:"):
            logger.warning("Summarization error for session %s: %s", session_id, raw)
            continue
        title = enforce_title(raw)
        if not title:
            continue
        history.mark_summarized(session_id, title)
        updated += 1
    if updated:
        logger.info("Auto-summarizer updated %d session title(s)", updated)
    return updated


async def run_summarizer_loop(interval_seconds: int = SUMMARY_INTERVAL_SECONDS):
    """Background loop that periodically refreshes session titles."""
    logger.info("Starting session auto-summarizer (every %ds)", interval_seconds)
    while True:
        try:
            await asyncio.to_thread(summarize_once)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("Summarizer loop iteration failed: %s", e)
        await asyncio.sleep(interval_seconds)
