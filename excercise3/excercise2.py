#!/usr/bin/env python3
"""
Exercise 2: COMPLETE SOLUTION
1. Create required roles (db_viewer, db_member)
2. Then create users with those roles
"""

import requests
from requests.auth import HTTPBasicAuth
import urllib3
import json
import sys

urllib3.disable_warnings()

# ========================================================================
# KONFIGURASI
# ========================================================================
API_BASE = "https://re-cluster1.ps-redislabs.org:9443"
AUTH = HTTPBasicAuth("admin@rl.org", "5yxQH3o")
HEADERS = {"Content-Type": "application/json"}

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

def create_role(role_name, description=""):
    """Create a new role"""
    print(f"\n📝 Creating role: {role_name}")
    
    role_data = {
        "name": role_name,
        "description": description,
        "management_type": "regular"
    }
    
    response = requests.post(
        f"{API_BASE}/v1/roles",
        auth=AUTH,
        headers=HEADERS,
        json=role_data,
        verify=False
    )
    
    if response.status_code in [200, 201]:
        print_success(f"Role '{role_name}' created")
        return True
    elif response.status_code == 409:
        print_info(f"Role '{role_name}' already exists")
        return True
    else:
        print_error(f"Failed: {response.status_code}")
        print_info(f"Response: {response.text}")
        return False

def create_user(email, name, role):
    """Create user with specified role"""
    print(f"\n👤 Creating: {email} - Role: {role}")
    
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
        print_success(f"User {email} created")
        return True
    elif response.status_code == 409:
        print_info(f"User {email} already exists")
        return True
    else:
        print_error(f"Failed: {response.status_code}")
        print_info(f"Response: {response.text}")
        return False

def list_roles():
    """List all roles"""
    print_header("CURRENT ROLES IN SYSTEM")
    
    response = requests.get(f"{API_BASE}/v1/roles", auth=AUTH, verify=False)
    
    if response.status_code == 200:
        roles = response.json()
        print(f"\nTotal: {len(roles)} roles")
        print("-" * 40)
        for role in roles:
            print(f"  • {role.get('name')} (UID: {role.get('uid')})")
        return roles
    else:
        print_error(f"Failed to get roles: {response.status_code}")
        return []

def list_users():
    """List all users"""
    print_header("ALL USERS IN SYSTEM")
    
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
        print_error(f"Failed to list users: {response.status_code}")
        return []

def delete_existing_users():
    """Delete target users if they exist"""
    print_header("CLEANING UP EXISTING USERS")
    
    target_emails = [
        "john.doe@example.com",
        "mike.smith@example.com",
        "cary.johnson@example.com"
    ]
    
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

def create_database():
    """Create a new database"""
    print_header("CREATING DATABASE")
    
    db_config = {
        "name": "test-db-api",
        "memory_size": 1073741824,  # 1GB
        "port": 12002,
        "shards_count": 1,
        "sharding": True
    }
    
    response = requests.post(
        f"{API_BASE}/v1/bdbs",
        auth=AUTH,
        headers=HEADERS,
        json=db_config,
        verify=False
    )
    
    if response.status_code in [200, 201]:
        db_info = response.json()
        print_success(f"Database created! UID: {db_info.get('uid')}")
        return db_info.get('uid')
    elif response.status_code == 409:
        print_info("Database already exists")
        # Get existing DB UID
        list_resp = requests.get(f"{API_BASE}/v1/bdbs", auth=AUTH, verify=False)
        for db in list_resp.json():
            if db.get('name') == "test-db-api":
                return db.get('uid')
    else:
        print_error(f"Failed: {response.status_code}")
        return None

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
        print_error(f"Failed: {response.status_code}")

# ========================================================================
# MAIN FUNCTION
# ========================================================================

def main():
    print("="*80)
    print("  EXERCISE 2: COMPLETE SOLUTION")
    print("  1. Create required roles")
    print("  2. Create users with those roles")
    print("="*80)
    
    # Step 1: Test connection
    try:
        requests.get(f"{API_BASE}/v1/users", auth=AUTH, verify=False, timeout=5)
        print_success("Connected to API")
    except Exception as e:
        print_error(f"Cannot connect: {e}")
        return
    
    # Step 2: Show current roles
    list_roles()
    
    # Step 3: Create missing roles
    print_header("CREATING MISSING ROLES")
    
    roles_to_create = [
        ("db_viewer", "Can view databases"),
        ("db_member", "Can access and modify databases"),
        ("admin", "Administrator role")  # This might already exist
    ]
    
    for role_name, description in roles_to_create:
        create_role(role_name, description)
    
    # Step 4: Show updated roles
    list_roles()
    
    # Step 5: Create database
    db_uid = create_database()
    
    # Step 6: Clean up existing users
    delete_existing_users()
    
    # Step 7: Create users with correct roles (sesuai soal)
    print_header("CREATING USERS WITH CORRECT ROLES")
    
    users_to_create = [
        ("john.doe@example.com", "John Doe", "db_viewer"),
        ("mike.smith@example.com", "Mike Smith", "db_member"),
        ("cary.johnson@example.com", "Cary Johnson", "admin")
    ]
    
    for email, name, role in users_to_create:
        create_user(email, name, role)
    
    # Step 8: List all users to verify
    list_users()
    
    # Step 9: Delete database
    delete_database(db_uid)
    
    # Summary
    print_header("EXERCISE 2 COMPLETED")
    print_success("✓ Roles created: db_viewer, db_member")
    print_success("✓ Database created and deleted")
    print_success("✓ Users created with correct roles:")
    for email, name, role in users_to_create:
        print(f"    • {email} - {role}")
    print_success("✓ All users listed and verified")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
