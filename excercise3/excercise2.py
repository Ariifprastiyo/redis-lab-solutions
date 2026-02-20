#!/usr/bin/env python3
"""
Exercise 2: FIXED VERSION - Dengan debug role
"""

import requests
from requests.auth import HTTPBasicAuth
import urllib3
urllib3.disable_warnings()

API_BASE = "https://re-cluster1.ps-redislabs.org:9443"
AUTH = HTTPBasicAuth("admin@rl.org", "5yxQH3o")
HEADERS = {"Content-Type": "application/json"}

def check_roles():
    """Cek available roles"""
    print("\n📋 Checking available roles...")
    url = f"{API_BASE}/v1/roles"
    response = requests.get(url, auth=AUTH, verify=False)
    
    if response.status_code == 200:
        roles = response.json()
        print(f"Found {len(roles)} roles:")
        for role in roles:
            print(f"  - {role.get('name')} (UID: {role.get('uid')})")
        return [role.get('name') for role in roles]
    else:
        print(f"❌ Failed to get roles: {response.status_code}")
        return []

def delete_existing_users():
    """Delete users if they already exist"""
    print("\n🗑️  Checking for existing users...")
    url = f"{API_BASE}/v1/users"
    response = requests.get(url, auth=AUTH, verify=False)
    
    if response.status_code == 200:
        users = response.json()
        target_emails = [
            "john.doe@example.com",
            "mike.smith@example.com", 
            "cary.johnson@example.com"
        ]
        
        for user in users:
            if user.get('email') in target_emails:
                uid = user.get('uid')
                del_resp = requests.delete(f"{API_BASE}/v1/users/{uid}", 
                                          auth=AUTH, verify=False)
                print(f"  Deleted: {user.get('email')} - {del_resp.status_code}")

def create_user(email, name, role_name):
    """Create a user with specified role"""
    print(f"\n👤 Creating: {email} - Role: {role_name}")
    
    user_data = {
        "email": email,
        "name": name,
        "role": role_name,
        "password": "TempPass123!"
    }
    
    response = requests.post(f"{API_BASE}/v1/users", 
                            auth=AUTH, 
                            headers=HEADERS,
                            json=user_data, 
                            verify=False)
    
    if response.status_code in [200, 201]:
        print(f"  ✅ SUCCESS")
        return True
    else:
        print(f"  ❌ FAILED: {response.status_code}")
        print(f"     Response: {response.text}")
        return False

def list_users():
    """List all users"""
    response = requests.get(f"{API_BASE}/v1/users", auth=AUTH, verify=False)
    
    if response.status_code == 200:
        users = response.json()
        print("\n" + "="*70)
        print("ALL USERS:")
        print("="*70)
        print(f"{'Name':<25} {'Role':<20} {'Email':<30}")
        print("-"*75)
        
        for user in users:
            name = user.get('name', 'N/A')[:24]
            role = user.get('role', 'N/A')[:19]
            email = user.get('email', 'N/A')[:29]
            print(f"{name:<25} {role:<20} {email:<30}")
        return users
    return []

def main():
    print("="*70)
    print("EXERCISE 2: FIXED VERSION")
    print("="*70)
    
    # Step 1: Check available roles
    available_roles = check_roles()
    
    if not available_roles:
        print("\n❌ Tidak bisa mendapatkan roles. Cek koneksi API.")
        return
    
    # Step 2: Tentukan role yang akan digunakan
    # Coba cari role yang mengandung kata "admin" (case insensitive)
    admin_role = None
    for role in available_roles:
        if 'admin' in role.lower():
            admin_role = role
            break
    
    if not admin_role:
        print("\n❌ Tidak menemukan role admin. Gunakan role pertama:")
        admin_role = available_roles[0]
    
    print(f"\n✅ Menggunakan role: '{admin_role}'")
    
    # Step 3: Delete existing users
    delete_existing_users()
    
    # Step 4: Create users with the detected role
    users_to_create = [
        ("john.doe@example.com", "John Doe"),
        ("mike.smith@example.com", "Mike Smith"),
        ("cary.johnson@example.com", "Cary Johnson")
    ]
    
    for email, name in users_to_create:
        create_user(email, name, admin_role)
    
    # Step 5: List all users
    list_users()
    
    print("\n" + "="*70)
    print("✅ EXERCISE 2 COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()
