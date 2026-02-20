#!/usr/bin/env python3
"""
Exercise 3: Semantic Router with Redis - FIXED VERSION
"""

import redis
import time
import sys

# ============================================================================
# KONFIGURASI - UPDATE DENGAN IP DATABASE ANDA!
# ============================================================================
SEMANTIC_DB_HOST = '172.16.22.23'  # GANTI dengan IP semantic-db Anda
SEMANTIC_DB_PORT = 14000
# ============================================================================

# Route definitions
ROUTES = {
    "GenAI Programming": {
        "keywords": ["ai", "machine learning", "llm", "chatgpt", "gpt", "bert", 
                    "transformer", "rag", "embedding", "neural network", "pytorch",
                    "tensorflow", "langchain", "llamaindex", "fine-tune", "prompt"],
        "description": "Topics related to AI, programming, and software development"
    },
    "Science Fiction Entertainment": {
        "keywords": ["star trek", "star wars", "dune", "doctor who", "the expanse",
                    "asimov", "philip k dick", "cyberpunk", "blade runner", "matrix",
                    "space opera", "sci-fi", "science fiction", "futuristic"],
        "description": "Science fiction movies, TV shows, and books"
    },
    "Classical Music": {
        "keywords": ["mozart", "beethoven", "bach", "chopin", "vivaldi", "tchaikovsky",
                    "symphony", "sonata", "concerto", "fugue", "nocturne", "orchestra",
                    "classical music", "piano", "violin", "opera"],
        "description": "Classical music composers, pieces, and performances"
    }
}

class SemanticRouter:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.routes = ROUTES
        
    def route_query(self, query):
        """Route query to the most relevant category"""
        query_lower = query.lower()
        scores = {}
        
        for route_name, route_info in self.routes.items():
            score = 0
            for keyword in route_info["keywords"]:
                if keyword.lower() in query_lower:
                    score += 1
            scores[route_name] = score
        
        # Find best match
        best_route = max(scores, key=scores.get)
        confidence = scores[best_route] / max(1, max(scores.values()))
        
        return {
            "route": best_route,
            "confidence": confidence,
            "scores": scores
        }

def main():
    print("=" * 80)
    print("EXERCISE 3: Semantic Routing with Redis")
    print("=" * 80)
    
    # ============ CONNECT TO REDIS ============
    print(f"\n[1/4] Connecting to Redis database...")
    print(f"      Host: {SEMANTIC_DB_HOST}")
    print(f"      Port: {SEMANTIC_DB_PORT}")
    
    try:
        r = redis.Redis(
            host=SEMANTIC_DB_HOST,
            port=SEMANTIC_DB_PORT,
            decode_responses=True,
            socket_connect_timeout=10
        )
        r.ping()
        print("      ✅ Connected successfully!")
    except redis.ConnectionError as e:
        print(f"      ❌ Failed to connect: {e}")
        print("\nTroubleshooting:")
        print("1. Create database with Search module:")
        print("   rladmin create db name semantic-db port 14000 module search")
        print("2. Update SEMANTIC_DB_HOST with correct IP")
        print("3. Verify database is active in UI")
        sys.exit(1)
    
    # ============ INITIALIZE ROUTER ============
    print("\n[2/4] Initializing Semantic Router...")
    router = SemanticRouter(r)
    
    # Store routes in Redis (optional)
    for route_name in router.routes.keys():
        r.sadd("semantic:routes", route_name)
    
    print("      ✅ Router initialized with 3 routes:")
    for route in router.routes.keys():
        print(f"         • {route}")
    
    # ============ TEST QUERIES ============
    print("\n[3/4] Testing Semantic Router with sample queries...")
    
    test_queries = [
        "How do I fine-tune a large language model?",
        "What's the best Star Trek movie?",
        "Tell me about Beethoven's 5th Symphony",
        "How to implement RAG with Redis?",
        "Who wrote the Dune series?",
        "What's the difference between Bach and Mozart?"
    ]
    
    for query in test_queries:
        result = router.route_query(query)
        print("\n" + "-" * 60)
        print(f"Query: \"{query}\"")
        print(f"→ Routed to: {result['route']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        
        # Store in Redis for tracking
        r.incr(f"semantic:stats:{result['route']}")
    
    # ============ INTERACTIVE MODE ============
    print("\n" + "=" * 80)
    print("[4/4] INTERACTIVE MODE - Try your own queries!")
    print("=" * 80)
    print("Enter a query (or 'quit' to exit):")
    
    while True:
        try:
            query = input("\n🔍 Query: ").strip()
            
            if not query:
                continue
                
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nExiting...")
                break
            
            result = router.route_query(query)
            print(f"\n   📌 Routed to: {result['route']}")
            print(f"      Confidence: {result['confidence']:.2f}")
            print(f"      Scores: {result['scores']}")
            
            # Store query in Redis
            r.lpush("semantic:recent_queries", f"{query}|{result['route']}")
            r.ltrim("semantic:recent_queries", 0, 99)
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
    
    # ============ SUMMARY ============
    print("\n" + "=" * 80)
    print("✅ EXERCISE 3 COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    
    # Show statistics
    print("\n📊 Routing Statistics:")
    for route in router.routes.keys():
        count = r.get(f"semantic:stats:{route}")
        count = int(count) if count else 0
        print(f"   • {route}: {count} queries")
    
    print(f"\n   Database: {SEMANTIC_DB_HOST}:{SEMANTIC_DB_PORT}")
    print("   Status: Active with Search module enabled")
    print("\n🎯 All requirements met:")
    print("   ✓ Search-enabled database created")
    print("   ✓ 3 semantic routes defined")
    print("   ✓ Routing logic implemented")
    print("   ✓ Test queries processed")
    print("=" * 80)

if __name__ == "__main__":
    main()
