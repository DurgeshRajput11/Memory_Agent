🧠 Long-Term Memory System for LLM (1000+ Turn Conversations)
=============================================================

📌 Overview
-----------

This project implements a structured long-term memory system around a Large Language Model (LLM) to support **1000+ turn conversations** in a single session without replaying the entire transcript.

The system is designed to:

*   Maintain conversational continuity
    
*   Store and retrieve persistent user information
    
*   Operate under strict latency constraints (<500ms target)
    
*   Avoid memory hallucinations
    
*   Scale to long, evolving dialogues
    

🏗 Architecture
---------------

The system uses a **three-tier memory architecture**:

### 1️⃣ Short-Term Memory (Session Memory)

*   Stores recent conversation turns
    
*   Maintains a sliding window of last _N_ messages
    
*   Stored in-memory (Python object)
    
*   Used for immediate conversational context
    

### 2️⃣ Active Long-Term Memory

*   Stores important persistent user data:
    
    *   Preferences
        
    *   Constraints
        
    *   Commitments
        
    *   Standing instructions
        
*   Stored in PostgreSQL with pgvector embeddings
    
*   Retrieved using semantic similarity search
    
*   Injected selectively into prompt
    

### 3️⃣ Archived Long-Term Memory (Optional Extension)

*   Stores older or lower-priority memories
    
*   Can be compressed into summaries
    
*   Retrieved only if highly relevant
    

🔄 Memory Flow
--------------

User Message 

↓  

Retrieval Policy Decision    

↓  

Vector Retrieval (Top-K)  

↓ 

Prompt Construction  

↓  

LLM Response Generation  

↓ 

Memory Extraction 

↓ 

Database Storage   `

Only relevant memories are injected.No full transcript replay is used.

🛠 Tech Stack
-------------

*   **LLM:** phi3:mini (via Ollama)
    
*   **Embeddings:** all-MiniLM-L6-v2
    
*   **Backend:** FastAPI
    
*   **Database:** PostgreSQL + pgvector
    
*   **Vector Search:** pgvector similarity
    
*   **Hardware:** RTX 3050 (optional GPU acceleration)
    

📂 Project Structure
--------------------

User Message
↓

Retrieval Policy Decision

↓

Vector Retrieval (Top-K)

↓

Prompt Construction

↓

LLM Response Generation

↓

Memory Extraction

↓

Database Storage

⚡ Latency Strategy (<500ms Target)
----------------------------------

To meet strict latency requirements:

*   Single LLM call per request
    
*   Small Top-K memory retrieval
    
*   Lightweight embedding model
    
*   Minimal prompt size
    
*   No LangChain / LangGraph overhead
    
*   Optional async memory extraction
    

🧠 Retrieval Strategy
---------------------

Memories are ranked using:

*   Semantic similarity (vector distance)
    
*   Memory type filtering
    
*   Optional recency weighting
    
*   Confidence thresholding
    

Only top relevant memories are injected to reduce hallucination risk.

🧪 Evaluation Approach
----------------------

The system can be evaluated using:

*   Long-range recall accuracy
    
*   Memory precision
    
*   Hallucination rate
    
*   Latency benchmarking
    
*   Synthetic 100–1000 turn conversation tests
    

Evaluation logs include retrieved memory IDs for transparency.

🔐 Hallucination Mitigation
---------------------------

*   No injection if similarity below threshold
    
*   Structured memory schema
    
*   Strict memory extraction format
    
*   Type-aware memory usage
    

🚀 Setup & Run
--------------

### 1️⃣ Install dependencies

pip install fastapi uvicorn psycopg2 sentence-transformers   `

### 2️⃣ Ensure PostgreSQL + pgvector is running

Port: 5432

### 3️⃣ Pull LLM model

 ollama pull phi3:mini   `

### 4️⃣ Start server
  uvicorn app:app --reload   `

🎯 Design Philosophy
--------------------

*   Explicit memory separation (short vs long term)
    
*   Controlled memory injection
    
*   Minimal abstraction
    
*   Framework-independent architecture
    
*   Evaluation-first design
    

🔮 Future Improvements
----------------------

*   Temporal decay scoring
    
*   Episodic memory summarization
    
*   Memory consolidation
    
*   User-editable memory
    
*   Hybrid vector + knowledge graph model
    

📎 Problem Alignment
--------------------

This solution directly addresses:

*   1000+ turn single-session conversations
    
*   Real-time retrieval without full replay
    
*   Structured long-term memory persistence
    
*   Strict latency constraints
    
*   Transparent evaluation mechanism


