import os
from cryptography.fernet import Fernet
from datetime import datetime

class EncryptedLogger:
    def __init__(self, log_file, encryption_key):
        self.log_file = log_file
        self.fernet = Fernet(encryption_key)
        # Ensure the logs directory exists
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def log(self, message, user=None):
        """Encrypt and log a message with timestamp and optional user."""
        timestamp = datetime.utcnow().isoformat()
        user_info = f"[{user}]" if user else ""
        log_entry = f"{timestamp} {user_info} {message}"
        encrypted_entry = self.fernet.encrypt(log_entry.encode('utf-8'))
        with open(self.log_file, 'ab') as f:
            f.write(encrypted_entry + b'\n')

    def read_logs(self):
        """Decrypt and return all log entries as strings."""
        logs = []
        with open(self.log_file, 'rb') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        decrypted = self.fernet.decrypt(line).decode('utf-8')
                        logs.append(decrypted)
                    except Exception:
                        logs.append("[Corrupted log entry]")
        return logs

def generate_log_key():
    """Generate a new Fernet key for logging."""
    return Fernet.generate_key()

# Example usage
if __name__ == "__main__":
    key = generate_log_key()
    logger = EncryptedLogger('logs/logs.enc', key)
    logger.log("This is a test log message.", user="system")
    for entry in logger.read_logs():
        print(entry)