#!/usr/bin/env python3
"""
Exercise 2: Berdasarkan UI Redis Enterprise
"""

import requests
from requests.auth import HTTPBasicAuth
import urllib3
import json

urllib3.disable_warnings()

API_BASE = "https://re-cluster1.ps-redislabs.org:9443"
AUTH = HTTPBasicAuth("admin@rl.org", "5yxQH3o")
HEADERS = {"Content-Type": "application/json"}

def print_header(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def create_role(role_name):
    """Create role"""
    print(f"\n📝 Creating role: {role_name}")
    
    role_data = {
        "name": role_name,
        "management": "regular"
    }
    
    resp = requests.post(
        f"{API_BASE}/v1/roles",
        auth=AUTH,
        headers=HEADERS,
        json=role_data,
        verify=False
    )
    
    if resp.status_code in [200, 201]:
        print(f"  ✅ Role '{role_name}' created")
        return True
    elif resp.status_code == 409:
        print(f"  ℹ️  Role '{role_name}' already exists")
        return True
    else:
        print(f"  ❌ Failed: {resp.status_code}")
        return False

def list_roles():
    """List all roles"""
    resp = requests.get(f"{API_BASE}/v1/roles", auth=AUTH, verify=False)
    
    if resp.status_code == 200:
        roles = resp.json()
        print(f"\n📋 Available roles ({len(roles)}):")
        for role in roles:
            print(f"  • {role.get('name')}")
        return roles
    return []

def create_database():
    """Create database"""
    print_header("CREATING DATABASE")
    
    db_config = {
        "name": "test-db-api",
        "memory_size": 1073741824,
        "port": 12002,
        "shards_count": 1
    }
    
    resp = requests.post(
        f"{API_BASE}/v1/bdbs",
        auth=AUTH,
        headers=HEADERS,
        json=db_config,
        verify=False
    )
    
    if resp.status_code in [200, 201]:
        db_uid = resp.json().get('uid')
        print(f"  ✅ Database created (UID: {db_uid})")
        return db_uid
    elif resp.status_code == 409:
        print(f"  ℹ️  Database already exists")
        # Get existing UID
        list_resp = requests.get(f"{API_BASE}/v1/bdbs", auth=AUTH, verify=False)
        for db in list_resp.json():
            if db.get('name') == "test-db-api":
                return db.get('uid')
    else:
        print(f"  ❌ Failed: {resp.status_code}")
        return None

def create_user(email, name, role):
    """Create user"""
    print(f"\n👤 Creating: {email} - Role: {role}")
    
    user_data = {
        "email": email,
        "name": name,
        "role": role,
        "password": "TempPass123!"
    }
    
    resp = requests.post(
        f"{API_BASE}/v1/users",
        auth=AUTH,
        headers=HEADERS,
        json=user_data,
        verify=False
    )
    
    if resp.status_code in [200, 201]:
        print(f"  ✅ User created")
        return True
    elif resp.status_code == 409:
        print(f"  ℹ️  User already exists")
        return True
    else:
        print(f"  ❌ Failed: {resp.status_code}")
        print(f"     {resp.text}")
        return False

def list_users():
    """List users"""
    print_header("LISTING ALL USERS")
    
    resp = requests.get(f"{API_BASE}/v1/users", auth=AUTH, verify=False)
    
    if resp.status_code == 200:
        users = resp.json()
        print(f"\n{'Name':<25} {'Role':<20} {'Email':<30}")
        print("-" * 75)
        
        for user in sorted(users, key=lambda x: x.get('email', '')):
            name = user.get('name', 'N/A')[:24]
            role = user.get('role', 'N/A')[:19]
            email = user.get('email', 'N/A')[:29]
            print(f"{name:<25} {role:<20} {email:<30}")
        
        print("-" * 75)
        print(f"Total: {len(users)} users")
        return users
    else:
        print(f"  ❌ Failed: {resp.status_code}")
        return []

def delete_database(db_uid):
    """Delete database"""
    print_header("DELETING DATABASE")
    
    if not db_uid:
        return
    
    resp = requests.delete(
        f"{API_BASE}/v1/bdbs/{db_uid}",
        auth=AUTH,
        verify=False
    )
    
    if resp.status_code == 200:
        print(f"  ✅ Database deleted")
    else:
        print(f"  ❌ Failed: {resp.status_code}")

def main():
    print("="*80)
    print("  EXERCISE 2: BERDASARKAN UI REDIS")
    print("="*80)
    
    # Test connection
    try:
        requests.get(f"{API_BASE}/v1/users", auth=AUTH, verify=False, timeout=5)
        print("\n✅ Connected to API")
    except Exception as e:
        print(f"\n❌ Cannot connect: {e}")
        return
    
    # STEP 0: Lihat roles yang ada
    print_header("CURRENT ROLES")
    list_roles()
    
    # STEP 1: Create roles yang diperlukan
    print_header("CREATING REQUIRED ROLES")
    create_role("db_viewer")
    create_role("db_member")
    
    # STEP 2: Lihat roles setelah dibuat
    print_header("UPDATED ROLES")
    list_roles()
    
    # STEP 3: Create database
    db_uid = create_database()
    
    # STEP 4: Create users sesuai soal
    print_header("CREATING USERS")
    
    users = [
        ("john.doe@example.com", "John Doe", "db_viewer"),
        ("mike.smith@example.com", "Mike Smith", "db_member"),
        ("cary.johnson@example.com", "Cary Johnson", "admin")
    ]
    
    for email, name, role in users:
        create_user(email, name, role)
    
    # STEP 5: List users
    list_users()
    
    # STEP 6: Delete database
    delete_database(db_uid)
    
    print_header("EXERCISE 2 COMPLETED")
    print("✅ Database created and deleted")
    print("✅ Users created:")
    for email, name, role in users:
        print(f"   • {email} - {role}")

if __name__ == "__main__":
    main()
