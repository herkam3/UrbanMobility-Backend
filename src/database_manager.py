# database_manager.py
import sqlite3
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="urban_mobility.db"):
        self.db_path = db_path
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.init_database()
    
    def _get_or_create_encryption_key(self):
        """Generate or retrieve encryption key for sensitive data"""
        key_file = "encryption.key"
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt_data(self, data):
        """Encrypt sensitive data"""
        if data is None:
            return None
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data):
        """Decrypt sensitive data"""
        if encrypted_data is None:
            return None
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    def hash_password(self, password):
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password, stored_hash):
        """Verify password against stored hash"""
        try:
            salt, hash_value = stored_hash.split(':')
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return password_hash == hash_value
        except:
            return False
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database with all required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table (System Admins and Service Engineers)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('super_admin', 'system_admin', 'service_engineer')),
                first_name TEXT,
                last_name TEXT,
                registration_date TEXT NOT NULL,
                created_by TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Travellers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS travellers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                birthday TEXT NOT NULL,
                gender TEXT NOT NULL CHECK (gender IN ('male', 'female')),
                street_name TEXT NOT NULL,
                house_number TEXT NOT NULL,
                zip_code TEXT NOT NULL,
                city TEXT NOT NULL,
                email_address TEXT NOT NULL,
                mobile_phone TEXT NOT NULL,
                driving_license_number TEXT NOT NULL,
                registration_date TEXT NOT NULL,
                created_by TEXT NOT NULL
            )
        ''')
        
        # Scooters table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scooters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                serial_number TEXT UNIQUE NOT NULL,
                top_speed INTEGER NOT NULL,
                battery_capacity INTEGER NOT NULL,
                state_of_charge INTEGER NOT NULL,
                target_range_soc_min INTEGER NOT NULL,
                target_range_soc_max INTEGER NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                out_of_service_status INTEGER DEFAULT 0,
                mileage REAL DEFAULT 0.0,
                last_maintenance_date TEXT,
                in_service_date TEXT NOT NULL,
                created_by TEXT NOT NULL
            )
        ''')
        
        # Activity logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                username TEXT,
                description TEXT NOT NULL,
                additional_info TEXT,
                suspicious INTEGER DEFAULT 0,
                read_status INTEGER DEFAULT 0
            )
        ''')
        
        # Backup codes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                backup_file TEXT NOT NULL,
                created_by TEXT NOT NULL,
                assigned_to TEXT NOT NULL,
                created_date TEXT NOT NULL,
                used INTEGER DEFAULT 0,
                revoked INTEGER DEFAULT 0
            )
        ''')
        
        # Predefined cities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Insert predefined cities
        cities = ['Rotterdam', 'Amsterdam', 'The Hague', 'Utrecht', 'Eindhoven', 
                 'Tilburg', 'Groningen', 'Almere', 'Breda', 'Nijmegen']
        
        for city in cities:
            cursor.execute('INSERT OR IGNORE INTO cities (name) VALUES (?)', (city,))
        
        # Insert hard-coded super admin
        super_admin_exists = cursor.execute(
            'SELECT COUNT(*) FROM users WHERE username = ?', ('super_admin',)
        ).fetchone()[0]
        
        if super_admin_exists == 0:
            password_hash = self.hash_password('Admin_123?')
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, first_name, last_name, 
                                 registration_date, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('super_admin', password_hash, 'super_admin', 'Super', 'Administrator',
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'SYSTEM'))
        
        conn.commit()
        conn.close()
    
    def log_activity(self, username, description, additional_info="", suspicious=False):
        """Log user activity"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now()
        date_str = now.strftime('%d-%m-%Y')
        time_str = now.strftime('%H:%M:%S')
        
        # Encrypt the log entry
        encrypted_description = self.encrypt_data(description)
        encrypted_additional_info = self.encrypt_data(additional_info) if additional_info else ""
        encrypted_username = self.encrypt_data(username) if username else ""
        
        cursor.execute('''
            INSERT INTO activity_logs (date, time, username, description, additional_info, suspicious)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date_str, time_str, encrypted_username, encrypted_description, 
              encrypted_additional_info, 1 if suspicious else 0))
        
        conn.commit()
        conn.close()
    
    def get_cities(self):
        """Get list of predefined cities"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cities = cursor.execute('SELECT name FROM cities ORDER BY name').fetchall()
        conn.close()
        return [city[0] for city in cities]
    
    def generate_customer_id(self):
        """Generate unique customer ID for travellers"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        while True:
            customer_id = str(secrets.randbelow(9000000000) + 1000000000)  # 10-digit number
            exists = cursor.execute(
                'SELECT COUNT(*) FROM travellers WHERE customer_id = ?', (customer_id,)
            ).fetchone()[0]
            if exists == 0:
                conn.close()
                return customer_id
    
    def close(self):
        """Clean up resources"""
        pass

# Input validation utilities
class InputValidator:
    @staticmethod
    def validate_zip_code(zip_code):
        """Validate Dutch zip code format: DDDDXX"""
        import re
        pattern = r'^\d{4}[A-Z]{2}$'
        return bool(re.match(pattern, zip_code))
    
    @staticmethod
    def validate_mobile_phone(phone):
        """Validate mobile phone format: DDDDDDDD (8 digits)"""
        import re
        pattern = r'^\d{8}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_driving_license(license_num):
        """Validate driving license format: XXDDDDDDD or XDDDDDDDD"""
        import re
        pattern = r'^[A-Z]{1,2}\d{7,8}$'
        return bool(re.match(pattern, license_num))
    
    @staticmethod
    def validate_email(email):
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_username(username):
        """Validate username according to requirements"""
        import re
        if len(username) < 8 or len(username) > 10:
            return False
        if not username[0].isalpha() and username[0] != '_':
            return False
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_.\'-]*$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def validate_password(password):
        """Validate password according to requirements"""
        if len(password) < 12 or len(password) > 30:
            return False
        
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "~!@#$%&_-+=`|\\(){}[]:;'<>,.?/" for c in password)
        
        return all([has_lower, has_upper, has_digit, has_special])
    
    @staticmethod
    def validate_serial_number(serial):
        """Validate scooter serial number: 10-17 alphanumeric characters"""
        import re
        pattern = r'^[a-zA-Z0-9]{10,17}$'
        return bool(re.match(pattern, serial))
    
    @staticmethod
    def validate_coordinates(lat, lon):
        """Validate GPS coordinates for Rotterdam region"""
        # Rotterdam region approximate bounds
        if not (51.85 <= lat <= 52.05):
            return False
        if not (4.35 <= lon <= 4.65):
            return False
        return True
    
    @staticmethod
    def validate_date_iso(date_str):
        """Validate ISO 8601 date format: YYYY-MM-DD"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

if __name__ == "__main__":
    # Test the database setup
    db = DatabaseManager()
    print("Database initialized successfully!")
    print("Available cities:", db.get_cities())
    
    # Test encryption
    test_data = "sensitive information"
    encrypted = db.encrypt_data(test_data)
    decrypted = db.decrypt_data(encrypted)
    print(f"Encryption test: {test_data} -> {encrypted[:20]}... -> {decrypted}")
    
    # Test password hashing
    password = "TestPassword123!"
    hashed = db.hash_password(password)
    verified = db.verify_password(password, hashed)
    print(f"Password test: {verified}")