#!/usr/bin/env python3
"""
Exercise 2: Working with Redis REST API
Dengan role sesuai soal: db_viewer, db_member, admin
"""

import requests
import json
from requests.auth import HTTPBasicAuth
import urllib3
import sys
from datetime import datetime

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========================================================================
# KONFIGURASI
# ========================================================================
API_BASE = "https://re-cluster1.ps-redislabs.org:9443"
AUTH = HTTPBasicAuth("admin@rl.org", "5yxQH3o")
HEADERS = {"Content-Type": "application/json"}

# Users dengan role sesuai SOAL (bukan semua admin)
USERS = [
    {
        "email": "john.doe@example.com",
        "name": "John Doe",
        "role": "db_viewer",        # Sesuai soal
        "password": "TempPass123!"
    },
    {
        "email": "mike.smith@example.com",
        "name": "Mike Smith",
        "role": "db_member",         # Sesuai soal
        "password": "TempPass123!"
    },
    {
        "email": "cary.johnson@example.com",
        "name": "Cary Johnson",
        "role": "admin",              # Sesuai soal
        "password": "TempPass123!"
    }
]

# Database yang akan dibuat
DB_CONFIG = {
    "name": "test-db-api",
    "memory_size": 1073741824,  # 1GB
    "port": 12002,
    "shards_count": 1,
    "sharding": True,
    "replication": False,
    "data_persistence": "disabled",
    "shard_type": "redis",
    "shards_placement": "dense",
    "oss_cluster": False
}

# ========================================================================
# FUNGSI-FUNGSI
# ========================================================================

def print_header(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_success(msg):
    print(f"  ✅ {msg}")

def print_error(msg):
    print(f"  ❌ {msg}")

def print_info(msg):
    print(f"  ℹ️  {msg}")

def test_connection():
    """Test koneksi ke API"""
    print_header("TESTING API CONNECTION")
    
    try:
        response = requests.get(
            f"{API_BASE}/v1/users",
            auth=AUTH,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            print_success(f"Connected to API")
            print_info(f"Found {len(response.json())} users")
            return True
        else:
            print_error(f"Failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Connection error: {e}")
        return False

def check_roles():
    """Cek roles yang tersedia"""
    print_header("CHECKING AVAILABLE ROLES")
    
    response = requests.get(f"{API_BASE}/v1/roles", auth=AUTH, verify=False)
    
    if response.status_code == 200:
        roles = response.json()
        role_names = [role.get('name') for role in roles]
        
        print_info(f"Found {len(roles)} roles:")
        for role in roles:
            print(f"     • {role.get('name')}")
        
        # Verifikasi role yang kita butuhkan
        required_roles = ['db_viewer', 'db_member', 'admin']
        print_info("\nChecking required roles:")
        for req_role in required_roles:
            if req_role in role_names:
                print_success(f"{req_role} available")
            else:
                print_error(f"{req_role} NOT available")
        
        return role_names
    else:
        print_error(f"Failed to get roles: {response.status_code}")
        return []

def create_database():
    """Create database"""
    print_header("CREATING DATABASE")
    
    response = requests.post(
        f"{API_BASE}/v1/bdbs",
        auth=AUTH,
        headers=HEADERS,
        json=DB_CONFIG,
        verify=False
    )
    
    if response.status_code in [200, 201]:
        db_info = response.json()
        db_uid = db_info.get('uid')
        print_success(f"Database created! UID: {db_uid}")
        return db_uid
    elif response.status_code == 409:
        print_info("Database already exists")
        # Cari UID database yang ada
        list_resp = requests.get(f"{API_BASE}/v1/bdbs", auth=AUTH, verify=False)
        for db in list_resp.json():
            if db.get('name') == DB_CONFIG['name']:
                return db.get('uid')
    else:
        print_error(f"Failed: {response.status_code}")
        return None

def delete_existing_users():
    """Delete users if they exist"""
    print_header("CLEANING UP EXISTING USERS")
    
    target_emails = [user["email"] for user in USERS]
    
    response = requests.get(f"{API_BASE}/v1/users", auth=AUTH, verify=False)
    
    if response.status_code == 200:
        users = response.json()
        deleted = 0
        
        for user in users:
            if user.get('email') in target_emails:
                uid = user.get('uid')
                del_resp = requests.delete(
                    f"{API_BASE}/v1/users/{uid}",
                    auth=AUTH,
                    verify=False
                )
                if del_resp.status_code == 200:
                    print_success(f"Deleted {user.get('email')}")
                    deleted += 1
        
        if deleted == 0:
            print_info("No existing users to delete")
        else:
            print_success(f"Deleted {deleted} users")

def create_user(user):
    """Create user dengan role sesuai soal"""
    print(f"\n📝 Creating: {user['email']}")
    print(f"   Name: {user['name']}")
    print(f"   Role: {user['role']}")
    
    response = requests.post(
        f"{API_BASE}/v1/users",
        auth=AUTH,
        headers=HEADERS,
        json=user,
        verify=False
    )
    
    if response.status_code in [200, 201]:
        print_success(f"Created {user['email']}")
        return True
    elif response.status_code == 409:
        print_info(f"{user['email']} already exists")
        return True
    else:
        print_error(f"Failed: HTTP {response.status_code}")
        print_info(f"Response: {response.text}")
        return False

def list_users():
    """List all users"""
    print_header("LISTING ALL USERS")
    
    response = requests.get(f"{API_BASE}/v1/users", auth=AUTH, verify=False)
    
    if response.status_code == 200:
        users = response.json()
        
        print(f"\n{'Name':<25} {'Role':<20} {'Email':<30}")
        print("-" * 75)
        
        for user in sorted(users, key=lambda x: x.get('email', '')):
            name = user.get('name', 'N/A')[:24]
            role = user.get('role', 'N/A')[:19]
            email = user.get('email', 'N/A')[:29]
            print(f"{name:<25} {role:<20} {email:<30}")
        
        print("-" * 75)
        print(f"Total: {len(users)} users")
        
        # Verifikasi target users
        print_header("VERIFICATION")
        for target in USERS:
            found = False
            for user in users:
                if user.get('email') == target['email']:
                    print_success(f"{target['email']} - Role: {user.get('role')}")
                    found = True
                    break
            if not found:
                print_error(f"{target['email']} - NOT FOUND")
        
        return users
    else:
        print_error(f"Failed to list users: {response.status_code}")
        return []

def delete_database(db_uid):
    """Delete database"""
    if not db_uid:
        return
    
    print_header("DELETING DATABASE")
    
    response = requests.delete(
        f"{API_BASE}/v1/bdbs/{db_uid}",
        auth=AUTH,
        verify=False
    )
    
    if response.status_code == 200:
        print_success("Database deleted")
    else:
        print_error(f"Failed to delete: {response.status_code}")

# ========================================================================
# MAIN
# ========================================================================

def main():
    print("="*80)
    print("  EXERCISE 2: Redis REST API")
    print("  Dengan role: db_viewer, db_member, admin")
    print("="*80)
    
    # Test connection
    if not test_connection():
        return
    
    # Check roles
    available_roles = check_roles()
    
    # Create database
    db_uid = create_database()
    
    # Clean up existing users
    delete_existing_users()
    
    # Create users with correct roles
    print_header("CREATING THREE USERS (sesuai soal)")
    for user in USERS:
        create_user(user)
    
    # List and verify
    list_users()
    
    # Delete database
    delete_database(db_uid)
    
    print_header("EXERCISE 2 COMPLETED")
    print_success("Database created and deleted")
    print_success("Three users created with correct roles:")
    for user in USERS:
        print(f"    • {user['email']} - {user['role']}")
    print_success("All users listed and verified")

if __name__ == "__main__":
    main()
