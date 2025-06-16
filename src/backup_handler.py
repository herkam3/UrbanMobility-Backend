import os
import shutil
import sqlite3
from datetime import datetime
import zipfile
import secrets

class BackupHandler:
    def __init__(self, db_path, backup_dir, restore_codes_path="restore_codes.txt"):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.restore_codes_path = restore_codes_path
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self):
        """Create a zip-based backup of the encrypted DB."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}.zip"
        backup_path = os.path.join(self.backup_dir, backup_name)
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(self.db_path, os.path.basename(self.db_path))
        return backup_path

    def restore_backup(self, backup_zip, restore_code=None, is_super_admin=False):
        """
        Restore the DB from a zip backup.
        - Super Admin can restore without code.
        - System Admin must provide a valid one-time restore code.
        """
        if not os.path.exists(backup_zip):
            raise FileNotFoundError("Backup file does not exist.")
        if not is_super_admin:
            if not self._validate_restore_code(restore_code):
                raise PermissionError("Invalid or used restore code.")
        with zipfile.ZipFile(backup_zip, 'r') as zipf:
            zipf.extract(os.path.basename(self.db_path), os.path.dirname(self.db_path))

    def list_backups(self):
        """List all backup zip files."""
        return [f for f in os.listdir(self.backup_dir) if f.endswith('.zip')]

    def delete_backup(self, backup_file):
        backup_path = os.path.join(self.backup_dir, backup_file)
        if os.path.exists(backup_path):
            os.remove(backup_path)
        else:
            raise FileNotFoundError("Backup file does not exist.")

    def generate_restore_code(self):
        """Generate a one-time restore code and save it."""
        code = secrets.token_urlsafe(8)
        with open(self.restore_codes_path, 'a') as f:
            f.write(f"{code}:unused\n")
        return code

    def _validate_restore_code(self, code):
        """Validate and mark a restore code as used."""
        if not code:
            return False
        if not os.path.exists(self.restore_codes_path):
            return False
        lines = []
        valid = False
        with open(self.restore_codes_path, 'r') as f:
            for line in f:
                if line.startswith(f"{code}:unused"):
                    lines.append(f"{code}:used\n")
                    valid = True
                else:
                    lines.append(line)
        if valid:
            with open(self.restore_codes_path, 'w') as f:
                f.writelines(lines)
        return valid