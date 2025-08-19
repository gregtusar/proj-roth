#!/usr/bin/env python3
"""
User management script for NJ Voter Chat authentication system
"""

import argparse
import sys
import uuid
from typing import Optional
from google.cloud import bigquery
from datetime import datetime
import json

# BigQuery configuration
PROJECT_ID = "proj-roth"
DATASET_ID = "voter_data"
TABLE_ID = "authorized_users"
TABLE_REF = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"


class UserManager:
    """Manage authorized users for NJ Voter Chat"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        
    def add_user(self, email: str, full_name: str, role: str = "viewer") -> bool:
        """Add a new authorized user"""
        try:
            # Check if user already exists
            check_query = f"""
                SELECT email FROM `{TABLE_REF}`
                WHERE email = @email
                LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("email", "STRING", email)
                ]
            )
            results = list(self.client.query(check_query, job_config=job_config).result())
            
            if results:
                print(f"❌ User {email} already exists")
                return False
            
            # Add new user
            user_id = str(uuid.uuid4())
            insert_query = f"""
                INSERT INTO `{TABLE_REF}` (
                    user_id, email, full_name, role, is_active, created_at
                ) VALUES (
                    @user_id, @email, @full_name, @role, TRUE, CURRENT_TIMESTAMP()
                )
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
                    bigquery.ScalarQueryParameter("email", "STRING", email),
                    bigquery.ScalarQueryParameter("full_name", "STRING", full_name),
                    bigquery.ScalarQueryParameter("role", "STRING", role),
                ]
            )
            self.client.query(insert_query, job_config=job_config).result()
            
            print(f"✅ Added user: {email} ({full_name}) with role: {role}")
            print(f"   User ID: {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding user: {e}")
            return False
    
    def remove_user(self, email: str) -> bool:
        """Remove/deactivate a user"""
        try:
            update_query = f"""
                UPDATE `{TABLE_REF}`
                SET is_active = FALSE
                WHERE email = @email
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("email", "STRING", email)
                ]
            )
            result = self.client.query(update_query, job_config=job_config).result()
            
            if result.num_dml_affected_rows > 0:
                print(f"✅ Deactivated user: {email}")
                return True
            else:
                print(f"❌ User {email} not found")
                return False
                
        except Exception as e:
            print(f"❌ Error removing user: {e}")
            return False
    
    def reactivate_user(self, email: str) -> bool:
        """Reactivate a deactivated user"""
        try:
            update_query = f"""
                UPDATE `{TABLE_REF}`
                SET is_active = TRUE
                WHERE email = @email
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("email", "STRING", email)
                ]
            )
            result = self.client.query(update_query, job_config=job_config).result()
            
            if result.num_dml_affected_rows > 0:
                print(f"✅ Reactivated user: {email}")
                return True
            else:
                print(f"❌ User {email} not found")
                return False
                
        except Exception as e:
            print(f"❌ Error reactivating user: {e}")
            return False
    
    def update_role(self, email: str, role: str) -> bool:
        """Update user's role"""
        valid_roles = ["viewer", "analyst", "admin"]
        if role not in valid_roles:
            print(f"❌ Invalid role. Must be one of: {', '.join(valid_roles)}")
            return False
            
        try:
            update_query = f"""
                UPDATE `{TABLE_REF}`
                SET role = @role
                WHERE email = @email
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("email", "STRING", email),
                    bigquery.ScalarQueryParameter("role", "STRING", role),
                ]
            )
            result = self.client.query(update_query, job_config=job_config).result()
            
            if result.num_dml_affected_rows > 0:
                print(f"✅ Updated role for {email} to: {role}")
                return True
            else:
                print(f"❌ User {email} not found")
                return False
                
        except Exception as e:
            print(f"❌ Error updating role: {e}")
            return False
    
    def list_users(self, active_only: bool = True) -> None:
        """List all authorized users"""
        try:
            where_clause = "WHERE is_active = TRUE" if active_only else ""
            query = f"""
                SELECT 
                    email,
                    full_name,
                    role,
                    is_active,
                    created_at,
                    last_login,
                    login_count
                FROM `{TABLE_REF}`
                {where_clause}
                ORDER BY created_at DESC
            """
            results = self.client.query(query).result()
            
            print("\n" + "="*80)
            print("AUTHORIZED USERS")
            print("="*80)
            
            for row in results:
                status = "✅ Active" if row.is_active else "❌ Inactive"
                last_login = row.last_login.strftime("%Y-%m-%d %H:%M") if row.last_login else "Never"
                print(f"\n📧 Email: {row.email}")
                print(f"   Name: {row.full_name}")
                print(f"   Role: {row.role}")
                print(f"   Status: {status}")
                print(f"   Created: {row.created_at.strftime('%Y-%m-%d')}")
                print(f"   Last Login: {last_login}")
                print(f"   Login Count: {row.login_count or 0}")
            
            print("\n" + "="*80)
            
        except Exception as e:
            print(f"❌ Error listing users: {e}")
    
    def get_user_info(self, email: str) -> None:
        """Get detailed info for a specific user"""
        try:
            query = f"""
                SELECT *
                FROM `{TABLE_REF}`
                WHERE email = @email
                LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("email", "STRING", email)
                ]
            )
            results = list(self.client.query(query, job_config=job_config).result())
            
            if not results:
                print(f"❌ User {email} not found")
                return
            
            row = results[0]
            print("\n" + "="*80)
            print(f"USER DETAILS: {email}")
            print("="*80)
            print(f"User ID: {row.user_id}")
            print(f"Email: {row.email}")
            print(f"Full Name: {row.full_name}")
            print(f"Given Name: {row.given_name or 'N/A'}")
            print(f"Family Name: {row.family_name or 'N/A'}")
            print(f"Google ID: {row.google_id or 'N/A'}")
            print(f"Role: {row.role}")
            print(f"Status: {'Active' if row.is_active else 'Inactive'}")
            print(f"Created: {row.created_at}")
            print(f"Last Login: {row.last_login or 'Never'}")
            print(f"Login Count: {row.login_count or 0}")
            print(f"Picture URL: {row.picture_url or 'N/A'}")
            print(f"Locale: {row.locale or 'N/A'}")
            if row.metadata:
                print(f"Metadata: {json.dumps(row.metadata, indent=2)}")
            print("="*80)
            
        except Exception as e:
            print(f"❌ Error getting user info: {e}")
    
    def bulk_add_users(self, filename: str) -> None:
        """Add multiple users from a CSV file"""
        import csv
        try:
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    email = row.get('email', '').strip()
                    name = row.get('name', '').strip()
                    role = row.get('role', 'viewer').strip()
                    
                    if email and name:
                        self.add_user(email, name, role)
                    else:
                        print(f"⚠️  Skipping invalid row: {row}")
                        
        except FileNotFoundError:
            print(f"❌ File not found: {filename}")
        except Exception as e:
            print(f"❌ Error processing file: {e}")


def main():
    parser = argparse.ArgumentParser(description="Manage authorized users for NJ Voter Chat")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add user command
    add_parser = subparsers.add_parser('add', help='Add a new user')
    add_parser.add_argument('email', help='User email address')
    add_parser.add_argument('name', help='User full name')
    add_parser.add_argument('--role', default='viewer', choices=['viewer', 'analyst', 'admin'],
                          help='User role (default: viewer)')
    
    # Remove user command
    remove_parser = subparsers.add_parser('remove', help='Remove/deactivate a user')
    remove_parser.add_argument('email', help='User email address')
    
    # Reactivate user command
    reactivate_parser = subparsers.add_parser('reactivate', help='Reactivate a user')
    reactivate_parser.add_argument('email', help='User email address')
    
    # Update role command
    role_parser = subparsers.add_parser('role', help='Update user role')
    role_parser.add_argument('email', help='User email address')
    role_parser.add_argument('role', choices=['viewer', 'analyst', 'admin'], help='New role')
    
    # List users command
    list_parser = subparsers.add_parser('list', help='List all users')
    list_parser.add_argument('--all', action='store_true', help='Include inactive users')
    
    # Get user info command
    info_parser = subparsers.add_parser('info', help='Get user details')
    info_parser.add_argument('email', help='User email address')
    
    # Bulk add command
    bulk_parser = subparsers.add_parser('bulk', help='Add users from CSV file')
    bulk_parser.add_argument('file', help='CSV file with columns: email, name, role')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = UserManager()
    
    if args.command == 'add':
        manager.add_user(args.email, args.name, args.role)
    elif args.command == 'remove':
        manager.remove_user(args.email)
    elif args.command == 'reactivate':
        manager.reactivate_user(args.email)
    elif args.command == 'role':
        manager.update_role(args.email, args.role)
    elif args.command == 'list':
        manager.list_users(not args.all)
    elif args.command == 'info':
        manager.get_user_info(args.email)
    elif args.command == 'bulk':
        manager.bulk_add_users(args.file)


if __name__ == "__main__":
    main()