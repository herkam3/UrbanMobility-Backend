# Urban Mobility Backend System

from db_handler import DatabaseHandler
from encryption import EncryptionHandler, generate_key
from utils import hash_password, check_password
from auth import AuthHandler
from validation import validate_username, validate_password, PREDEFINED_CITIES
from logging_handler import EncryptedLogger, generate_log_key
from backup_handler import BackupHandler
import getpass
import os

# --- Configuration ---
DB_PATH = "src/data/urban_mobility.db"
LOG_PATH = "src/logs/logs.enc"
BACKUP_DIR = "src/backups"
RESTORE_CODES_PATH = "src/backups/restore_codes.txt"
# In production, load these keys securely!
ENCRYPTION_KEY = generate_key()
LOG_KEY = generate_log_key()

def main():
    print("Welcome to the Urban Mobility Backend System!")
    # Initialize components
    db = DatabaseHandler(DB_PATH)
    enc = EncryptionHandler(ENCRYPTION_KEY)
    logger = EncryptedLogger(LOG_PATH, LOG_KEY)
    backup = BackupHandler(DB_PATH, BACKUP_DIR, RESTORE_CODES_PATH)
    auth = AuthHandler(db, enc)

    # Login loop
    while True:
        print("\n--- Login ---")
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        role = auth.authenticate_user(username, password)
        if role:
            logger.log(f"User '{username}' logged in.", user=username)
            print(f"Login successful! Role: {role}")
            main_menu(role, auth, db, enc, logger, backup, username)
        else:
            logger.log(f"Failed login attempt for '{username}'.", user=username)
            print("Invalid credentials. Try again.")

def main_menu(role, auth, db, enc, logger, backup, username):
    while True:
        print("\n--- Main Menu ---")
        print("1. Change Password")
        if role in ["Super Admin", "System Admin"]:
            print("2. Register User")
        if role in ["Super Admin", "System Admin"]:
            print("3. View Logs")
        if role in ["Super Admin", "System Admin"]:
            print("4. Create Backup")
            print("5. Restore Backup")
        print("0. Logout")

        choice = input("Select an option: ").strip()
        if choice == "1":
            new_pw = getpass.getpass("New password: ")
            if validate_password(new_pw):
                auth.change_password(username, new_pw)
                logger.log(f"User '{username}' changed their password.", user=username)
                print("Password changed successfully.")
            else:
                print("Password does not meet requirements.")
        elif choice == "2" and role in ["Super Admin", "System Admin"]:
            reg_user = input("New username: ").strip()
            reg_pw = getpass.getpass("New password: ")
            reg_role = input("Role (System Admin/Service Engineer): ").strip()
            if not validate_username(reg_user):
                print("Invalid username format.")
                continue
            if not validate_password(reg_pw):
                print("Invalid password format.")
                continue
            auth.register_user(reg_user, reg_pw, reg_role)
            logger.log(f"User '{username}' registered new user '{reg_user}' as '{reg_role}'.", user=username)
            print("User registered successfully.")
        elif choice == "3" and role in ["Super Admin", "System Admin"]:
            print("\n--- Logs ---")
            for entry in logger.read_logs():
                print(entry)
        elif choice == "4" and role in ["Super Admin", "System Admin"]:
            backup_path = backup.create_backup()
            logger.log(f"User '{username}' created a backup: {backup_path}", user=username)
            print(f"Backup created at {backup_path}")
        elif choice == "5" and role in ["Super Admin", "System Admin"]:
            print("Available backups:")
            backups = backup.list_backups()
            for idx, b in enumerate(backups):
                print(f"{idx+1}. {b}")
            sel = input("Select backup number to restore: ").strip()
            try:
                sel_idx = int(sel) - 1
                backup_file = backups[sel_idx]
                backup_zip = os.path.join(BACKUP_DIR, backup_file)
                if role == "Super Admin":
                    backup.restore_backup(backup_zip, is_super_admin=True)
                else:
                    code = input("Enter restore code: ").strip()
                    backup.restore_backup(backup_zip, restore_code=code, is_super_admin=False)
                logger.log(f"User '{username}' restored backup: {backup_file}", user=username)
                print("Backup restored successfully.")
            except Exception as e:
                print(f"Restore failed: {e}")
        elif choice == "0":
            logger.log(f"User '{username}' logged out.", user=username)
            print("Logged out.")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()