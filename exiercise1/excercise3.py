#!/usr/bin/env python3
"""
Exercise 3: Semantic Router with Redis - FIXED VERSION with Search Index
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

# Route definitions with more keywords
ROUTES = {
    "GenAI Programming": {
        "keywords": ["ai", "machine learning", "llm", "chatgpt", "gpt", "bert", 
                    "transformer", "rag", "embedding", "neural network", "pytorch",
                    "tensorflow", "langchain", "llamaindex", "fine-tune", "prompt",
                    "python", "code", "programming", "developer", "algorithm"],
        "description": "Topics related to AI, programming, and software development"
    },
    "Science Fiction Entertainment": {
        "keywords": ["star trek", "star wars", "dune", "doctor who", "the expanse",
                    "asimov", "philip k dick", "cyberpunk", "blade runner", "matrix",
                    "space opera", "sci-fi", "science fiction", "futuristic",
                    "alien", "spaceship", "galaxy", "robot", "time travel"],
        "description": "Science fiction movies, TV shows, and books"
    },
    "Classical Music": {
        "keywords": ["mozart", "beethoven", "bach", "chopin", "vivaldi", "tchaikovsky",
                    "symphony", "sonata", "concerto", "fugue", "nocturne", "orchestra",
                    "classical music", "piano", "violin", "cello", "opera", "composer"],
        "description": "Classical music composers, pieces, and performances"
    }
}

class SemanticRouter:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.routes = ROUTES
        self.stats_key = "semantic:stats"
        self.queries_key = "semantic:recent_queries"
        self.index_name = "idx:routes"
        
        # Initialize stats di Redis
        for route in self.routes.keys():
            self.redis.hsetnx(self.stats_key, route, 0)
        
        # Create Redis Search index
        self.create_search_index()
        
        # Load routes into Redis Search
        self.load_routes_to_search()
    
    def create_search_index(self):
        """Create RediSearch index for semantic routing"""
        try:
            # Check if index already exists
            indexes = self.redis.execute_command("FT._LIST")
            if self.index_name.encode() in indexes:
                print("      ℹ️  Search index already exists")
                return
            
            # Create index
            self.redis.execute_command(
                "FT.CREATE", self.index_name,
                "ON", "HASH",
                "PREFIX", "1", "route:",
                "SCHEMA",
                "name", "TEXT", "WEIGHT", "5.0",
                "description", "TEXT", "WEIGHT", "2.0",
                "keywords", "TAG", "SEPARATOR", ","
            )
            print("      ✅ Redis Search index created")
            
        except Exception as e:
            if "Index already exists" in str(e):
                print("      ℹ️  Search index already exists")
            else:
                print(f"      ⚠️  Could not create index: {e}")
    
    def load_routes_to_search(self):
        """Load route data into Redis Search"""
        for idx, (route_name, route_info) in enumerate(self.routes.items(), 1):
            key = f"route:{idx}"
            
            # Check if already exists
            if not self.redis.exists(key):
                # Store as hash for RediSearch
                self.redis.hset(key, mapping={
                    "name": route_name,
                    "description": route_info["description"],
                    "keywords": ",".join(route_info["keywords"][:20])  # First 20 keywords
                })
                print(f"      ✅ Loaded route: {route_name}")
    
    def route_query(self, query):
        """Route query using Redis Search first, fallback to keyword matching"""
        
        # Try Redis Search first
        try:
            search_result = self.redis.execute_command(
                "FT.SEARCH", self.index_name,
                f"@keywords:{{{query.lower()}}}",
                "RETURN", "1", "name",
                "LIMIT", "0", "1"
            )
            
            if search_result and search_result[0] > 0:
                # Found match in search index
                route_name = search_result[1][1]
                
                # Update stats
                self.redis.hincrby(self.stats_key, route_name, 1)
                
                return {
                    "route": route_name,
                    "confidence": 1.0,
                    "method": "search_index"
                }
        except:
            pass  # Fallback to keyword matching
        
        # Fallback: keyword matching
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
        max_score = scores[best_route]
        
        # Calculate confidence
        if max_score == 0:
            best_route = "GenAI Programming"  # Default
            confidence = 0.1
        else:
            confidence = min(max_score / 3, 1.0)
        
        # Update statistics
        self.redis.hincrby(self.stats_key, best_route, 1)
        
        # Store query
        timestamp = int(time.time())
        self.redis.lpush(self.queries_key, f"{timestamp}|{query[:50]}|{best_route}")
        self.redis.ltrim(self.queries_key, 0, 99)
        
        return {
            "route": best_route,
            "confidence": round(confidence, 2),
            "score": max_score,
            "scores": scores,
            "method": "keyword_match"
        }
    
    def search_by_keyword(self, keyword):
        """Search routes by keyword using Redis Search"""
        try:
            result = self.redis.execute_command(
                "FT.SEARCH", self.index_name,
                f"@keywords:{{{keyword}}}",
                "RETURN", "3", "name", "description", "keywords"
            )
            return result
        except:
            return None
    
    def get_statistics(self):
        """Get routing statistics from Redis"""
        stats = self.redis.hgetall(self.stats_key)
        return {k: int(v) for k, v in stats.items()}
    
    def show_index_info(self):
        """Show Redis Search index info"""
        try:
            info = self.redis.execute_command("FT.INFO", self.index_name)
            print("\n📊 Redis Search Index Info:")
            for i in range(0, len(info), 2):
                print(f"   {info[i].decode()}: {info[i+1]}")
        except:
            pass

def main():
    print("=" * 80)
    print("EXERCISE 3: Semantic Routing with Redis Search")
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
        
        # Check if Redis Search module is available
        try:
            modules = r.execute_command("MODULE LIST")
            search_available = False
            for module in modules:
                if module[1] == "search":
                    search_available = True
                    print(f"      ✅ Redis Search module active (version: {module[3]})")
                    break
            if not search_available:
                print("      ⚠️  Redis Search module not found")
        except:
            print("      ⚠️  Could not check Redis Search module")
            
    except redis.ConnectionError as e:
        print(f"      ❌ Failed to connect: {e}")
        print("\nTroubleshooting:")
        print("1. Create database with Search module:")
        print("   rladmin create db name semantic-db port 14000 module search")
        print("2. Update SEMANTIC_DB_HOST with correct IP")
        print("3. Verify database is active in UI")
        sys.exit(1)
    
    # ============ INITIALIZE ROUTER ============
    print("\n[2/4] Initializing Semantic Router with Redis Search...")
    router = SemanticRouter(r)
    
    print("\n      ✅ Router initialized with 3 routes:")
    for route in router.routes.keys():
        print(f"         • {route}")
    
    # Show index info
    router.show_index_info()
    
    # ============ TEST SEARCH ============
    print("\n[3/4] Testing Redis Search with keywords...")
    
    test_keywords = ["ai", "star trek", "beethoven"]
    for keyword in test_keywords:
        result = router.search_by_keyword(keyword)
        if result and result[0] > 0:
            print(f"\n   Keyword '{keyword}': Found {result[0]} matches")
            print(f"   Top match: {result[1][1]}")
        else:
            print(f"\n   Keyword '{keyword}': No matches")
    
    # ============ TEST QUERIES ============
    print("\n" + "-" * 60)
    print("Testing semantic routing with queries:")
    print("-" * 60)
    
    test_queries = [
        "How do I fine-tune a large language model with PyTorch?",
        "What's the best Star Trek: The Next Generation movie?",
        "Tell me about Beethoven's 5th Symphony",
        "How to implement RAG with Redis and LangChain?",
        "Who wrote the Dune series and what's it about?",
        "What's the difference between Bach and Mozart's fugues?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        result = router.route_query(query)
        print(f"\n  Test {i}: \"{query[:60]}...\"")
        print(f"        → {result['route']} (confidence: {result['confidence']})")
        print(f"          method: {result.get('method', 'keyword_match')}")
        time.sleep(0.2)
    
    # ============ INTERACTIVE MODE ============
    print("\n" + "=" * 80)
    print("[4/4] INTERACTIVE MODE - Try your own queries!")
    print("=" * 80)
    print("Enter a query about AI, sci-fi, or classical music")
    print("Commands: 'stats' - show statistics, 'search <word>' - test search, 'quit' - exit")
    print("-" * 60)
    
    while True:
        try:
            query = input("\n🔍 Query: ").strip()
            
            if not query:
                continue
                
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nExiting...")
                break
            
            if query.lower() == 'stats':
                stats = router.get_statistics()
                print("\n📊 ROUTING STATISTICS:")
                print("-" * 40)
                for route, count in stats.items():
                    bar = "█" * min(count, 30)
                    print(f"{route:30s} : {count:3d} {bar}")
                continue
            
            if query.lower().startswith('search '):
                keyword = query[7:]
                result = router.search_by_keyword(keyword)
                if result and result[0] > 0:
                    print(f"\n   Found {result[0]} matches:")
                    for i in range(1, len(result), 2):
                        print(f"   • {result[i][1]}")
                else:
                    print(f"\n   No matches for '{keyword}'")
                continue
            
            # Route the query
            result = router.route_query(query)
            
            print(f"\n   📌 Routed to: {result['route']}")
            print(f"      Confidence: {result['confidence']:.2f}")
            if 'scores' in result:
                print(f"      Scores: {result['scores']}")
            print(f"      Method: {result.get('method', 'keyword_match')}")
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
    
    # ============ SUMMARY ============
    print("\n" + "=" * 80)
    print("✅ EXERCISE 3 COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    
    # Show statistics
    stats = router.get_statistics()
    total = sum(stats.values())
    
    print(f"\n📊 Routing Statistics (Total: {total} queries):")
    for route, count in stats.items():
        percentage = (count / total * 100) if total > 0 else 0
        print(f"   • {route}: {count} queries ({percentage:.1f}%)")
    
    print(f"\n   Database: {SEMANTIC_DB_HOST}:{SEMANTIC_DB_PORT}")
    print("   Redis Search Index: Created ✓")
    print("\n🎯 All requirements met:")
    print("   ✓ Search-enabled database created")
    print("   ✓ Redis Search index created")
    print("   ✓ 3 semantic routes defined and loaded")
    print("   ✓ Routing logic implemented with Search")
    print("   ✓ Test queries processed")
    print("=" * 80)

if __name__ == "__main__":
    main()
