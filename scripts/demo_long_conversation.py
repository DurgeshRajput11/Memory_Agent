#!/usr/bin/env python3
"""
Long conversation demo — simulates 100+ turn conversation to showcase memory system.

This script:
1. Sends a series of messages that establish user facts and context
2. Tests recall of facts across many turns
3. Shows episodic memory compression
4. Outputs metrics (facts stored, episodes created, latency, recall accuracy)
"""

import requests
import time
import json
from typing import List, Dict

API_URL = "http://localhost:8000/chat"
USER_ID = "demo_user_001"

# Color codes for terminal output
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


# Conversation script with 100+ turns
CONVERSATION_TURNS = [
    # Phase 1: Establish identity and preferences (turns 1-10)
    "Hi, my name is Alex",
    "I prefer to speak in English",
    "I'm located in San Francisco, Pacific timezone",
    "I'm a software engineer working on AI systems",
    "I love Python and prefer type hints in all my code",
    "Always use black for code formatting with line length 100",
    "I'm learning about memory systems for LLMs",
    "Can you help me understand how vector databases work?",
    "What's the difference between FAISS and pgvector?",
    "Thanks! That's helpful",
    
    # Phase 2: More context and conversation (turns 11-30)
    "I'm also interested in retrieval augmented generation",
    "What are the best practices for prompt engineering?",
    "How do you handle context windows in long conversations?",
    "I've been experimenting with LangChain",
    "What do you think about semantic chunking strategies?",
    "Tell me about embedding models",
    "What's the difference between dense and sparse embeddings?",
    "How do you measure retrieval quality?",
    "What metrics should I track?",
    "I prefer pytest for testing Python code",
    "Always add docstrings to functions",
    "I use FastAPI for building APIs",
    "What's your recommendation for async Python patterns?",
    "How do you handle database connection pooling?",
    "I'm working on a hackathon project right now",
    "It's about long-term memory for chatbots",
    "The goal is to remember facts across 1000+ turns",
    "We're using PostgreSQL with pgvector",
    "The challenge is keeping latency under 500ms",
    "What's your advice on optimizing vector search?",
    
    # Phase 3: Test recall (turns 31-50)
    "Quick question - what's my name?",
    "What programming language do I prefer?",
    "What timezone am I in?",
    "What's my code formatting preference?",
    "What am I working on currently?",
    "Which testing framework do I use?",
    "Do you remember what I'm trying to build?",
    "What's the latency target for my project?",
    "What database am I using?",
    "Good! You remembered. Now let's talk about scaling",
    "How do you scale vector search to millions of documents?",
    "What about approximate nearest neighbor algorithms?",
    "Tell me about HNSW indexes",
    "How does quantization help with vector storage?",
    "What's the trade-off between accuracy and speed?",
    "I'm considering sharding my vector database",
    "What are the best practices?",
    "How do you handle versioning of embeddings?",
    "What if the embedding model changes?",
    "These are all great points",
    
    # Phase 4: More conversation to build episodic memory (turns 51-80)
    "Let's shift topics - tell me about system design",
    "How do you design for high availability?",
    "What's your approach to load balancing?",
    "How do you handle database replication?",
    "What about cache invalidation strategies?",
    "I'm reading about microservices architecture",
    "What are the main challenges?",
    "How do you handle distributed transactions?",
    "Tell me about the saga pattern",
    "What's your take on event-driven architecture?",
    "How do you ensure data consistency?",
    "What monitoring tools do you recommend?",
    "How do you handle logging in distributed systems?",
    "What about distributed tracing?",
    "I've heard about OpenTelemetry",
    "How does it compare to other solutions?",
    "What metrics are most important to track?",
    "How do you set up alerting?",
    "What's a good incident response process?",
    "I'm learning so much from this conversation",
    "Let's talk about security now",
    "How do you secure API endpoints?",
    "What's your approach to authentication?",
    "Should I use JWT or session tokens?",
    "How do you handle authorization?",
    "What about rate limiting?",
    "How do you prevent SQL injection?",
    "What's the best way to store sensitive data?",
    "Tell me about encryption at rest",
    "What about encryption in transit?",
    
    # Phase 5: More recall tests (turns 81-100)
    "Before we continue - what's my name again?",
    "What am I currently working on?",
    "What's my preferred programming language?",
    "What's my code line length preference?",
    "Which API framework do I use?",
    "Excellent memory! Now let's discuss deployment",
    "How do you approach CI/CD?",
    "What's your preferred deployment strategy?",
    "Blue-green or canary deployments?",
    "How do you handle database migrations?",
    "What about zero-downtime deployments?",
    "I'm using Docker for containerization",
    "What's your take on Kubernetes vs simpler solutions?",
    "How do you manage secrets in production?",
    "What about configuration management?",
    "Tell me about infrastructure as code",
    "Should I use Terraform or CloudFormation?",
    "How do you structure your IaC repos?",
    "What's your backup strategy?",
    "How do you test disaster recovery?",
    
    # Phase 6: Final recall test (turns 101-110)
    "Let's do a final memory check",
    "What's my full name?",
    "Where am I located?",
    "What's my timezone?",
    "What project am I working on?",
    "What's the goal of that project?",
    "What's my target latency?",
    "Which database am I using?",
    "What's my preferred code formatter?",
    "What line length do I use?",
]


def send_message(message: str) -> Dict:
    """Send a chat message and return response with metadata."""
    try:
        start = time.time()
        resp = requests.post(API_URL, json={"user_id": USER_ID, "message": message}, timeout=30)
        latency = time.time() - start
        
        if resp.status_code == 200:
            data = resp.json()
            return {
                "success": True,
                "response": data["response"],
                "llm_latency_ms": data.get("latency_ms", 0),
                "total_latency_ms": latency * 1000,
                "error": None
            }
        else:
            return {
                "success": False,
                "response": None,
                "llm_latency_ms": 0,
                "total_latency_ms": latency * 1000,
                "error": f"HTTP {resp.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "response": None,
            "llm_latency_ms": 0,
            "total_latency_ms": 0,
            "error": str(e)
        }


def check_recall(response: str, expected_facts: List[str]) -> int:
    """Check if response contains expected facts. Returns count of matched facts."""
    response_lower = response.lower()
    matches = sum(1 for fact in expected_facts if fact.lower() in response_lower)
    return matches


def run_demo():
    """Run the full 100+ turn conversation demo."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}🧠 Long-Term Memory System Demo — 100+ Turn Conversation{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    print(f"User ID: {USER_ID}")
    print(f"Total turns: {len(CONVERSATION_TURNS)}")
    print(f"API: {API_URL}\n")
    
    # Metrics
    total_latency = []
    successful_turns = 0
    failed_turns = 0
    recall_tests = []
    
    # Run conversation
    for i, message in enumerate(CONVERSATION_TURNS, 1):
        print(f"\n{GREEN}[Turn {i}/{len(CONVERSATION_TURNS)}]{RESET}")
        print(f"{YELLOW}User:{RESET} {message}")
        
        result = send_message(message)
        
        if result["success"]:
            successful_turns += 1
            total_latency.append(result["total_latency_ms"])
            print(f"{BLUE}Assistant:{RESET} {result['response'][:150]}...")
            print(f"  ⏱️  Latency: {result['total_latency_ms']:.0f}ms (LLM: {result['llm_latency_ms']:.0f}ms)")
            
            # Check recall for specific test questions
            if "what's my name" in message.lower():
                matches = check_recall(result["response"], ["Alex"])
                recall_tests.append(("name", matches > 0))
                print(f"  {'✓' if matches > 0 else '✗'} Recall test: name")
            
            elif "what programming language" in message.lower() or "language do i prefer" in message.lower():
                matches = check_recall(result["response"], ["Python"])
                recall_tests.append(("language", matches > 0))
                print(f"  {'✓' if matches > 0 else '✗'} Recall test: language")
            
            elif "what timezone" in message.lower() or "where am i located" in message.lower():
                matches = check_recall(result["response"], ["Pacific", "San Francisco"])
                recall_tests.append(("location", matches > 0))
                print(f"  {'✓' if matches > 0 else '✗'} Recall test: location")
            
            elif "working on" in message.lower() and "?" in message:
                matches = check_recall(result["response"], ["hackathon", "memory", "chatbot"])
                recall_tests.append(("project", matches > 0))
                print(f"  {'✓' if matches > 0 else '✗'} Recall test: project")
            
            elif "code formatter" in message.lower() or "formatting preference" in message.lower():
                matches = check_recall(result["response"], ["black", "100"])
                recall_tests.append(("formatter", matches > 0))
                print(f"  {'✓' if matches > 0 else '✗'} Recall test: formatter")
        
        else:
            failed_turns += 1
            print(f"{RED}❌ Error: {result['error']}{RESET}")
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.2)
    
    # Print final metrics
    print(f"\n\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}📊 Demo Results{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    print(f"✅ Successful turns: {successful_turns}/{len(CONVERSATION_TURNS)}")
    print(f"❌ Failed turns: {failed_turns}/{len(CONVERSATION_TURNS)}")
    
    if total_latency:
        avg_latency = sum(total_latency) / len(total_latency)
        max_latency = max(total_latency)
        min_latency = min(total_latency)
        print(f"\n⏱️  Latency Stats:")
        print(f"   Average: {avg_latency:.0f}ms")
        print(f"   Min: {min_latency:.0f}ms")
        print(f"   Max: {max_latency:.0f}ms")
    
    if recall_tests:
        correct = sum(1 for _, passed in recall_tests if passed)
        total = len(recall_tests)
        accuracy = (correct / total) * 100 if total > 0 else 0
        print(f"\n🎯 Recall Accuracy: {correct}/{total} ({accuracy:.0f}%)")
        print(f"   Tests performed:")
        for test_name, passed in recall_tests:
            print(f"     {'✓' if passed else '✗'} {test_name}")
    
    print(f"\n{GREEN}Demo complete!{RESET}")
    print(f"\n{YELLOW}Note: Check your database to see:{RESET}")
    print(f"  - Structured facts stored (should have ~10-15 key facts)")
    print(f"  - Episodic memory chunks created (should have ~5-6 episodes)")
    print(f"\n{BLUE}{'='*80}{RESET}\n")
    
    # Cleanup: Delete demo data
    cleanup_demo_data()


def cleanup_demo_data():
    """Clean up demo user data from database."""
    print(f"\n{YELLOW}Cleaning up demo data...{RESET}")
    
    try:
        import sys
        import os
        # Add parent directory to path to import config
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        import psycopg2
        from config import DB_CONFIG
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Delete structured facts
        cur.execute("DELETE FROM structured_facts WHERE user_id = %s", (USER_ID,))
        facts_deleted = cur.rowcount
        
        # Delete episodic memory
        cur.execute("DELETE FROM episodic_memory WHERE user_id = %s", (USER_ID,))
        episodes_deleted = cur.rowcount
        
        # Delete from profile_memory (legacy table if it exists)
        try:
            cur.execute("DELETE FROM profile_memory WHERE user_id = %s", (USER_ID,))
            profile_deleted = cur.rowcount
        except:
            profile_deleted = 0
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"{GREEN}✅ Cleaned up demo data:{RESET}")
        print(f"   - Deleted {facts_deleted} structured facts")
        print(f"   - Deleted {episodes_deleted} episodic memories")
        if profile_deleted > 0:
            print(f"   - Deleted {profile_deleted} profile entries")
        print(f"\n{BLUE}Database is ready for next demo run!{RESET}")
        
    except Exception as e:
        print(f"{RED}❌ Cleanup failed: {e}{RESET}")
        print(f"{YELLOW}You may need to manually clean the database.{RESET}")


if __name__ == "__main__":
    print("\n⚠️  Make sure the API server is running: uvicorn app:app --reload\n")
    input("Press Enter to start the demo...")
    run_demo()
