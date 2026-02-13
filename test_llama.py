"""Test llama3.2:3b and all the fixes."""

import requests
import time

BASE_URL = "http://localhost:8000"
USER_ID = "test_llama_" + str(int(time.time()))

def chat(msg):
    resp = requests.post(f"{BASE_URL}/chat", json={"user_id": USER_ID, "message": msg})
    data = resp.json()
    print(f"\n👤 User: {msg}")
    print(f"🤖 Bot:  {data['response']}")
    print(f"⏱️  {data['latency_ms']}ms")
    return data

print("="*70)
print("TESTING LLAMA3.2:3B WITH ALL FIXES")
print("="*70)

# Provide facts
chat("Hi, my name is Alex")
time.sleep(2)

chat("I'm a software engineer in Seattle")
time.sleep(2)

chat("I prefer Python for coding")
time.sleep(2)

chat("Always use black formatter with line length 100")
time.sleep(2)

chat("I'm working on a hackathon project")
time.sleep(2)

print("\n" + "="*70)
print("TESTING RECALL (should use semantic retrieval)")
print("="*70)

# Test recall
chat("What's my name?")
chat("What programming language do I prefer?")
chat("What's my code formatter?")
chat("What's my line length?")
chat("What am I working on?")

print("\n" + "="*70)
print("CLEANING UP TEST DATA")
print("="*70)

# Clean up database
import psycopg2
from config import DB_CONFIG

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Delete structured facts
    cur.execute("DELETE FROM structured_facts WHERE user_id = %s", (USER_ID,))
    facts_deleted = cur.rowcount
    
    # Delete episodic memory
    cur.execute("DELETE FROM episodic_memory WHERE user_id = %s", (USER_ID,))
    episodes_deleted = cur.rowcount
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"✅ Deleted {facts_deleted} facts and {episodes_deleted} episodes for user {USER_ID}")
    
except Exception as e:
    print(f"❌ Cleanup failed: {e}")

print("="*70)
