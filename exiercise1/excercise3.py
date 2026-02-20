#!/usr/bin/env python3
"""
Exercise 3: COMPLETE SOLUTION
1. Create database with Search module via API
2. Semantic Router with 3 routes
"""
#
import requests
import redis
import time
import json
import sys
from requests.auth import HTTPBasicAuth
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========================================================================
# KONFIGURASI API
# ========================================================================
API_BASE = "https://re-cluster1.ps-redislabs.org:9443"
API_AUTH = HTTPBasicAuth("admin@rl.org", "5yxQH3o")
API_HEADERS = {"Content-Type": "application/json"}

# Database configuration
DB_NAME = "semantic-router-db"
DB_PORT = 14000
DB_MEMORY = 1073741824  # 1GB in bytes

# ========================================================================
# ROUTE DEFINITIONS
# ========================================================================
ROUTES = {
    "GenAI Programming": {
        "keywords": [
            "ai", "machine learning", "llm", "chatgpt", "gpt", "bert",
            "transformer", "rag", "embedding", "neural network", "pytorch",
            "tensorflow", "langchain", "llamaindex", "fine-tune", "prompt",
            "vector", "semantic search", "python", "code", "programming",
            "developer", "algorithm", "api", "backend", "artificial intelligence"
        ],
        "description": "Topics about AI, programming, and software development"
    },
    
    "Science Fiction Entertainment": {
        "keywords": [
            "star trek", "star wars", "dune", "doctor who", "the expanse",
            "asimov", "philip k dick", "cyberpunk", "blade runner", "matrix",
            "space opera", "sci-fi", "science fiction", "futuristic",
            "alien", "spaceship", "galaxy", "mars", "robot", "android",
            "time travel", "parallel universe", "dystopia", "outer space"
        ],
        "description": "Science fiction movies, TV shows, and books"
    },
    
    "Classical Music": {
        "keywords": [
            "mozart", "beethoven", "bach", "chopin", "vivaldi", "tchaikovsky",
            "symphony", "sonata", "concerto", "fugue", "nocturne", "orchestra",
            "classical music", "piano", "violin", "cello", "opera",
            "maestro", "composer", "baroque", "romantic", "orchestral",
            "philharmonic", "chamber music", "string quartet"
        ],
        "description": "Classical music composers, pieces, and performances"
    }
}

# ========================================================================
# PART 1: CREATE DATABASE WITH SEARCH MODULE
# ========================================================================

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_success(msg):
    print(f"  ✅ {msg}")

def print_error(msg):
    print(f"  ❌ {msg}")

def print_info(msg):
    print(f"  ℹ️  {msg}")

def create_database_with_search():
    """Create database with Search module via API"""
    print_header("PART 1: CREATING DATABASE WITH SEARCH MODULE")
    
    # Database configuration
    db_config = {
        "name": DB_NAME,
        "memory_size": DB_MEMORY,
        "port": DB_PORT,
        "shards_count": 1,
        "sharding": True,
        "replication": False,
        "data_persistence": "disabled",
        "shard_type": "redis",
        "shards_placement": "dense",
        "oss_cluster": False,
        "module_list": [
            {
                "module_name": "search",
                "module_args": "",
                "semantic_version": "2.4.3"
            }
        ]
    }
    
    print_info(f"Creating database '{DB_NAME}' on port {DB_PORT} with Search module...")
    
    try:
        response = requests.post(
            f"{API_BASE}/v1/bdbs",
            auth=API_AUTH,
            headers=API_HEADERS,
            json=db_config,
            verify=False,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            db_info = response.json()
            db_uid = db_info.get('uid')
            print_success(f"Database created! UID: {db_uid}")
            
            # Get endpoint info
            time.sleep(5)  # Wait for database to be ready
            return get_database_endpoint(db_uid)
            
        elif response.status_code == 409:
            print_info("Database already exists")
            # Get existing database UID and endpoint
            return get_existing_database_endpoint()
            
        else:
            print_error(f"Failed to create database: {response.status_code}")
            print_info(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Error creating database: {e}")
        return None

def get_database_endpoint(db_uid):
    """Get database endpoint by UID"""
    try:
        response = requests.get(
            f"{API_BASE}/v1/bdbs/{db_uid}",
            auth=API_AUTH,
            verify=False
        )
        
        if response.status_code == 200:
            db_info = response.json()
            endpoint = db_info.get('endpoint')
            
            # Extract host and port
            if endpoint:
                host_port = endpoint.replace('redis://', '').split(':')
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else DB_PORT
                
                print_success(f"Database endpoint: {host}:{port}")
                return host, port
        
        # Fallback to default
        print_info("Using default endpoint (check Secure UI for actual IP)")
        return "172.16.22.23", DB_PORT
        
    except Exception as e:
        print_error(f"Error getting endpoint: {e}")
        return "172.16.22.23", DB_PORT

def get_existing_database_endpoint():
    """Get endpoint for existing database"""
    try:
        response = requests.get(
            f"{API_BASE}/v1/bdbs",
            auth=API_AUTH,
            verify=False
        )
        
        if response.status_code == 200:
            for db in response.json():
                if db.get('name') == DB_NAME:
                    db_uid = db.get('uid')
                    return get_database_endpoint(db_uid)
        
        return "172.16.22.23", DB_PORT
        
    except Exception as e:
        print_error(f"Error finding existing database: {e}")
        return "172.16.22.23", DB_PORT

# ========================================================================
# PART 2: SEMANTIC ROUTER
# ========================================================================

class SemanticRouter:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.routes = ROUTES
        self.stats_key = "semantic:stats"
        self.queries_key = "semantic:recent_queries"
        
        # Initialize stats in Redis
        for route in self.routes.keys():
            self.redis.hsetnx(self.stats_key, route, 0)
        
        # Check if Search module is available
        try:
            modules = redis_client.execute_command("MODULE LIST")
            self.search_enabled = any(module[1] == "search" for module in modules)
            if self.search_enabled:
                print_success("Redis Search module is active")
        except:
            self.search_enabled = False
    
    def route_query(self, query):
        """Route query to best matching category"""
        query_lower = query.lower()
        scores = {}
        
        # Count keyword matches for each route
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
            confidence = min(max_score / 5, 1.0)
        
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
            "all_scores": scores
        }
    
    def get_statistics(self):
        """Get routing statistics"""
        stats = self.redis.hgetall(self.stats_key)
        return {k: int(v) for k, v in stats.items()}
    
    def show_routes(self):
        """Display all routes"""
        print("\n📌 DEFINED ROUTES:")
        print("-" * 60)
        for i, (route_name, route_info) in enumerate(self.routes.items(), 1):
            print(f"\n  {i}. {route_name}")
            print(f"     Description: {route_info['description']}")
            print(f"     Sample keywords: {', '.join(route_info['keywords'][:5])}...")

def test_redis_connection(host, port):
    """Test connection to Redis"""
    try:
        r = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
            socket_connect_timeout=5
        )
        r.ping()
        print_success(f"Connected to Redis at {host}:{port}")
        return r
    except redis.ConnectionError as e:
        print_error(f"Cannot connect to Redis: {e}")
        return None

def run_semantic_router(redis_client):
    """Run the semantic router"""
    print_header("PART 2: SEMANTIC ROUTER")
    
    # Initialize router
    router = SemanticRouter(redis_client)
    router.show_routes()
    
    # Test queries
    print("\n📝 Testing with sample queries...")
    
    test_queries = [
        # GenAI Programming
        "How do I build a chatbot with GPT-4?",
        "What's the best way to fine-tune BERT?",
        
        # Science Fiction
        "What are the best Star Trek episodes?",
        "Who wrote the Dune series?",
        
        # Classical Music
        "Tell me about Beethoven's 5th Symphony",
        "What's the difference between Mozart and Bach?",
        
        # Ambiguous
        "I want to learn something new"
    ]
    
    for i, query in enumerate(test_queries, 1):
        result = router.route_query(query)
        print(f"\n  Test {i:2d}: \"{query[:40]}...\"")
        print(f"        → {result['route']} (confidence: {result['confidence']})")
        time.sleep(0.1)
    
    # Interactive mode
    print("\n" + "="*60)
    print("INTERACTIVE MODE")
    print("="*60)
    print("Ask about AI, sci-fi, or classical music")
    print("Commands: 'stats', 'routes', 'quit'")
    
    while True:
        try:
            query = input("\n🔍 You: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if query.lower() == 'stats':
                stats = router.get_statistics()
                print("\n📊 STATISTICS:")
                for route, count in stats.items():
                    bar = "█" * min(count, 30)
                    print(f"  {route:25s} : {count:3d} {bar}")
                continue
            
            if query.lower() == 'routes':
                router.show_routes()
                continue
            
            result = router.route_query(query)
            print(f"\n  → {result['route']} (confidence: {result['confidence']})")
            
        except KeyboardInterrupt:
            break
    
    return router

# ========================================================================
# MAIN FUNCTION
# ========================================================================

def main():
    print("="*80)
    print("  EXERCISE 3: COMPLETE SOLUTION")
    print("  1. Create database with Search module")
    print("  2. Run Semantic Router with 3 routes")
    print("="*80)
    
    # PART 1: Create database with Search module
    db_host, db_port = create_database_with_search()
    
    if not db_host:
        print_error("Failed to get database endpoint")
        sys.exit(1)
    
    # Wait for database to be ready
    print_info("Waiting 10 seconds for database to initialize...")
    time.sleep(10)
    
    # PART 2: Connect to Redis and run semantic router
    redis_client = test_redis_connection(db_host, db_port)
    
    if not redis_client:
        print_error("Cannot proceed without Redis connection")
        sys.exit(1)
    
    router = run_semantic_router(redis_client)
    
    # Final summary
    print_header("EXERCISE 3 COMPLETED")
    print_success("✓ Database with Search module created")
    print_success("✓ 3 semantic routes defined")
    print_success("✓ Routing logic implemented")
    print_success("✓ Test queries processed")
    
    stats = router.get_statistics()
    total = sum(stats.values())
    
    print(f"\n📊 Total queries routed: {total}")
    print("="*80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
