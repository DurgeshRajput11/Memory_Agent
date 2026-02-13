"""
Multi-stage retrieval harness — combines deterministic, episodic, and ranking.

Stage 1: Semantic fact retrieval using query-to-key similarity
Stage 2: Episodic memory vector search (conversational context)
Stage 3: Ranking by relevance + importance + recency
"""

import logging
from typing import List, Dict
from memory.structured_facts import get_all_facts
from memory.episodic_store import retrieve_episodes
from database import embed
from config import CANONICAL_KEY_MAPPING

logger = logging.getLogger(__name__)


def _compute_key_relevance(query: str, fact_key: str) -> float:
    """
    Compute relevance score between query and fact key using semantic similarity.
    Returns score 0.0-1.0 (higher = more relevant).
    """
    try:
        from sentence_transformers import util
        import torch
        
        # Generate embeddings
        query_emb = torch.tensor(eval(embed(query)))
        key_emb = torch.tensor(eval(embed(fact_key)))
        
        # Compute cosine similarity
        similarity = util.cos_sim(query_emb, key_emb).item()
        return max(0.0, similarity)  # Clamp to 0-1
    except Exception as e:
        logger.warning("Similarity computation failed: %s", e)
        # Fallback: simple keyword match
        return 1.0 if fact_key.lower() in query.lower() else 0.0


def retrieve_all(
    user_id: str,
    query: str,
    top_k_facts: int = 5,
    top_k_episodes: int = 3,
) -> Dict:
    """
    Execute full 2-stage retrieval with semantic ranking.
    
    Returns dict:
    {
        "structured_facts": [...],     # Top-K relevant facts
        "episodic_context": [...],     # Relevant conversation episodes
        "total_items": int
    }
    """
    results = {
        "structured_facts": [],
        "episodic_context": [],
        "total_items": 0
    }
    
    # Stage 1: Semantic fact retrieval
    # Get all facts, then rank by query relevance
    all_facts = get_all_facts(user_id, min_importance=0.3)
    
    if query.strip().endswith('?'):
        # User is asking a question - rank facts by relevance
        scored_facts = []
        for fact in all_facts:
            relevance = _compute_key_relevance(query, fact['key'])
            # Boost by importance
            score = relevance * 0.7 + fact.get('importance', 0.5) * 0.3
            scored_facts.append((score, fact))
        
        # Sort by score and take top K
        scored_facts.sort(reverse=True, key=lambda x: x[0])
        results["structured_facts"] = [f for score, f in scored_facts[:top_k_facts] if score > 0.2]
    else:
        # User is making a statement - include recent important facts
        results["structured_facts"] = sorted(
            all_facts, 
            key=lambda f: f.get('importance', 0.5), 
            reverse=True
        )[:top_k_facts]
    
    logger.info("Stage 1 (Semantic): Retrieved %d/%d facts", len(results["structured_facts"]), len(all_facts))
    
    # Stage 2: Episodic vector retrieval
    episodes = retrieve_episodes(user_id, query, top_k=top_k_episodes)
    results["episodic_context"] = episodes
    logger.info("Stage 2 (Episodic): Retrieved %d episodes", len(episodes))
    
    # Calculate total items
    results["total_items"] = len(results["structured_facts"]) + len(episodes)
    
    return results


def format_for_injection(retrieval_results: Dict, max_tokens: int = 400) -> str:
    """
    Format retrieval results into clean prompt injection text.
    
    Args:
        retrieval_results: Output from retrieve_all()
        max_tokens: Approximate token budget (rough estimate: 1 token ≈ 4 chars)
    
    Returns:
        Formatted string ready for prompt injection
    """
    lines = []
    char_budget = max_tokens * 4  # Rough conversion
    current_chars = 0
    
    # Section 1: Structured Facts
    facts = retrieval_results["structured_facts"]
    if facts:
        lines.append("## User Profile")
        for fact in facts:
            line = f"- {fact['key']}: {fact['value']}"
            if current_chars + len(line) > char_budget:
                break
            lines.append(line)
            current_chars += len(line)
    
    # Section 2: Episodic Context
    episodes = retrieval_results["episodic_context"]
    if episodes and current_chars < char_budget:
        lines.append("\n## Recent Context")
        for ep in episodes:
            line = f"- {ep['turn_range']}: {ep['summary'][:150]}..."
            if current_chars + len(line) > char_budget:
                break
            lines.append(line)
            current_chars += len(line)
    
    return "\n".join(lines) if lines else "No relevant memory found."
