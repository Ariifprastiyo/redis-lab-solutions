#!/usr/bin/env python3
"""
Exercise 1: FIXED - Insert 5100 keys and verify replication
"""

import redis
import time

# ========================================================================
# CONFIGURATION - Gunakan IP yang sama dengan sebelumnya
# ========================================================================
SOURCE_HOST = '172.16.22.21'  # source-db IP
SOURCE_PORT = 12000

REPLICA_HOST = '172.16.22.22'  # replica-db IP
REPLICA_PORT = 12001
# ========================================================================

def main():
    print("="*80)
    print("EXERCISE 1: INSERT 5100 KEYS into source-db")
    print("="*80)
    
    # Connect ke database
    source = redis.Redis(
        host=SOURCE_HOST,
        port=SOURCE_PORT,
        decode_responses=True,
        socket_timeout=10
    )
    
    replica = redis.Redis(
        host=REPLICA_HOST,
        port=REPLICA_PORT,
        decode_responses=True,
        socket_timeout=10
    )
    
    # Test koneksi
    source.ping()
    replica.ping()
    print("✓ Connected to both databases\n")
    
    # ============ CLEAN EXISTING DATA ============
    print("Cleaning existing data...")
    keys_to_delete = []
    for key in source.scan_iter("*"):
        keys_to_delete.append(key)
        if len(keys_to_delete) >= 1000:
            source.delete(*keys_to_delete)
            keys_to_delete = []
    if keys_to_delete:
        source.delete(*keys_to_delete)
    print("✓ Existing data cleared\n")
    
    # ============ INSERT 5100 KEYS ============
    print("Inserting 5100 keys into source-db...")
    print("-" * 40)
    
    start_time = time.time()
    
    # Insert keys 1-100 (format: test:1, test:2, etc)
    print("Phase 1: Inserting test keys (1-100)...")
    for i in range(1, 101):
        source.set(f"test:{i}", f"value-{i}")
        if i % 25 == 0:
            print(f"  Progress: {i}/100 test keys")
    
    # Insert keys 101-5100 (format: data:101, data:102, etc)
    print("\nPhase 2: Inserting data keys (101-5100)...")
    batch_size = 500
    for i in range(101, 5101):
        source.set(f"data:{i}", f"value-{i}")
        if i % 1000 == 0:
            print(f"  Progress: {i}/5100 total keys")
    
    elapsed = time.time() - start_time
    print(f"\n✓ Inserted 5100 keys in {elapsed:.2f} seconds")
    
    # ============ VERIFY SOURCE KEY COUNT ============
    source_count = len(source.keys('*'))
    print(f"\n📊 Source-db key count: {source_count}")
    
    if source_count >= 5100:
        print("✓ PASSED: source-db has 5100+ keys")
    else:
        print(f"❌ FAILED: Only {source_count} keys found")
    
    # ============ WAIT FOR REPLICATION ============
    print("\n⏳ Waiting 10 seconds for replication...")
    time.sleep(10)
    
    # ============ VERIFY REPLICA KEY COUNT ============
    replica_count = len(replica.keys('*'))
    print(f"📊 Replica-db key count: {replica_count}")
    
    if replica_count >= 5100:
        print("✓ PASSED: replica-db has 5100+ keys")
    else:
        print(f"❌ FAILED: Only {replica_count} keys found")
    
    # ============ READ 100 KEYS IN REVERSE ============
    print("\n" + "="*80)
    print("READING test:1 - test:100 IN REVERSE ORDER")
    print("="*80)
    
    print("\nFirst 10 values (100 → 91):")
    print("-" * 40)
    for i in range(100, 90, -1):
        val = replica.get(f"test:{i}")
        print(f"  test:{i} = {val}")
    
    print("\n... (values 90-11 omitted) ...\n")
    
    print("Last 10 values (10 → 1):")
    print("-" * 40)
    for i in range(10, 0, -1):
        val = replica.get(f"test:{i}")
        print(f"  test:{i} = {val}")
    
    # ============ FINAL VERIFICATION ============
    print("\n" + "="*80)
    print("FINAL VERIFICATION")
    print("="*80)
    
    # Check replication lag
    info = replica.info('replication')
    lag = info.get('master_repl_offset', 0)
    print(f"Replication offset: {lag}")
    
    # Summary
    print("\n📋 SUMMARY:")
    print(f"  • source-db keys: {source_count}")
    print(f"  • replica-db keys: {replica_count}")
    print(f"  • Replicated: {'✓ YES' if replica_count >= 5100 else '✗ NO'}")
    
    if replica_count >= 5100:
        print("\n✅ EXERCISE 1 COMPLETED SUCCESSFULLY!")
        print("   All requirements met:")
        print("   • 5100+ keys in source-db ✓")
        print("   • 5100+ keys in replica-db ✓")
        print("   • Values 1-100 inserted and read in reverse ✓")
    else:
        print("\n❌ EXERCISE 1 NOT COMPLETE")
        print("   Please check replication status")
    
    print("="*80)

if __name__ == "__main__":
    main()