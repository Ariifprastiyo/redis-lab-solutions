#!/usr/bin/env python3
"""
Exercise 1: FIX - Insert 100 keys with correct format 'key:1' to 'key:100'
"""

import redis
import time

# ========================================================================
# KONFIGURASI
# ========================================================================
SOURCE_HOST = '172.16.22.21'
SOURCE_PORT = 12000
REPLICA_HOST = '172.16.22.22'
REPLICA_PORT = 12001
# ========================================================================

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_success(msg):
    print(f"  ✅ {msg}")

def print_error(msg):
    print(f"  ❌ {msg}")

def print_info(msg):
    print(f"  ℹ️  {msg}")

def main():
    print_header("EXERCISE 1 FIX - Insert 100 keys with correct format")
    
    # Connect to databases
    try:
        source = redis.Redis(
            host=SOURCE_HOST,
            port=SOURCE_PORT,
            decode_responses=True,
            socket_connect_timeout=5
        )
        source.ping()
        print_success(f"Connected to source-db at {SOURCE_HOST}:{SOURCE_PORT}")
        
        replica = redis.Redis(
            host=REPLICA_HOST,
            port=REPLICA_PORT,
            decode_responses=True,
            socket_connect_timeout=5
        )
        replica.ping()
        print_success(f"Connected to replica-db at {REPLICA_HOST}:{REPLICA_PORT}")
        
    except redis.ConnectionError as e:
        print_error(f"Connection failed: {e}")
        return
    
    # Step 1: Check current keys
    print_header("STEP 1: Check existing keys")
    
    # Check wrong format keys (keys:)
    wrong_keys = source.keys("keys:*")
    print_info(f"Found {len(wrong_keys)} keys with wrong format 'keys:*'")
    
    if wrong_keys:
        print_info("Deleting wrong format keys...")
        for key in wrong_keys:
            source.delete(key)
        print_success("Wrong format keys deleted")
    
    # Check correct format keys (key:)
    correct_keys = source.keys("key:*")
    print_info(f"Found {len(correct_keys)} keys with correct format 'key:*'")
    
    # Step 2: Delete existing correct keys if any
    if correct_keys:
        print_info("Deleting existing correct format keys to reinsert...")
        for key in correct_keys:
            source.delete(key)
        print_success("Existing correct keys deleted")
    
    # Step 3: Insert 100 keys with correct format
    print_header("STEP 2: Insert 100 keys with format 'key:1' to 'key:100'")
    
    inserted = 0
    for i in range(1, 101):
        key = f"key:{i}"
        source.set(key, i)
        inserted += 1
        if i % 20 == 0:
            print_info(f"Progress: {i}/100 inserted")
    
    print_success(f"Inserted {inserted} keys with correct format")
    
    # Step 4: Wait for replication
    print_header("STEP 3: Wait for replication")
    print_info("Waiting 5 seconds...")
    time.sleep(5)
    print_success("Replication wait complete")
    
    # Step 5: Verify in replica
    print_header("STEP 4: Verify keys in replica-db")
    
    replica_keys = replica.keys("key:*")
    print_info(f"Found {len(replica_keys)} keys in replica with format 'key:*'")
    
    if len(replica_keys) == 100:
        print_success("All 100 keys replicated successfully!")
    else:
        print_error(f"Expected 100 keys, found {len(replica_keys)}")
    
    # Show sample keys
    print_header("STEP 5: Sample verification")
    
    print_info("First 10 keys (1-10):")
    for i in range(1, 11):
        val = replica.get(f"key:{i}")
        print(f"     key:{i} = {val}")
    
    print_info("\nLast 10 keys (91-100):")
    for i in range(91, 101):
        val = replica.get(f"key:{i}")
        print(f"     key:{i} = {val}")
    
    # Read in reverse order (for documentation)
    print_header("STEP 6: Reading in reverse order (100 → 1)")
    
    print_info("First 10 reverse (100-91):")
    for i in range(100, 90, -1):
        val = replica.get(f"key:{i}")
        print(f"     key:{i} = {val}")
    
    print_info("\nLast 10 reverse (10-1):")
    for i in range(10, 0, -1):
        val = replica.get(f"key:{i}")
        print(f"     key:{i} = {val}")
    
    # Final statistics
    print_header("FINAL STATISTICS")
    
    source_count = source.dbsize()
    replica_count = replica.dbsize()
    
    print_info(f"source-db total keys: {source_count}")
    print_info(f"replica-db total keys: {replica_count}")
    
    correct_count = len(replica.keys("key:*"))
    
    if correct_count == 100 and source_count >= 5100 and replica_count >= 5100:
        print_header("✅ EXERCISE 1 FIXED SUCCESSFULLY!")
        print_success("✓ 100 keys with format 'key:1-100' are present")
        print_success("✓ Keys can be read in reverse from replica")
        print_success("✓ Total keys in source-db: " + str(source_count))
        print_success("✓ Total keys in replica-db: " + str(replica_count))
        print("\n" + "="*70)
        print("  NOW READY FOR GRADING! 🎉")
        print("="*70)
    else:
        print_header("❌ EXERCISE 1 STILL HAS ISSUES")
        if correct_count != 100:
            print_error(f"Expected 100 keys with format 'key:*', found {correct_count}")
        if source_count < 5100:
            print_error(f"source-db has {source_count} keys, need at least 5100")
        if replica_count < 5100:
            print_error(f"replica-db has {replica_count} keys, need at least 5100")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
