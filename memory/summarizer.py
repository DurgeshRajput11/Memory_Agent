"""
Session summarizer — compresses old session turns into episodic memory.

Periodically called to move conversation history from short-term (RAM)
to mid-term episodic storage with vector embeddings.
"""

import logging
from typing import List, Dict
from llm.generator import call_llm
from memory.episodic_store import store_episode

logger = logging.getLogger(__name__)

# Summarize every N turns
SUMMARIZE_EVERY = 20


_SUMMARIZATION_PROMPT = """Summarize this conversation in 2-3 concise sentences.

Focus on:
- Key facts shared by the user
- Main topics discussed
- Important decisions or commitments

Conversation:
{conversation}

Summary:"""


def summarize_turns(turns: List[Dict[str, str]]) -> str:
    """
    Use LLM to create a summary of conversation turns.
    
    Args:
        turns: List of {"role": "user"|"assistant", "content": "..."}
    
    Returns:
        Summary string
    """
    conversation_text = "\n".join(
        f"{turn['role'].capitalize()}: {turn['content'][:100]}"  # Limit to 100 chars per turn
        for turn in turns
    )
    
    prompt = _SUMMARIZATION_PROMPT.format(conversation=conversation_text)
    
    try:
        import requests
        from config import OLLAMA_URL, LLM_MODEL, LLM_TIMEOUT_SEC
        
        # Direct call with more tokens for summarization
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 150,
                },
            },
            timeout=LLM_TIMEOUT_SEC,
        )
        resp.raise_for_status()
        summary = resp.json().get("response", "").strip()
        logger.info("Generated summary (%d chars) from %d turns", len(summary), len(turns))
        return summary
    except Exception as e:
        logger.error("Summarization failed: %s", e, exc_info=True)
        # Fallback: just concatenate
        return " | ".join(t["content"][:50] for t in turns[:5])


def should_summarize(session_length: int) -> bool:
    """Check if session has enough turns to warrant summarization."""
    return session_length >= SUMMARIZE_EVERY


def compress_session_to_episodic(
    user_id: str,
    session_history: List[Dict[str, str]],
    turn_offset: int = 0
) -> bool:
    """
    Take old session turns, summarize them, and store in episodic memory.
    
    Args:
        user_id: User identifier
        session_history: List of turns to compress
        turn_offset: Global turn number offset (for turn_start/turn_end)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if len(session_history) < 5:
            logger.debug("Too few turns to compress (%d)", len(session_history))
            return False
        
        logger.info("🔄 Starting compression for %d turns (user=%s, offset=%d)", 
                   len(session_history), user_id, turn_offset)
        
        summary = summarize_turns(session_history)
        
        if not summary or len(summary) < 10:
            logger.warning("Summary too short or empty, skipping storage")
            return False
        
        turn_start = turn_offset
        turn_end = turn_offset + len(session_history) - 1
        
        success = store_episode(user_id, summary, turn_start, turn_end)
        
        if success:
            logger.info("✅ Compressed turns %d-%d into episodic memory for user %s", 
                       turn_start, turn_end, user_id)
        else:
            logger.error("❌ Failed to store episode in database")
        
        return success
        
    except Exception as e:
        logger.error("❌ Compression failed with exception: %s", e, exc_info=True)
        return False
