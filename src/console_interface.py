# console_interface.py
import os
import sys
from datetime import datetime
from auth_manager import SessionManager
from user_manager import UserManager
from traveller_manager import TravellerManager
from scooter_manager import ScooterManager
from backup_logging_manager import LogManager, BackupManager

class ConsoleInterface:
    def __init__(self):
        self.session = SessionManager()
        self.user_mgr = None
        self.traveller_mgr = None
        self.scooter_mgr = None
        self.log_mgr = None
        self.backup_mgr = None
        self.running = False
    
    def run(self):
        """Main application loop"""
        self.clear_screen()
        self.print_welcome()
        
        # Login loop
        if not self.login_process():
            print("\nGoodbye!")
            return
        
        # Initialize managers after successful login
        self.initialize_managers()
        
        # Show unread suspicious activities alert
        self.show_suspicious_activity_alert()
        
        # Main menu loop
        self.running = True
        while self.running:
            try:
                self.show_main_menu()
                choice = input("\nEnter your choice: ").strip()
                self.handle_main_menu_choice(choice)
            except KeyboardInterrupt:
                print("\n\nExiting application...")
                self.logout()
                break
            except Exception as e:
                print(f"\nAn error occurred: {e}")
                input("Press Enter to continue...")
    
    def print_welcome(self):
        """Print welcome banner"""
        print("=" * 60)
        print("          URBAN MOBILITY BACKEND SYSTEM")
        print("              Secure Management Portal")
        print("=" * 60)
        print()
    
    def login_process(self):
        """Handle user login"""
        max_attempts = 3
        attempts = 0
        
        while attempts < max_attempts:
            print(f"\n--- LOGIN ({attempts + 1}/{max_attempts}) ---")
            username = input("Username: ").strip()
            
            if not username:
                print("Username cannot be empty.")
                attempts += 1
                continue
            
            # Hide password input (basic version - in real app would use getpass)
            password = input("Password: ").strip()
            
            if not password:
                print("Password cannot be empty.")
                attempts += 1
                continue
            
            # Attempt login
            self.session.start_session()
            result = self.session.auth.login(username, password)
            
            if result['success']:
                print(f"\n✓ Login successful! Welcome, {result['user']['first_name']} {result['user']['last_name']}")
                print(f"  Role: {result['user']['role'].replace('_', ' ').title()}")
                
                # Show unread suspicious activities count
                if result.get('unread_suspicious', 0) > 0:
                    print(f"  ⚠️  {result['unread_suspicious']} unread suspicious activities")
                
                input("\nPress Enter to continue...")
                return True
            else:
                print(f"\n✗ {result['message']}")
                attempts += 1
                
                if attempts < max_attempts:
                    input("Press Enter to try again...")
        
        print("\nMaximum login attempts exceeded.")
        return False
    
    def initialize_managers(self):
        """Initialize all manager instances"""
        self.user_mgr = UserManager(self.session)
        self.traveller_mgr = TravellerManager(self.session)
        self.scooter_mgr = ScooterManager(self.session)
        self.log_mgr = LogManager(self.session)
        self.backup_mgr = BackupManager(self.session)
    
    def show_suspicious_activity_alert(self):
        """Show alert for unread suspicious activities"""
        if self.session.authz.check_permission('view_logs'):
            summary = self.log_mgr.get_suspicious_activity_summary()
            if summary['success'] and summary['data']['unread_count'] > 0:
                print(f"\n{'=' * 60}")
                print(f"⚠️  SECURITY ALERT: {summary['data']['unread_count']} unread suspicious activities")
                print("   Use 'System Logs' menu to review these activities.")
                print("=" * 60)
                input("Press Enter to continue...")
    
    def show_main_menu(self):
        """Display main menu based on user role"""
        self.clear_screen()
        user = self.session.auth.get_current_user()
        role = user['role']
        
        print(f"URBAN MOBILITY - Main Menu")
        print(f"User: {user['first_name']} {user['last_name']} ({role.replace('_', ' ').title()})")
        print(f"Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        
        # Common options for all users
        print("1. Update My Password")
        print("2. View My Profile")
        
        # Service Engineer specific options
        if role == 'service_engineer':
            print("3. Search Scooters")
            print("4. Update Scooter Information")
        
        # System Administrator and Super Administrator options
        if role in ['system_admin', 'super_admin']:
            print("3. User Management")
            print("4. Traveller Management")
            print("5. Scooter Management")
            print("6. System Logs")
            print("7. Backup & Restore")
        
        # Super Administrator exclusive options
        if role == 'super_admin':
            print("8. System Administrator Management")
            print("9. Restore Code Management")
        
        print("\n0. Logout")
        print("-" * 60)
    
    def handle_main_menu_choice(self, choice):
        """Handle main menu selection"""
        user_role = self.session.auth.get_current_user()['role']
        
        if choice == '0':
            self.logout()
        elif choice == '1':
            self.update_password_menu()
        elif choice == '2':
            self.view_profile_menu()
        elif choice == '3':
            if user_role == 'service_engineer':
                self.search_scooters_menu()
            elif user_role in ['system_admin', 'super_admin']:
                self.user_management_menu()
        elif choice == '4':
            if user_role == 'service_engineer':
                self.update_scooter_menu()
            elif user_role in ['system_admin', 'super_admin']:
                self.traveller_management_menu()
        elif choice == '5' and user_role in ['system_admin', 'super_admin']:
            self.scooter_management_menu()
        elif choice == '6' and user_role in ['system_admin', 'super_admin']:
            self.system_logs_menu()
        elif choice == '7' and user_role in ['system_admin', 'super_admin']:
            self.backup_restore_menu()
        elif choice == '8' and user_role == 'super_admin':
            self.system_admin_management_menu()
        elif choice == '9' and user_role == 'super_admin':
            self.restore_code_management_menu()
        else:
            print("Invalid choice. Please try again.")
            input("Press Enter to continue...")
    
    def update_password_menu(self):
        """Update user password"""
        self.clear_screen()
        print("=== UPDATE PASSWORD ===\n")
        
        current_password = input("Current Password: ").strip()
        new_password = input("New Password: ").strip()
        confirm_password = input("Confirm New Password: ").strip()
        
        if new_password != confirm_password:
            print("Passwords do not match.")
            input("Press Enter to continue...")
            return
        
        # Update password
        username = self.session.auth.get_current_user()['username']
        result = self.user_mgr.update_user(username, new_password=new_password)
        
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def view_profile_menu(self):
        """View user profile"""
        self.clear_screen()
        print("=== MY PROFILE ===\n")
        
        result = self.user_mgr.get_user_profile()
        if result['success']:
            profile = result['data']
            print(f"Username: {profile['username']}")
            print(f"Role: {profile['role'].replace('_', ' ').title()}")
            print(f"First Name: {profile['first_name']}")
            print(f"Last Name: {profile['last_name']}")
            print(f"Registration Date: {profile['registration_date']}")
            print(f"Created By: {profile['created_by']}")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")
    
    def user_management_menu(self):
        """User management submenu"""
        while True:
            self.clear_screen()
            print("=== USER MANAGEMENT ===\n")
            print("1. Create New Service Engineer")
            print("2. List All Users")
            print("3. Search Users")
            print("4. Update User")
            print("5. Delete User")
            print("6. Reset User Password")
            print("\n0. Back to Main Menu")
            print("-" * 40)
            
            choice = input("Enter your choice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.create_user_submenu()
            elif choice == '2':
                self.list_users_submenu()
            elif choice == '3':
                self.search_users_submenu()
            elif choice == '4':
                self.update_user_submenu()
            elif choice == '5':
                self.delete_user_submenu()
            elif choice == '6':
                self.reset_password_submenu()
            else:
                print("Invalid choice.")
                input("Press Enter to continue...")
    
    def create_user_submenu(self):
        """Create new user"""
        self.clear_screen()
        print("=== CREATE NEW SERVICE ENGINEER ===\n")
        
        username = input("Username (8-10 chars): ").strip()
        password = input("Password: ").strip()
        first_name = input("First Name: ").strip()
        last_name = input("Last Name: ").strip()
        
        result = self.user_mgr.create_user(username, password, 'service_engineer', first_name, last_name)
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def list_users_submenu(self):
        """List all users"""
        self.clear_screen()
        print("=== ALL USERS ===\n")
        
        result = self.user_mgr.list_users()
        if result['success']:
            if result['data']:
                print(f"{'Username':<15} {'Role':<20} {'Name':<25} {'Created'}")
                print("-" * 80)
                for user in result['data']:
                    role_display = user['role'].replace('_', ' ').title()
                    name = f"{user['first_name']} {user['last_name']}"
                    print(f"{user['username']:<15} {role_display:<20} {name:<25} {user['registration_date'][:10]}")
            else:
                print("No users found.")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")
    
    def search_users_submenu(self):
        """Search users"""
        self.clear_screen()
        print("=== SEARCH USERS ===\n")
        
        search_term = input("Enter search term (name or username): ").strip()
        if not search_term:
            print("Search term cannot be empty.")
            input("Press Enter to continue...")
            return
        
        result = self.user_mgr.search_users(search_term)
        if result['success']:
            if result['data']:
                print(f"\n{'Username':<15} {'Role':<20} {'Name':<25}")
                print("-" * 60)
                for user in result['data']:
                    role_display = user['role'].replace('_', ' ').title()
                    name = f"{user['first_name']} {user['last_name']}"
                    print(f"{user['username']:<15} {role_display:<20} {name:<25}")
            else:
                print("No users found matching your search.")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")
    
    def traveller_management_menu(self):
        """Traveller management submenu"""
        while True:
            self.clear_screen()
            print("=== TRAVELLER MANAGEMENT ===\n")
            print("1. Register New Traveller")
            print("2. Search Travellers")
            print("3. Update Traveller")
            print("4. Delete Traveller")
            print("5. View Traveller Details")
            print("\n0. Back to Main Menu")
            print("-" * 40)
            
            choice = input("Enter your choice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.create_traveller_submenu()
            elif choice == '2':
                self.search_travellers_submenu()
            elif choice == '3':
                self.update_traveller_submenu()
            elif choice == '4':
                self.delete_traveller_submenu()
            elif choice == '5':
                self.view_traveller_details_submenu()
            else:
                print("Invalid choice.")
                input("Press Enter to continue...")
    
    def create_traveller_submenu(self):
        """Create new traveller"""
        self.clear_screen()
        print("=== REGISTER NEW TRAVELLER ===\n")
        
        print("Available cities:")
        cities = self.traveller_mgr.db.get_cities()
        for i, city in enumerate(cities, 1):
            print(f"{i}. {city}")
        
        print("\nEnter traveller information:")
        first_name = input("First Name: ").strip()
        last_name = input("Last Name: ").strip()
        birthday = input("Birthday (YYYY-MM-DD): ").strip()
        
        while True:
            gender = input("Gender (male/female): ").strip().lower()
            if gender in ['male', 'female']:
                break
            print("Please enter 'male' or 'female'")
        
        street_name = input("Street Name: ").strip()
        house_number = input("House Number: ").strip()
        zip_code = input("Zip Code (DDDDXX): ").strip().upper()
        
        while True:
            city = input("City: ").strip()
            if city in cities:
                break
            print(f"Please select from: {', '.join(cities)}")
        
        email_address = input("Email Address: ").strip()
        mobile_phone = input("Mobile Phone (8 digits): ").strip()
        driving_license = input("Driving License (XXDDDDDDD): ").strip().upper()
        
        result = self.traveller_mgr.create_traveller(
            first_name, last_name, birthday, gender, street_name,
            house_number, zip_code, city, email_address, mobile_phone, driving_license
        )
        
        print(f"\n{result['message']}")
        if result['success']:
            print(f"Customer ID: {result['data']['customer_id']}")
        
        input("Press Enter to continue...")
    
    def search_travellers_submenu(self):
        """Search travellers"""
        self.clear_screen()
        print("=== SEARCH TRAVELLERS ===\n")
        
        search_term = input("Enter search term (name or customer ID): ").strip()
        if not search_term:
            print("Search term cannot be empty.")
            input("Press Enter to continue...")
            return
        
        result = self.traveller_mgr.search_travellers(search_term)
        if result['success']:
            if result['data']:
                print(f"\n{'Customer ID':<15} {'Name':<25} {'City':<15} {'Registration'}")
                print("-" * 70)
                for traveller in result['data']:
                    name = f"{traveller['first_name']} {traveller['last_name']}"
                    print(f"{traveller['customer_id']:<15} {name:<25} {traveller['city']:<15} {traveller['registration_date'][:10]}")
            else:
                print("No travellers found matching your search.")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")
    
    def scooter_management_menu(self):
        """Scooter management submenu"""
        while True:
            self.clear_screen()
            print("=== SCOOTER MANAGEMENT ===\n")
            print("1. Add New Scooter")
            print("2. Search Scooters")
            print("3. Update Scooter")
            print("4. Delete Scooter")
            print("5. View Scooter Details")
            print("\n0. Back to Main Menu")
            print("-" * 40)
            
            choice = input("Enter your choice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.create_scooter_submenu()
            elif choice == '2':
                self.search_scooters_submenu()
            elif choice == '3':
                self.update_scooter_submenu()
            elif choice == '4':
                self.delete_scooter_submenu()
            elif choice == '5':
                self.view_scooter_details_submenu()
            else:
                print("Invalid choice.")
                input("Press Enter to continue...")
    
    def create_scooter_submenu(self):
        """Create new scooter"""
        self.clear_screen()
        print("=== ADD NEW SCOOTER ===\n")
        
        brand = input("Brand: ").strip()
        model = input("Model: ").strip()
        serial_number = input("Serial Number (10-17 alphanumeric): ").strip()
        
        try:
            top_speed = int(input("Top Speed (km/h): ").strip())
            battery_capacity = int(input("Battery Capacity (Wh): ").strip())
            state_of_charge = int(input("State of Charge (%): ").strip())
            target_min = int(input("Target Range SoC Min (%): ").strip())
            target_max = int(input("Target Range SoC Max (%): ").strip())
            latitude = float(input("Latitude (Rotterdam region): ").strip())
            longitude = float(input("Longitude (Rotterdam region): ").strip())
        except ValueError:
            print("Invalid numeric input.")
            input("Press Enter to continue...")
            return
        
        maintenance_date = input("Last Maintenance Date (YYYY-MM-DD, optional): ").strip()
        if not maintenance_date:
            maintenance_date = None
        
        result = self.scooter_mgr.create_scooter(
            brand, model, serial_number, top_speed, battery_capacity,
            state_of_charge, target_min, target_max, latitude, longitude, maintenance_date
        )
        
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def search_scooters_submenu(self):
        """Search scooters"""
        self.clear_screen()
        print("=== SEARCH SCOOTERS ===\n")
        
        search_term = input("Enter search term (serial, brand, or model): ").strip()
        if not search_term:
            print("Search term cannot be empty.")
            input("Press Enter to continue...")
            return
        
        result = self.scooter_mgr.search_scooters(search_term)
        if result['success']:
            if result['data']:
                print(f"\n{'Serial Number':<18} {'Brand':<12} {'Model':<15} {'Battery%':<10} {'Status'}")
                print("-" * 70)
                for scooter in result['data']:
                    status = "Out of Service" if scooter['out_of_service_status'] else "In Service"
                    print(f"{scooter['serial_number']:<18} {scooter['brand']:<12} {scooter['model']:<15} {scooter['state_of_charge']:<10} {status}")
            else:
                print("No scooters found matching your search.")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")
    
    def system_logs_menu(self):
        """System logs submenu"""
        while True:
            self.clear_screen()
            print("=== SYSTEM LOGS ===\n")
            print("1. View Recent Logs")
            print("2. View Suspicious Activities")
            print("3. Search Logs")
            print("4. Suspicious Activity Summary")
            print("\n0. Back to Main Menu")
            print("-" * 40)
            
            choice = input("Enter your choice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.view_recent_logs()
            elif choice == '2':
                self.view_suspicious_logs()
            elif choice == '3':
                self.search_logs_submenu()
            elif choice == '4':
                self.suspicious_summary_submenu()
            else:
                print("Invalid choice.")
                input("Press Enter to continue...")
    
    def view_recent_logs(self):
        """View recent system logs"""
        self.clear_screen()
        print("=== RECENT SYSTEM LOGS ===\n")
        
        try:
            limit = int(input("Number of logs to show (default 20): ").strip() or "20")
        except ValueError:
            limit = 20
        
        result = self.log_mgr.view_logs(limit=limit)
        if result['success']:
            if result['data']:
                print(f"\n{'Date':<12} {'Time':<10} {'User':<15} {'Description':<30} {'Suspicious'}")
                print("-" * 85)
                for log in result['data']:
                    suspicious_flag = "⚠️ YES" if log['suspicious'] else "No"
                    description = log['description'][:28] + ".." if len(log['description']) > 30 else log['description']
                    print(f"{log['date']:<12} {log['time']:<10} {log['username']:<15} {description:<30} {suspicious_flag}")
            else:
                print("No logs found.")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")
    
    def backup_restore_menu(self):
        """Backup and restore submenu"""
        while True:
            self.clear_screen()
            print("=== BACKUP & RESTORE ===\n")
            print("1. Create Backup")
            print("2. List Backups")
            print("3. Restore from Backup")
            if self.session.auth.get_current_user()['role'] == 'super_admin':
                print("4. Generate Restore Code")
                print("5. Revoke Restore Code")
            print("\n0. Back to Main Menu")
            print("-" * 40)
            
            choice = input("Enter your choice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.create_backup_submenu()
            elif choice == '2':
                self.list_backups_submenu()
            elif choice == '3':
                self.restore_backup_submenu()
            elif choice == '4' and self.session.auth.get_current_user()['role'] == 'super_admin':
                self.generate_restore_code_submenu()
            elif choice == '5' and self.session.auth.get_current_user()['role'] == 'super_admin':
                self.revoke_restore_code_submenu()
            else:
                print("Invalid choice.")
                input("Press Enter to continue...")
    
    def create_backup_submenu(self):
        """Create system backup"""
        self.clear_screen()
        print("=== CREATE BACKUP ===\n")
        
        confirm = input("Create a full system backup? (y/N): ").strip().lower()
        if confirm != 'y':
            return
        
        print("Creating backup...")
        result = self.backup_mgr.create_backup()
        
        print(f"\n{result['message']}")
        if result['success']:
            data = result['data']
            print(f"Backup file: {data['backup_filename']}")
            print(f"Size: {data['backup_size']} bytes")
        
        input("Press Enter to continue...")
    
    def list_backups_submenu(self):
        """List available backups"""
        self.clear_screen()
        print("=== AVAILABLE BACKUPS ===\n")
        
        result = self.backup_mgr.list_backups()
        if result['success']:
            if result['data']:
                print(f"{'Filename':<35} {'Size (KB)':<12} {'Created'}")
                print("-" * 60)
                for backup in result['data']:
                    size_kb = backup['size'] // 1024
                    print(f"{backup['filename']:<35} {size_kb:<12} {backup['created_date']}")
            else:
                print("No backups found.")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")
    
    def logout(self):
        """Logout user"""
        self.clear_screen()
        user = self.session.auth.get_current_user()
        if user:
            print(f"Goodbye, {user['first_name']}!")
        
        self.session.end_session()
        self.running = False
        print("Session ended successfully.")
    
    def clear_screen(self):
        """Clear console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    # Additional helper methods for remaining submenus...
    def update_user_submenu(self):
        """Update user information"""
        self.clear_screen()
        print("=== UPDATE USER ===\n")
        
        username = input("Username to update: ").strip()
        if not username:
            print("Username cannot be empty.")
            input("Press Enter to continue...")
            return
        
        first_name = input("New First Name (leave empty to skip): ").strip() or None
        last_name = input("New Last Name (leave empty to skip): ").strip() or None
        
        result = self.user_mgr.update_user(username, first_name=first_name, last_name=last_name)
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def delete_user_submenu(self):
        """Delete user"""
        self.clear_screen()
        print("=== DELETE USER ===\n")
        
        username = input("Username to delete: ").strip()
        if not username:
            print("Username cannot be empty.")
            input("Press Enter to continue...")
            return
        
        confirm = input(f"Are you sure you want to delete user '{username}'? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            input("Press Enter to continue...")
            return
        
        result = self.user_mgr.delete_user(username)
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def reset_password_submenu(self):
        """Reset user password"""
        self.clear_screen()
        print("=== RESET USER PASSWORD ===\n")
        
        username = input("Username to reset password: ").strip()
        if not username:
            print("Username cannot be empty.")
            input("Press Enter to continue...")
            return
        
        result = self.user_mgr.reset_password(username)
        print(f"\n{result['message']}")
        if result['success']:
            print(f"Temporary password: {result['data']['temporary_password']}")
            print("⚠️  Please share this password securely with the user.")
        
        input("Press Enter to continue...")
    
    def update_traveller_submenu(self):
        """Update traveller information"""
        self.clear_screen()
        print("=== UPDATE TRAVELLER ===\n")
        
        customer_id = input("Customer ID to update: ").strip()
        if not customer_id:
            print("Customer ID cannot be empty.")
            input("Press Enter to continue...")
            return
        
        print("Enter new information (leave empty to skip):")
        first_name = input("First Name: ").strip() or None
        last_name = input("Last Name: ").strip() or None
        email = input("Email Address: ").strip() or None
        mobile = input("Mobile Phone (8 digits): ").strip() or None
        
        updates = {}
        if first_name: updates['first_name'] = first_name
        if last_name: updates['last_name'] = last_name
        if email: updates['email_address'] = email
        if mobile: updates['mobile_phone'] = mobile
        
        if not updates:
            print("No updates provided.")
            input("Press Enter to continue...")
            return
        
        result = self.traveller_mgr.update_traveller(customer_id, **updates)
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def delete_traveller_submenu(self):
        """Delete traveller"""
        self.clear_screen()
        print("=== DELETE TRAVELLER ===\n")
        
        customer_id = input("Customer ID to delete: ").strip()
        if not customer_id:
            print("Customer ID cannot be empty.")
            input("Press Enter to continue...")
            return
        
        confirm = input(f"Are you sure you want to delete traveller '{customer_id}'? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            input("Press Enter to continue...")
            return
        
        result = self.traveller_mgr.delete_traveller(customer_id)
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def view_traveller_details_submenu(self):
        """View detailed traveller information"""
        self.clear_screen()
        print("=== TRAVELLER DETAILS ===\n")
        
        customer_id = input("Customer ID: ").strip()
        if not customer_id:
            print("Customer ID cannot be empty.")
            input("Press Enter to continue...")
            return
        
        result = self.traveller_mgr.get_traveller_details(customer_id)
        if result['success']:
            traveller = result['data']
            print(f"Customer ID: {traveller['customer_id']}")
            print(f"Name: {traveller['first_name']} {traveller['last_name']}")
            print(f"Birthday: {traveller['birthday']}")
            print(f"Gender: {traveller['gender']}")
            print(f"Address: {traveller['street_name']} {traveller['house_number']}")
            print(f"Zip/City: {traveller['zip_code']} {traveller['city']}")
            print(f"Email: {traveller['email_address']}")
            print(f"Phone: {traveller['mobile_phone']}")
            print(f"License: {traveller['driving_license_number']}")
            print(f"Registration: {traveller['registration_date']}")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")
    
    def update_scooter_submenu(self):
        """Update scooter information"""
        self.clear_screen()
        print("=== UPDATE SCOOTER ===\n")
        
        serial = input("Serial Number: ").strip()
        if not serial:
            print("Serial number cannot be empty.")
            input("Press Enter to continue...")
            return
        
        print("Enter new information (leave empty to skip):")
        try:
            soc_input = input("State of Charge (%): ").strip()
            soc = int(soc_input) if soc_input else None
            
            lat_input = input("Latitude: ").strip()
            lat = float(lat_input) if lat_input else None
            
            lon_input = input("Longitude: ").strip()
            lon = float(lon_input) if lon_input else None
            
            service_input = input("Out of service? (y/n): ").strip().lower()
            out_of_service = 1 if service_input == 'y' else 0 if service_input == 'n' else None
        except ValueError:
            print("Invalid numeric input.")
            input("Press Enter to continue...")
            return
        
        updates = {}
        if soc is not None: updates['state_of_charge'] = soc
        if lat is not None: updates['latitude'] = lat
        if lon is not None: updates['longitude'] = lon
        if out_of_service is not None: updates['out_of_service_status'] = out_of_service
        
        if not updates:
            print("No updates provided.")
            input("Press Enter to continue...")
            return
        
        result = self.scooter_mgr.update_scooter(serial, **updates)
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def delete_scooter_submenu(self):
        """Delete scooter"""
        self.clear_screen()
        print("=== DELETE SCOOTER ===\n")
        
        serial = input("Serial Number to delete: ").strip()
        if not serial:
            print("Serial number cannot be empty.")
            input("Press Enter to continue...")
            return
        
        confirm = input(f"Are you sure you want to delete scooter '{serial}'? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            input("Press Enter to continue...")
            return
        
        result = self.scooter_mgr.delete_scooter(serial)
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def view_scooter_details_submenu(self):
        """View detailed scooter information"""
        self.clear_screen()
        print("=== SCOOTER DETAILS ===\n")
        
        serial = input("Serial Number: ").strip()
        if not serial:
            print("Serial number cannot be empty.")
            input("Press Enter to continue...")
            return
        
        result = self.scooter_mgr.get_scooter_details(serial)
        if result['success']:
            scooter = result['data']
            print(f"Serial Number: {scooter['serial_number']}")
            print(f"Brand/Model: {scooter['brand']} {scooter['model']}")
            print(f"Top Speed: {scooter['top_speed']} km/h")
            print(f"Battery: {scooter['battery_capacity']} Wh")
            print(f"State of Charge: {scooter['state_of_charge']}%")
            print(f"Target SoC Range: {scooter['target_range_soc_min']}-{scooter['target_range_soc_max']}%")
            print(f"Location: {scooter['latitude']}, {scooter['longitude']}")
            print(f"Status: {'Out of Service' if scooter['out_of_service_status'] else 'In Service'}")
            print(f"Mileage: {scooter['mileage']} km")
            print(f"Last Maintenance: {scooter['last_maintenance_date'] or 'Not recorded'}")
            print(f"In Service Since: {scooter['in_service_date']}")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")
    
    def view_suspicious_logs(self):
        """View suspicious activities"""
        self.clear_screen()
        print("=== SUSPICIOUS ACTIVITIES ===\n")
        
        result = self.log_mgr.view_logs(limit=50, show_suspicious_only=True)
        if result['success']:
            if result['data']:
                print(f"{'Date':<12} {'Time':<10} {'User':<15} {'Description'}")
                print("-" * 70)
                for log in result['data']:
                    description = log['description'][:40] + ".." if len(log['description']) > 40 else log['description']
                    print(f"{log['date']:<12} {log['time']:<10} {log['username']:<15} {description}")
                
                print(f"\n⚠️  All {len(result['data'])} suspicious activities have been marked as read.")
            else:
                print("No suspicious activities found.")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")
    
    def search_logs_submenu(self):
        """Search system logs"""
        self.clear_screen()
        print("=== SEARCH LOGS ===\n")
        
        search_term = input("Enter search term: ").strip()
        if not search_term:
            print("Search term cannot be empty.")
            input("Press Enter to continue...")
            return
        
        result = self.log_mgr.search_logs(search_term)
        if result['success']:
            if result['data']:
                print(f"\n{'Date':<12} {'Time':<10} {'User':<15} {'Description':<30} {'Suspicious'}")
                print("-" * 85)
                for log in result['data']:
                    suspicious_flag = "⚠️ YES" if log['suspicious'] else "No"
                    description = log['description'][:28] + ".." if len(log['description']) > 30 else log['description']
                    print(f"{log['date']:<12} {log['time']:<10} {log['username']:<15} {description:<30} {suspicious_flag}")
            else:
                print("No logs found matching your search.")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")
    
    def suspicious_summary_submenu(self):
        """View suspicious activity summary"""
        self.clear_screen()
        print("=== SUSPICIOUS ACTIVITY SUMMARY ===\n")
        
        result = self.log_mgr.get_suspicious_activity_summary()
        if result['success']:
            data = result['data']
            print(f"Unread suspicious activities: {data['unread_count']}")
            
            if data['recent_activities']:
                print("\nRecent suspicious activities:")
                print(f"{'Date':<12} {'Time':<10} {'User':<15} {'Description'}")
                print("-" * 70)
                for activity in data['recent_activities']:
                    description = activity['description'][:40] + ".." if len(activity['description']) > 40 else activity['description']
                    print(f"{activity['date']:<12} {activity['time']:<10} {activity['username']:<15} {description}")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")
    
    def restore_backup_submenu(self):
        """Restore from backup"""
        self.clear_screen()
        print("=== RESTORE FROM BACKUP ===\n")
        
        # First show available backups
        print("Available backups:")
        result = self.backup_mgr.list_backups()
        if result['success'] and result['data']:
            for i, backup in enumerate(result['data'], 1):
                print(f"{i}. {backup['filename']} ({backup['created_date']})")
        else:
            print("No backups available.")
            input("Press Enter to continue...")
            return
        
        backup_filename = input("\nEnter backup filename: ").strip()
        if not backup_filename:
            print("Backup filename cannot be empty.")
            input("Press Enter to continue...")
            return
        
        restore_code = None
        if self.session.auth.get_current_user()['role'] == 'system_admin':
            restore_code = input("Enter restore code: ").strip()
        
        confirm = input(f"⚠️  This will replace the current system with backup '{backup_filename}'. Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            input("Press Enter to continue...")
            return
        
        print("Restoring backup...")
        result = self.backup_mgr.restore_backup(backup_filename, restore_code)
        print(f"\n{result['message']}")
        
        if result['success']:
            print("⚠️  Please restart the application to complete the restore.")
            self.running = False
        
        input("Press Enter to continue...")


if __name__ == "__main__":
    app = ConsoleInterface()
    app.run()