# backup_logging_manager.py
from database_manager import DatabaseManager
from datetime import datetime
import os
import shutil
import zipfile
import secrets
import string


class LogManager:
    def __init__(self, session_manager):
        self.db = DatabaseManager()
        self.session = session_manager
        self.auth = session_manager.auth
        self.authz = session_manager.authz

    def view_logs(self, limit=50, show_suspicious_only=False):
        """View system logs with decryption"""
        # Check permissions
        if not self.authz.check_permission('view_logs'):
            self.db.log_activity(
                self.auth.current_user['username'],
                "Unauthorized log access attempt",
                "Attempted to view system logs",
                suspicious=True
            )
            return {
                'success': False,
                'message': 'Access denied. Cannot view system logs.',
                'data': None
            }

        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Build query based on filters
            query = '''
                SELECT id, date, time, username, description, additional_info, suspicious, read_status
                FROM activity_logs
            '''
            params = []

            if show_suspicious_only:
                query += ' WHERE suspicious = 1'

            query += ' ORDER BY id DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            logs = cursor.fetchall()

            # Mark suspicious logs as read
            if show_suspicious_only and logs:
                suspicious_ids = [log[0]
                                  # suspicious = 1
                                  for log in logs if log[6] == 1]
                if suspicious_ids:
                    placeholders = ','.join('?' * len(suspicious_ids))
                    cursor.execute(f'''
                        UPDATE activity_logs SET read_status = 1 
                        WHERE id IN ({placeholders})
                    ''', suspicious_ids)
                    conn.commit()

            conn.close()

            # Decrypt log entries
            decrypted_logs = []
            for log in logs:
                decrypted_log = {
                    'id': log[0],
                    'date': log[1],
                    'time': log[2],
                    'username': self.db.decrypt_data(log[3]) if log[3] else 'SYSTEM',
                    'description': self.db.decrypt_data(log[4]),
                    'additional_info': self.db.decrypt_data(log[5]) if log[5] else '',
                    'suspicious': bool(log[6]),
                    'read_status': bool(log[7])
                }
                decrypted_logs.append(decrypted_log)

            # Log this access
            self.db.log_activity(
                self.auth.current_user['username'],
                "System logs viewed",
                f"Viewed {len(decrypted_logs)} log entries, suspicious_only: {show_suspicious_only}"
            )

            return {
                'success': True,
                'message': f'Retrieved {len(decrypted_logs)} log entries.',
                'data': decrypted_logs
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving logs: {str(e)}',
                'data': None
            }

    def get_suspicious_activity_summary(self):
        """Get summary of suspicious activities"""
        if not self.authz.check_permission('view_logs'):
            return {
                'success': False,
                'message': 'Access denied. Cannot view suspicious activities.',
                'data': None
            }

        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get unread suspicious activities count
            unread_count = cursor.execute('''
                SELECT COUNT(*) FROM activity_logs 
                WHERE suspicious = 1 AND read_status = 0
            ''').fetchone()[0]

            # Get recent suspicious activities (last 10)
            cursor.execute('''
                SELECT date, time, username, description, additional_info
                FROM activity_logs
                WHERE suspicious = 1
                ORDER BY id DESC LIMIT 10
            ''')

            recent_suspicious = cursor.fetchall()
            conn.close()

            # Decrypt recent activities
            decrypted_activities = []
            for activity in recent_suspicious:
                decrypted_activity = {
                    'date': activity[0],
                    'time': activity[1],
                    'username': self.db.decrypt_data(activity[2]) if activity[2] else 'SYSTEM',
                    'description': self.db.decrypt_data(activity[3]),
                    'additional_info': self.db.decrypt_data(activity[4]) if activity[4] else ''
                }
                decrypted_activities.append(decrypted_activity)

            return {
                'success': True,
                'message': 'Suspicious activity summary retrieved.',
                'data': {
                    'unread_count': unread_count,
                    'recent_activities': decrypted_activities
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving suspicious activity summary: {str(e)}',
                'data': None
            }

    def search_logs(self, search_term, date_from=None, date_to=None):
        """Search logs by term and date range"""
        if not self.authz.check_permission('view_logs'):
            return {
                'success': False,
                'message': 'Access denied. Cannot search logs.',
                'data': None
            }

        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Note: Since logs are encrypted, we need to decrypt them to search
            # This is less efficient but necessary for security
            query = 'SELECT * FROM activity_logs'
            params = []

            # Add date filters if provided
            conditions = []
            if date_from:
                conditions.append('date >= ?')
                params.append(date_from)
            if date_to:
                conditions.append('date <= ?')
                params.append(date_to)

            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)

            query += ' ORDER BY id DESC'

            cursor.execute(query, params)
            all_logs = cursor.fetchall()
            conn.close()

            # Decrypt and filter logs
            matching_logs = []
            search_lower = search_term.lower()

            for log in all_logs:
                # Decrypt fields for searching
                username = self.db.decrypt_data(log[3]) if log[3] else 'SYSTEM'
                description = self.db.decrypt_data(log[4])
                additional_info = self.db.decrypt_data(
                    log[5]) if log[5] else ''

                # Check if search term matches any field
                if (search_lower in (username or "").lower() or
                    search_lower in (description or "").lower() or
                        search_lower in (additional_info or "").lower()):

                    matching_logs.append({
                        'id': log[0],
                        'date': log[1],
                        'time': log[2],
                        'username': username,
                        'description': description,
                        'additional_info': additional_info,
                        'suspicious': bool(log[6]),
                        'read_status': bool(log[7])
                    })

            # Log this search
            self.db.log_activity(
                self.auth.current_user['username'],
                "Log search performed",
                f"Search term: '{search_term}', Results: {len(matching_logs)}"
            )

            return {
                'success': True,
                'message': f'Found {len(matching_logs)} matching log entries.',
                'data': matching_logs
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error searching logs: {str(e)}',
                'data': None
            }


class BackupManager:
    def __init__(self, session_manager):
        self.db = DatabaseManager()
        self.session = session_manager
        self.auth = session_manager.auth
        self.authz = session_manager.authz
        self.backup_dir = "backups"

        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def create_backup(self):
        """Create a full system backup"""
        # Check permissions
        if not self.authz.check_permission('create_backup'):
            self.db.log_activity(
                self.auth.current_user['username'],
                "Unauthorized backup creation attempt",
                "Attempted to create system backup",
                suspicious=True
            )
            return {
                'success': False,
                'message': 'Access denied. Cannot create backups.',
                'data': None
            }

        try:
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"urban_mobility_backup_{timestamp}.zip"
            backup_path = os.path.join(self.backup_dir, backup_filename)

            # Create backup zip file
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                # Add database file
                db_path = self.db.db_path
                if os.path.exists(db_path):
                    backup_zip.write(db_path, os.path.basename(db_path))

                # Add encryption key
                key_path = "encryption.key"
                if os.path.exists(key_path):
                    backup_zip.write(key_path, os.path.basename(key_path))

                # Add backup metadata
                metadata = {
                    'backup_date': datetime.now().isoformat(),
                    'created_by': self.auth.current_user['username'],
                    'version': '1.0',
                    'description': 'Full Urban Mobility system backup'
                }

                backup_zip.writestr('backup_metadata.txt', str(metadata))

            # Log backup creation
            self.db.log_activity(
                self.auth.current_user['username'],
                "System backup created",
                f"Backup file: {backup_filename}"
            )

            return {
                'success': True,
                'message': 'Backup created successfully.',
                'data': {
                    'backup_filename': backup_filename,
                    'backup_path': backup_path,
                    'backup_size': os.path.getsize(backup_path)
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error creating backup: {str(e)}',
                'data': None
            }

    def restore_backup(self, backup_filename, restore_code=None):
        """Restore system from backup"""
        # Check permissions and restore code requirements
        current_role = self.auth.current_user['role']

        if current_role == 'super_admin':
            # Super admin can restore any backup without code
            if not self.authz.check_permission('restore_backup'):
                return {
                    'success': False,
                    'message': 'Access denied. Cannot restore backups.',
                    'data': None
                }
        elif current_role == 'system_admin':
            # System admin needs valid restore code
            if not self.authz.check_permission('restore_specific_backup'):
                return {
                    'success': False,
                    'message': 'Access denied. Cannot restore backups.',
                    'data': None
                }

            if not restore_code:
                return {
                    'success': False,
                    'message': 'Restore code required for System Administrator.',
                    'data': None
                }

            # Validate restore code
            code_validation = self._validate_restore_code(
                restore_code, backup_filename)
            if not code_validation['success']:
                return code_validation
        else:
            return {
                'success': False,
                'message': 'Access denied. Insufficient permissions to restore backups.',
                'data': None
            }

        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)

            if not os.path.exists(backup_path):
                return {
                    'success': False,
                    'message': 'Backup file not found.',
                    'data': None
                }

            # Create restore directory
            restore_dir = "restore_temp"
            if os.path.exists(restore_dir):
                shutil.rmtree(restore_dir)
            os.makedirs(restore_dir)

            # Extract backup
            with zipfile.ZipFile(backup_path, 'r') as backup_zip:
                backup_zip.extractall(restore_dir)

            # Backup current database before restore
            current_db_backup = f"pre_restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(self.db.db_path, current_db_backup)

            # Restore database
            restored_db_path = os.path.join(
                restore_dir, os.path.basename(self.db.db_path))
            if os.path.exists(restored_db_path):
                shutil.copy2(restored_db_path, self.db.db_path)

            # Restore encryption key if exists
            restored_key_path = os.path.join(restore_dir, "encryption.key")
            if os.path.exists(restored_key_path):
                shutil.copy2(restored_key_path, "encryption.key")

            # Mark restore code as used if applicable
            if restore_code and current_role == 'system_admin':
                self._mark_restore_code_used(restore_code)

            # Clean up restore directory
            shutil.rmtree(restore_dir)

            # Log restore operation
            self.db.log_activity(
                self.auth.current_user['username'],
                "System restored from backup",
                f"Backup file: {backup_filename}, Restore code used: {bool(restore_code)}"
            )

            return {
                'success': True,
                'message': 'System restored successfully. Please restart the application.',
                'data': {
                    'backup_filename': backup_filename,
                    'current_db_backup': current_db_backup
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error restoring backup: {str(e)}',
                'data': None
            }

    def generate_restore_code(self, backup_filename, target_username):
        """Generate one-time restore code for System Administrator"""
        # Only Super Admin can generate restore codes
        if not self.authz.check_permission('generate_restore_code'):
            self.db.log_activity(
                self.auth.current_user['username'],
                "Unauthorized restore code generation attempt",
                f"Attempted to generate code for: {target_username}",
                suspicious=True
            )
            return {
                'success': False,
                'message': 'Access denied. Cannot generate restore codes.',
                'data': None
            }

        # Verify backup file exists
        backup_path = os.path.join(self.backup_dir, backup_filename)
        if not os.path.exists(backup_path):
            return {
                'success': False,
                'message': 'Backup file not found.',
                'data': None
            }

        # Verify target user exists and is system admin
        target_user = self._get_user_by_username(target_username)
        if not target_user or target_user['role'] != 'system_admin':
            return {
                'success': False,
                'message': 'Target user must be a System Administrator.',
                'data': None
            }

        try:
            # Generate unique restore code
            restore_code = self._generate_restore_code()

            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO backup_codes (code, backup_file, created_by, assigned_to, created_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (restore_code, backup_filename, self.auth.current_user['username'],
                  target_username, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            conn.commit()
            conn.close()

            # Log code generation
            self.db.log_activity(
                self.auth.current_user['username'],
                "Restore code generated",
                f"Code for: {target_username}, Backup: {backup_filename}"
            )

            return {
                'success': True,
                'message': 'Restore code generated successfully.',
                'data': {
                    'restore_code': restore_code,
                    'backup_filename': backup_filename,
                    'assigned_to': target_username,
                    'expires': 'One-time use only'
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error generating restore code: {str(e)}',
                'data': None
            }

    def revoke_restore_code(self, restore_code):
        """Revoke a previously generated restore code"""
        # Only Super Admin can revoke restore codes
        if not self.authz.check_permission('revoke_restore_code'):
            self.db.log_activity(
                self.auth.current_user['username'],
                "Unauthorized restore code revocation attempt",
                f"Attempted to revoke code: {restore_code[:8]}...",
                suspicious=True
            )
            return {
                'success': False,
                'message': 'Access denied. Cannot revoke restore codes.',
                'data': None
            }

        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Check if code exists and is not already used/revoked
            cursor.execute('''
                SELECT assigned_to, backup_file, used, revoked 
                FROM backup_codes WHERE code = ?
            ''', (restore_code,))

            code_info = cursor.fetchone()

            if not code_info:
                conn.close()
                return {
                    'success': False,
                    'message': 'Restore code not found.',
                    'data': None
                }

            if code_info[2]:  # already used
                conn.close()
                return {
                    'success': False,
                    'message': 'Restore code has already been used.',
                    'data': None
                }

            if code_info[3]:  # already revoked
                conn.close()
                return {
                    'success': False,
                    'message': 'Restore code has already been revoked.',
                    'data': None
                }

            # Revoke the code
            cursor.execute('''
                UPDATE backup_codes SET revoked = 1 
                WHERE code = ?
            ''', (restore_code,))

            conn.commit()
            conn.close()

            # Log revocation
            self.db.log_activity(
                self.auth.current_user['username'],
                "Restore code revoked",
                f"Revoked code for: {code_info[0]}, Backup: {code_info[1]}"
            )

            return {
                'success': True,
                'message': 'Restore code revoked successfully.',
                'data': None
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error revoking restore code: {str(e)}',
                'data': None
            }

    def list_backups(self):
        """List all available backup files"""
        if not self.authz.check_permission('create_backup'):
            return {
                'success': False,
                'message': 'Access denied. Cannot view backups.',
                'data': None
            }

        try:
            backups = []

            if os.path.exists(self.backup_dir):
                for filename in os.listdir(self.backup_dir):
                    if filename.endswith('.zip'):
                        file_path = os.path.join(self.backup_dir, filename)
                        stat_info = os.stat(file_path)

                        backups.append({
                            'filename': filename,
                            'size': stat_info.st_size,
                            'created_date': datetime.fromtimestamp(stat_info.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                            'modified_date': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        })

            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x['created_date'], reverse=True)

            return {
                'success': True,
                'message': f'Found {len(backups)} backup files.',
                'data': backups
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error listing backups: {str(e)}',
                'data': None
            }

    def _validate_restore_code(self, restore_code, backup_filename):
        """Validate restore code for specific backup and user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT assigned_to, used, revoked 
                FROM backup_codes 
                WHERE code = ? AND backup_file = ?
            ''', (restore_code, backup_filename))

            code_info = cursor.fetchone()
            conn.close()

            if not code_info:
                return {
                    'success': False,
                    'message': 'Invalid restore code or backup file mismatch.',
                    'data': None
                }

            if code_info[0] != self.auth.current_user['username']:
                return {
                    'success': False,
                    'message': 'Restore code not assigned to current user.',
                    'data': None
                }

            if code_info[1]:  # used
                return {
                    'success': False,
                    'message': 'Restore code has already been used.',
                    'data': None
                }

            if code_info[2]:  # revoked
                return {
                    'success': False,
                    'message': 'Restore code has been revoked.',
                    'data': None
                }

            return {'success': True, 'message': 'Valid restore code.', 'data': None}

        except Exception as e:
            return {
                'success': False,
                'message': f'Error validating restore code: {str(e)}',
                'data': None
            }

    def _mark_restore_code_used(self, restore_code):
        """Mark restore code as used"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE backup_codes SET used = 1 
                WHERE code = ?
            ''', (restore_code,))

            conn.commit()
            conn.close()

        except Exception:
            pass  # Don't fail restore if marking fails

    def _generate_restore_code(self):
        """Generate a secure restore code"""
        # Generate 16-character alphanumeric code
        characters = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(characters) for _ in range(16))

    def _get_user_by_username(self, username):
        """Get user information by username"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, username, role, first_name, last_name, registration_date, created_by
            FROM users
            WHERE LOWER(username) = ? AND is_active = 1
        ''', (username.lower(),))

        user = cursor.fetchone()
        conn.close()

        if user:
            return {
                'id': user[0],
                'username': user[1],
                'role': user[2],
                'first_name': user[3],
                'last_name': user[4],
                'registration_date': user[5],
                'created_by': user[6]
            }
        return None
