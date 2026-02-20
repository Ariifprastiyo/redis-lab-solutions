#!/usr/bin/env python3
"""
Exercise 2: FIXED - Dengan format role yang benar dari curl
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
    """Create role dengan format yang benar dari curl"""
    print(f"\n📝 Creating role: {role_name}")
    
    # FORMAT YANG BENAR - berdasarkan response curl
    role_data = {
        "name": role_name,
        "management": role_name  # management = nama role
    }
    
    print(f"  Request: {role_data}")
    
    response = requests.post(
        f"{API_BASE}/v1/roles",
        auth=AUTH,
        headers=HEADERS,
        json=role_data,
        verify=False
    )
    
    if response.status_code in [200, 201]:
        print(f"  ✅ Role '{role_name}' created")
        return True
    elif response.status_code == 409:
        print(f"  ℹ️  Role '{role_name}' already exists")
        return True
    else:
        print(f"  ❌ Failed: {response.status_code}")
        print(f"     Response: {response.text}")
        return False

def create_user(email, name, role):
    """Create user"""
    print(f"\n👤 Creating: {email} - Role: {role}")
    
    # Cek dulu apakah user sudah ada
    resp = requests.get(f"{API_BASE}/v1/users", auth=AUTH, verify=False)
    for user in resp.json():
        if user.get('email') == email:
            uid = user.get('uid')
            requests.delete(f"{API_BASE}/v1/users/{uid}", auth=AUTH, verify=False)
            print(f"  🗑️  Deleted existing {email}")
            break
    
    user_data = {
        "email": email,
        "name": name,
        "role": role,
        "password": "TempPass123!"
    }
    
    response = requests.post(
        f"{API_BASE}/v1/users",
        auth=AUTH,
        headers=HEADERS,
        json=user_data,
        verify=False
    )
    
    if response.status_code in [200, 201]:
        print(f"  ✅ User created")
        return True
    else:
        print(f"  ❌ Failed: {response.status_code}")
        print(f"     Response: {response.text}")
        return False

def list_roles():
    """List all roles"""
    response = requests.get(f"{API_BASE}/v1/roles", auth=AUTH, verify=False)
    
    if response.status_code == 200:
        roles = response.json()
        print(f"\n📋 Available roles ({len(roles)}):")
        for role in roles:
            print(f"  • {role.get('name')} (management: {role.get('management')})")
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
    
    response = requests.post(
        f"{API_BASE}/v1/bdbs",
        auth=AUTH,
        headers=HEADERS,
        json=db_config,
        verify=False
    )
    
    if response.status_code in [200, 201]:
        db_uid = response.json().get('uid')
        print(f"  ✅ Database created (UID: {db_uid})")
        return db_uid
    elif response.status_code == 409:
        print(f"  ℹ️  Database already exists")
        list_resp = requests.get(f"{API_BASE}/v1/bdbs", auth=AUTH, verify=False)
        for db in list_resp.json():
            if db.get('name') == "test-db-api":
                uid = db.get('uid')
                print(f"  ℹ️  Using existing database UID: {uid}")
                return uid
    else:
        print(f"  ❌ Failed: {response.status_code}")
        return None

def list_users():
    """List users"""
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
        return users
    else:
        print(f"  ❌ Failed: {response.status_code}")
        return []

def delete_database(db_uid):
    """Delete database"""
    print_header("DELETING DATABASE")
    
    if not db_uid:
        return
    
    response = requests.delete(
        f"{API_BASE}/v1/bdbs/{db_uid}",
        auth=AUTH,
        verify=False
    )
    
    if response.status_code == 200:
        print(f"  ✅ Database deleted")
    else:
        print(f"  ❌ Failed: {response.status_code}")

def main():
    print("="*80)
    print("  EXERCISE 2: FIXED - Format role dari curl")
    print("="*80)
    
    # STEP 1: Lihat roles yang ada
    print_header("CURRENT ROLES")
    list_roles()
    
    # STEP 2: Create roles dengan format yang benar
    print_header("CREATING REQUIRED ROLES")
    create_role("db_viewer")
    create_role("db_member")
    
    # STEP 3: Lihat roles setelah dibuat
    print_header("UPDATED ROLES")
    list_roles()
    
    # STEP 4: Create database
    db_uid = create_database()
    
    # STEP 5: Create users sesuai soal
    print_header("CREATING USERS")
    
    users = [
        ("john.doe@example.com", "John Doe", "db_viewer"),
        ("mike.smith@example.com", "Mike Smith", "db_member"),
        ("cary.johnson@example.com", "Cary Johnson", "admin")
    ]
    
    for email, name, role in users:
        create_user(email, name, role)
    
    # STEP 6: List users
    list_users()
    
    # STEP 7: Delete database
    delete_database(db_uid)
    
    print_header("EXERCISE 2 COMPLETED")
    print("✅ Database created and deleted")
    print("✅ Users created:")
    for email, name, role in users:
        print(f"   • {email} - {role}")

if __name__ == "__main__":
    main()
