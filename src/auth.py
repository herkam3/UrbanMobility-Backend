from utils import hash_password, check_password
from encryption import EncryptionHandler
from db_handler import DatabaseHandler

# Hardcoded Super Admin credentials (as per README)
SUPER_ADMIN_USERNAME = "super_admin"
SUPER_ADMIN_PASSWORD = "Admin_123?"
SUPER_ADMIN_ROLE = "Super Admin"

class AuthHandler:
    def __init__(self, db_handler: DatabaseHandler, encryption_handler: EncryptionHandler):
        self.db = db_handler
        self.enc = encryption_handler
        self.ensure_super_admin()

    def ensure_super_admin(self):
        """Ensure the hardcoded Super Admin exists in the DB."""
        enc_username = self.enc.encrypt_str(SUPER_ADMIN_USERNAME.lower())
        user = self.db.fetch_all("SELECT * FROM users WHERE username = ?", (enc_username,))
        if not user:
            hashed_pw = hash_password(SUPER_ADMIN_PASSWORD)
            self.db.execute_query(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (enc_username, hashed_pw, SUPER_ADMIN_ROLE)
            )

    def register_user(self, username, password, role):
        """Register a new user with encrypted username and hashed password."""
        enc_username = self.enc.encrypt_str(username.lower())
        hashed_pw = hash_password(password)
        self.db.execute_query(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (enc_username, hashed_pw, role)
        )

    def authenticate_user(self, username, password):
        """Authenticate user by encrypted username and bcrypt password."""
        enc_username = self.enc.encrypt_str(username.lower())
        user = self.db.fetch_all("SELECT * FROM users WHERE username = ?", (enc_username,))
        if user:
            user = user[0]
            if check_password(user[2], password):  # user[2] is password
                return user[3]  # user[3] is role
        return None

    def change_password(self, username, new_password):
        """Change password for a user."""
        enc_username = self.enc.encrypt_str(username.lower())
        hashed_pw = hash_password(new_password)
        self.db.execute_query(
            "UPDATE users SET password = ? WHERE username = ?",
            (hashed_pw, enc_username)
        )

# Example usage (console-based)
if __name__ == "__main__":
    # You would load your encryption key securely in a real app
    key = b'your-fernet-key-here'  # Replace with your actual key
    db = DatabaseHandler('src/data/urban_mobility.db')
    enc = EncryptionHandler(key)
    auth = AuthHandler(db, enc)

    # Example: Register and authenticate a user
    username = input("Enter username: ")
    password = input("Enter password: ")
    role = input("Enter role: ")
    auth.register_user(username, password, role)
    print("User registered.")

    username = input("Login username: ")
    password = input("Login password: ")
    user_role = auth.authenticate_user(username, password)
    if user_role:
        print(f"Login successful. Role: {user_role}")
    else:
        print("Invalid credentials.")