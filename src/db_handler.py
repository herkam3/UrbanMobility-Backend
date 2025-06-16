import sqlite3

class DatabaseHandler:
    def __init__(self, db_file):
        """Initialize the database connection."""
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        """Create necessary tables in the database."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username BLOB NOT NULL UNIQUE,  -- Encrypted
                password TEXT NOT NULL,         -- Hashed
                role TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS travellers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email BLOB NOT NULL UNIQUE,     -- Encrypted
                phone BLOB NOT NULL,            -- Encrypted
                address BLOB                    -- Encrypted
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS scooters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL,
                status TEXT NOT NULL,
                location TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action BLOB NOT NULL,           -- Encrypted
                user_id INTEGER,                -- Optional: who did it
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS restore_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                generated_by INTEGER,           -- Optional: admin id
                used INTEGER DEFAULT 0
            )
        ''')
        self.connection.commit()

    def execute_query(self, query, params=()):
        """Execute a query with optional parameters."""
        self.cursor.execute(query, params)
        self.connection.commit()

    def fetch_all(self, query, params=()):
        """Fetch all results from a query."""
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def close(self):
        """Close the database connection."""
        self.connection.close()