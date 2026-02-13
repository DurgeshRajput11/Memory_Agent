"""Quick test to verify memory extraction is working."""

import requests
import time

BASE_URL = "http://localhost:8000"
USER_ID = "test_user_" + str(int(time.time()))

def test_chat(message: str):
    """Send a message and check response."""
    resp = requests.post(
        f"{BASE_URL}/chat",
        json={"user_id": USER_ID, "message": message}
    )
    data = resp.json()
    print(f"User: {message}")
    print(f"Bot:  {data['response'][:100]}...")
    print(f"⏱️   {data['latency_ms']}ms\n")
    return data

# Test sequence with facts
print("=" * 70)
print("EXTRACTION TEST")
print("=" * 70)
print()

test_chat("Hi, my name is Sarah")
time.sleep(2)  # Wait for background extraction

test_chat("I'm a data scientist in New York")
time.sleep(2)

test_chat("I prefer Python with type hints")
time.sleep(2)

test_chat("Always use pytest for testing")
time.sleep(2)

# Memory recall test
test_chat("What's my name?")
test_chat("What's my job?")
test_chat("Which programming language do I prefer?")

print("=" * 70)
print("Check database with:")
print(f"  SELECT * FROM structured_facts WHERE user_id='{USER_ID}';")
print("=" * 70)
