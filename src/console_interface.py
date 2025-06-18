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

            password = input("Password: ").strip()

            if not password:
                print("Password cannot be empty.")
                attempts += 1
                continue

            # Attempt login
            self.session.start_session()
            result = self.session.auth.login(username, password)

            if result['success']:
                print(
                    f"\n✓ Login successful! Welcome, {result['user']['first_name']} {result['user']['last_name']}")
                print(
                    f"  Role: {result['user']['role'].replace('_', ' ').title()}")

                if result.get('unread_suspicious', 0) > 0:
                    print(
                        f"  ⚠️  {result['unread_suspicious']} unread suspicious activities")

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
        if self.session.authz and self.log_mgr and self.session.authz.check_permission('view_logs'):
            summary = self.log_mgr.get_suspicious_activity_summary()
            if summary and summary.get('success') and summary.get('data') and summary['data'].get('unread_count', 0) > 0:
                print(f"\n{'=' * 60}")
                print(
                    f"⚠️  SECURITY ALERT: {summary['data']['unread_count']} unread suspicious activities")
                print("   Use 'System Logs' menu to review these activities.")
                print("=" * 60)
                input("Press Enter to continue...")

    def show_main_menu(self):
        """Display main menu based on user role"""
        self.clear_screen()

        # Fix: Add None check for current user
        user = self.session.auth.get_current_user()
        if not user:
            print("Error: No user logged in.")
            return

        role = user['role']

        print(f"URBAN MOBILITY - Main Menu")
        print(
            f"User: {user['first_name']} {user['last_name']} ({role.replace('_', ' ').title()})")
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
        from menu_handlers import MenuHandlers
        from admin_menus import AdminMenus

        # Initialize menu handlers
        menu_handlers = MenuHandlers(self)
        admin_menus = AdminMenus(self)

        current_user = self.session.auth.get_current_user()
        if not current_user:
            print("Error: No user logged in.")
            return

        user_role = current_user['role']

        if choice == '0':
            self.logout()
        elif choice == '1':
            self.update_password_menu()
        elif choice == '2':
            self.view_profile_menu()
        elif choice == '3':
            if user_role == 'service_engineer':
                menu_handlers.search_scooters_menu()
            elif user_role in ['system_admin', 'super_admin']:
                menu_handlers.user_management_menu()
        elif choice == '4':
            if user_role == 'service_engineer':
                menu_handlers.update_scooter_menu()
            elif user_role in ['system_admin', 'super_admin']:
                menu_handlers.traveller_management_menu()
        elif choice == '5' and user_role in ['system_admin', 'super_admin']:
            menu_handlers.scooter_management_menu()
        elif choice == '6' and user_role in ['system_admin', 'super_admin']:
            admin_menus.system_logs_menu()
        elif choice == '7' and user_role in ['system_admin', 'super_admin']:
            admin_menus.backup_restore_menu()
        elif choice == '8' and user_role == 'super_admin':
            admin_menus.system_admin_management_menu()
        elif choice == '9' and user_role == 'super_admin':
            admin_menus.restore_code_management_menu()
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
        
        # Fix: Add None check and current password verification
        current_user = self.session.auth.get_current_user()
        if current_user and self.user_mgr:
            username = current_user['username']
            
            # Verify current password first
            login_result = self.session.auth.login(username, current_password)
            if not login_result['success']:
                print("Current password is incorrect.")
                input("Press Enter to continue...")
                return
            
            # Update password
            result = self.user_mgr.update_user(username, new_password=new_password)
            print(f"\n{result['message']}")
        else:
            print("Error: Session not properly initialized.")
        
        input("Press Enter to continue...")

    def view_profile_menu(self):
        """View user profile"""
        self.clear_screen()
        print("=== MY PROFILE ===\n")

        # Fix: Add None check
        if self.user_mgr:
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
        else:
            print("Error: User manager not initialized.")

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


if __name__ == "__main__":
    app = ConsoleInterface()
    app.run()
