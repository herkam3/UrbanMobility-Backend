# admin_menus.py

class AdminMenus:
    def __init__(self, console_interface):
        self.console = console_interface
        self.session = console_interface.session
        self.user_mgr = console_interface.user_mgr
        self.log_mgr = console_interface.log_mgr
        self.backup_mgr = console_interface.backup_mgr
    
    # ========== SYSTEM LOGS ==========
    
    def system_logs_menu(self):
        """System logs submenu"""
        while True:
            self.console.clear_screen()
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
        self.console.clear_screen()
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
    
    def view_suspicious_logs(self):
        """View suspicious activities"""
        self.console.clear_screen()
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
        self.console.clear_screen()
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
        self.console.clear_screen()
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
    
    # ========== BACKUP & RESTORE ==========
    
    def backup_restore_menu(self):
        """Backup and restore submenu"""
        while True:
            self.console.clear_screen()
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
        self.console.clear_screen()
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
        self.console.clear_screen()
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
    
    def restore_backup_submenu(self):
        """Restore from backup"""
        self.console.clear_screen()
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
            self.console.running = False
        
        input("Press Enter to continue...")
    
    def generate_restore_code_submenu(self):
        """Generate restore code for System Administrator"""
        self.console.clear_screen()
        print("=== GENERATE RESTORE CODE ===\n")
        
        # Show available backups first
        backup_result = self.backup_mgr.list_backups()
        if backup_result['success'] and backup_result['data']:
            print("Available backups:")
            for backup in backup_result['data']:
                print(f"  - {backup['filename']}")
        else:
            print("No backups available.")
            input("Press Enter to continue...")
            return
        
        backup_filename = input("\nBackup filename: ").strip()
        target_username = input("Target System Administrator username: ").strip()
        
        if not backup_filename or not target_username:
            print("Both fields are required.")
            input("Press Enter to continue...")
            return
        
        result = self.backup_mgr.generate_restore_code(backup_filename, target_username)
        print(f"\n{result['message']}")
        if result['success']:
            print(f"Restore Code: {result['data']['restore_code']}")
            print("⚠️  Share this code securely with the target user.")
        
        input("Press Enter to continue...")
    
    def revoke_restore_code_submenu(self):
        """Revoke a restore code"""
        self.console.clear_screen()
        print("=== REVOKE RESTORE CODE ===\n")
        
        restore_code = input("Restore code to revoke: ").strip()
        if not restore_code:
            print("Restore code cannot be empty.")
            input("Press Enter to continue...")
            return
        
        confirm = input(f"Are you sure you want to revoke code '{restore_code[:8]}...'? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            input("Press Enter to continue...")
            return
        
        result = self.backup_mgr.revoke_restore_code(restore_code)
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    # ========== SYSTEM ADMINISTRATOR MANAGEMENT ==========
    
    def system_admin_management_menu(self):
        """System Administrator management (Super Admin only)"""
        while True:
            self.console.clear_screen()
            print("=== SYSTEM ADMINISTRATOR MANAGEMENT ===\n")
            print("1. Create New System Administrator")
            print("2. List System Administrators")
            print("3. Update System Administrator")
            print("4. Delete System Administrator")
            print("5. Reset System Administrator Password")
            print("\n0. Back to Main Menu")
            print("-" * 50)
            
            choice = input("Enter your choice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.create_system_admin_submenu()
            elif choice == '2':
                self.list_system_admins_submenu()
            elif choice == '3':
                self.update_system_admin_submenu()
            elif choice == '4':
                self.delete_system_admin_submenu()
            elif choice == '5':
                self.reset_system_admin_password_submenu()
            else:
                print("Invalid choice.")
                input("Press Enter to continue...")
    
    def create_system_admin_submenu(self):
        """Create new System Administrator"""
        self.console.clear_screen()
        print("=== CREATE NEW SYSTEM ADMINISTRATOR ===\n")
        
        username = input("Username (8-10 chars): ").strip()
        password = input("Password: ").strip()
        first_name = input("First Name: ").strip()
        last_name = input("Last Name: ").strip()
        
        result = self.user_mgr.create_user(username, password, 'system_admin', first_name, last_name)
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def list_system_admins_submenu(self):
        """List system administrators"""
        self.console.clear_screen()
        print("=== SYSTEM ADMINISTRATORS ===\n")
        
        result = self.user_mgr.list_users()
        if result['success']:
            if result['data']:
                admins = [user for user in result['data'] if user['role'] == 'system_admin']
                if admins:
                    print(f"{'Username':<15} {'Name':<25} {'Created'}")
                    print("-" * 55)
                    for admin in admins:
                        name = f"{admin['first_name']} {admin['last_name']}"
                        print(f"{admin['username']:<15} {name:<25} {admin['registration_date'][:10]}")
                else:
                    print("No System Administrators found.")
            else:
                print("No System Administrators found.")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")
    
    def update_system_admin_submenu(self):
        """Update System Administrator"""
        self.console.clear_screen()
        print("=== UPDATE SYSTEM ADMINISTRATOR ===\n")
        
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
    
    def delete_system_admin_submenu(self):
        """Delete System Administrator"""
        self.console.clear_screen()
        print("=== DELETE SYSTEM ADMINISTRATOR ===\n")
        
        username = input("Username to delete: ").strip()
        if not username:
            print("Username cannot be empty.")
            input("Press Enter to continue...")
            return
        
        confirm = input(f"Are you sure you want to delete System Administrator '{username}'? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            input("Press Enter to continue...")
            return
        
        result = self.user_mgr.delete_user(username)
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def reset_system_admin_password_submenu(self):
        """Reset System Administrator password"""
        self.console.clear_screen()
        print("=== RESET SYSTEM ADMINISTRATOR PASSWORD ===\n")
        
        username = input("Username to reset password: ").strip()
        if not username:
            print("Username cannot be empty.")
            input("Press Enter to continue...")
            return
        
        result = self.user_mgr.reset_password(username)
        print(f"\n{result['message']}")
        if result['success']:
            print(f"Temporary password: {result['data']['temporary_password']}")
            print("⚠️  Share this password securely with the user.")
        
        input("Press Enter to continue...")
    
    # ========== RESTORE CODE MANAGEMENT ==========
    
    def restore_code_management_menu(self):
        """Restore code management (Super Admin only)"""
        while True:
            self.console.clear_screen()
            print("=== RESTORE CODE MANAGEMENT ===\n")
            print("1. Generate Restore Code")
            print("2. Revoke Restore Code")
            print("3. List Active Codes")
            print("\n0. Back to Main Menu")
            print("-" * 40)
            
            choice = input("Enter your choice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.generate_restore_code_submenu()
            elif choice == '2':
                self.revoke_restore_code_submenu()
            elif choice == '3':
                self.list_restore_codes_submenu()
            else:
                print("Invalid choice.")
                input("Press Enter to continue...")
    
    def list_restore_codes_submenu(self):
        """List active restore codes"""
        self.console.clear_screen()
        print("=== ACTIVE RESTORE CODES ===\n")
        
        # Simple implementation - would query backup_codes table in real version
        try:
            conn = self.backup_mgr.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT code, backup_file, assigned_to, created_date, used, revoked
                FROM backup_codes
                WHERE used = 0 AND revoked = 0
                ORDER BY created_date DESC
            ''')
            
            codes = cursor.fetchall()
            conn.close()
            
            if codes:
                print(f"{'Code (first 8)':<15} {'Backup File':<30} {'Assigned To':<15} {'Created'}")
                print("-" * 75)
                for code in codes:
                    code_display = code[0][:8] + "..."
                    print(f"{code_display:<15} {code[1]:<30} {code[2]:<15} {code[3][:10]}")
            else:
                print("No active restore codes found.")
                
        except Exception as e:
            print(f"Error retrieving codes: {e}")
        
        input("\nPress Enter to continue...")