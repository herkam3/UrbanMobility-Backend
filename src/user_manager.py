# user_manager.py
from database_manager import DatabaseManager, InputValidator
from datetime import datetime
import secrets
import string

class UserManager:
    def __init__(self, session_manager):
        self.db = DatabaseManager()
        self.session = session_manager
        self.auth = session_manager.auth
        self.authz = session_manager.authz
      
    def create_user(self, username, password, role, first_name, last_name):
        """Create a new user (System Admin or Service Engineer)"""
        # Check permissions
        if not self.authz.can_manage_user_role(role):
            self.db.log_activity(
                self.auth.current_user['username'], 
                "Unauthorized user creation attempt", 
                f"Attempted to create {role}: {username}", 
                suspicious=True
            )
            return {
                'success': False,
                'message': f'Access denied. Cannot create {role} accounts.',
                'data': None
            }
        
        # Validate inputs
        validation_result = self._validate_user_input(username, password, role, first_name, last_name)
        if not validation_result['success']:
            return validation_result
        
        # Check if username already exists (case-insensitive)
        if self._username_exists(username):
            return {
                'success': False,
                'message': 'Username already exists.',
                'data': None
            }
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Hash password
            password_hash = self.db.hash_password(password)
            
            # Create user
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, first_name, last_name, 
                                 registration_date, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, password_hash, role, first_name, last_name,
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                  self.auth.current_user['username']))
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            # Log activity
            self.db.log_activity(
                self.auth.current_user['username'],
                f"New {role} user created",
                f"username: {username}, name: {first_name} {last_name}"
            )
            
            return {
                'success': True,
                'message': f'{role.replace("_", " ").title()} created successfully.',
                'data': {'user_id': user_id, 'username': username}
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error creating user: {str(e)}',
                'data': None
            }
    
    def update_user(self, username, first_name=None, last_name=None, new_password=None):
        """Update user profile information"""
        # Check if user exists and get user info
        user_info = self._get_user_by_username(username)
        if not user_info:
            return {
                'success': False,
                'message': 'User not found.',
                'data': None
            }
        
        # Check permissions
        current_username = self.auth.current_user['username']
        
        # Users can update their own profile
        if username.lower() == current_username.lower():
            # Self-update allowed
            pass
        # Or if they can manage this user role
        elif not self.authz.can_manage_user_role(user_info['role']):
            self.db.log_activity(
                current_username, 
                "Unauthorized user update attempt", 
                f"Attempted to update user: {username}", 
                suspicious=True
            )
            return {
                'success': False,
                'message': 'Access denied. Cannot update this user.',
                'data': None
            }
        
        # Validate inputs
        if first_name and not first_name.strip():
            return {'success': False, 'message': 'First name cannot be empty.', 'data': None}
        if last_name and not last_name.strip():
            return {'success': False, 'message': 'Last name cannot be empty.', 'data': None}
        if new_password and not InputValidator.validate_password(new_password):
            return {
                'success': False, 
                'message': 'Password must be 12-30 characters with uppercase, lowercase, digit, and special character.',
                'data': None
            }
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if first_name:
                updates.append("first_name = ?")
                params.append(first_name.strip())
            
            if last_name:
                updates.append("last_name = ?")
                params.append(last_name.strip())
            
            if new_password:
                updates.append("password_hash = ?")
                params.append(self.db.hash_password(new_password))
            
            if not updates:
                return {
                    'success': False,
                    'message': 'No updates provided.',
                    'data': None
                }
            
            params.append(username)
            
            cursor.execute(f'''
                UPDATE users SET {", ".join(updates)}
                WHERE username = ?
            ''', params)
            
            conn.commit()
            conn.close()
            
            # Log activity
            update_fields = []
            if first_name: update_fields.append("first_name")
            if last_name: update_fields.append("last_name")
            if new_password: update_fields.append("password")
            
            self.db.log_activity(
                current_username,
                f"User profile updated",
                f"Updated user: {username}, fields: {', '.join(update_fields)}"
            )
            
            return {
                'success': True,
                'message': 'User updated successfully.',
                'data': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error updating user: {str(e)}',
                'data': None
            }
    
    def delete_user(self, username):
        """Delete a user account"""
        # Get user info
        user_info = self._get_user_by_username(username)
        if not user_info:
            return {
                'success': False,
                'message': 'User not found.',
                'data': None
            }
        
        current_username = self.auth.current_user['username']
        
        # Check permissions
        if username.lower() == current_username.lower():
            # Self-deletion (only System Admins can delete themselves)
            if self.auth.current_user['role'] != 'system_admin':
                return {
                    'success': False,
                    'message': 'Only System Administrators can delete their own accounts.',
                    'data': None
                }
        elif not self.authz.can_manage_user_role(user_info['role']):
            self.db.log_activity(
                current_username, 
                "Unauthorized user deletion attempt", 
                f"Attempted to delete user: {username}", 
                suspicious=True
            )
            return {
                'success': False,
                'message': 'Access denied. Cannot delete this user.',
                'data': None
            }
        
        # Cannot delete super admin
        if user_info['role'] == 'super_admin':
            return {
                'success': False,
                'message': 'Cannot delete Super Administrator account.',
                'data': None
            }
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Soft delete (mark as inactive)
            cursor.execute('''
                UPDATE users SET is_active = 0
                WHERE username = ?
            ''', (username,))
            
            conn.commit()
            conn.close()
            
            # Log activity
            self.db.log_activity(
                current_username,
                f"User deleted",
                f"Deleted user: {username} ({user_info['role']})"
            )
            
            # If user deleted themselves, logout
            if username.lower() == current_username.lower():
                self.session.end_session()
            
            return {
                'success': True,
                'message': 'User deleted successfully.',
                'data': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error deleting user: {str(e)}',
                'data': None
            }
    
    def reset_password(self, username):
        """Reset user password to a temporary password"""
        # Get user info
        user_info = self._get_user_by_username(username)
        if not user_info:
            return {
                'success': False,
                'message': 'User not found.',
                'data': None
            }
        
        # Check permissions
        if not self.authz.can_manage_user_role(user_info['role']):
            self.db.log_activity(
                self.auth.current_user['username'], 
                "Unauthorized password reset attempt", 
                f"Attempted to reset password for: {username}", 
                suspicious=True
            )
            return {
                'success': False,
                'message': 'Access denied. Cannot reset password for this user.',
                'data': None
            }
        
        # Generate temporary password
        temp_password = self._generate_temporary_password()
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Update password
            password_hash = self.db.hash_password(temp_password)
            cursor.execute('''
                UPDATE users SET password_hash = ?
                WHERE username = ?
            ''', (password_hash, username))
            
            conn.commit()
            conn.close()
            
            # Log activity
            self.db.log_activity(
                self.auth.current_user['username'],
                f"Password reset",
                f"Reset password for user: {username}"
            )
            
            return {
                'success': True,
                'message': 'Password reset successfully.',
                'data': {'temporary_password': temp_password}
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error resetting password: {str(e)}',
                'data': None
            }
    
    def list_users(self):
        """Get list of all users with their roles"""
        # Check permissions
        if not self.authz.check_permission('view_users'):
            return {
                'success': False,
                'message': 'Access denied. Cannot view users.',
                'data': None
            }
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT username, role, first_name, last_name, registration_date, created_by, is_active
                FROM users
                WHERE is_active = 1
                ORDER BY role, username
            ''')
            
            users = cursor.fetchall()
            conn.close()
            
            user_list = []
            for user in users:
                user_list.append({
                    'username': user[0],
                    'role': user[1],
                    'first_name': user[2],
                    'last_name': user[3],
                    'registration_date': user[4],
                    'created_by': user[5],
                    'is_active': bool(user[6])
                })
            
            return {
                'success': True,
                'message': f'Found {len(user_list)} active users.',
                'data': user_list
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving users: {str(e)}',
                'data': None
            }
    
    def search_users(self, search_term):
        """Search users by username, first name, or last name"""
        if not self.authz.check_permission('view_users'):
            return {
                'success': False,
                'message': 'Access denied. Cannot search users.',
                'data': None
            }
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            search_pattern = f'%{search_term.lower()}%'
            cursor.execute('''
                SELECT username, role, first_name, last_name, registration_date, created_by
                FROM users
                WHERE is_active = 1 AND (
                    LOWER(username) LIKE ? OR 
                    LOWER(first_name) LIKE ? OR 
                    LOWER(last_name) LIKE ?
                )
                ORDER BY role, username
            ''', (search_pattern, search_pattern, search_pattern))
            
            users = cursor.fetchall()
            conn.close()
            
            user_list = []
            for user in users:
                user_list.append({
                    'username': user[0],
                    'role': user[1],
                    'first_name': user[2],
                    'last_name': user[3],
                    'registration_date': user[4],
                    'created_by': user[5]
                })
            
            return {
                'success': True,
                'message': f'Found {len(user_list)} users matching "{search_term}".',
                'data': user_list
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error searching users: {str(e)}',
                'data': None
            }
    
    def get_user_profile(self, username=None):
        """Get detailed profile information for a user"""
        # If no username provided, get current user's profile
        if username is None:
            username = self.auth.current_user['username']
        
        user_info = self._get_user_by_username(username)
        if not user_info:
            return {
                'success': False,
                'message': 'User not found.',
                'data': None
            }
        
        # Check permissions (can view own profile or if can manage this user type)
        current_username = self.auth.current_user['username']
        if (username.lower() != current_username.lower() and 
            not self.authz.can_manage_user_role(user_info['role'])):
            return {
                'success': False,
                'message': 'Access denied. Cannot view this user profile.',
                'data': None
            }
        
        return {
            'success': True,
            'message': 'Profile retrieved successfully.',
            'data': user_info
        }
    
    def _validate_user_input(self, username, password, role, first_name, last_name):
        """Validate user input data"""
        # Validate username
        if not InputValidator.validate_username(username):
            return {
                'success': False,
                'message': 'Username must be 8-10 characters, start with letter/underscore, contain only letters, numbers, underscores, apostrophes, and periods.',
                'data': None
            }
        
        # Validate password
        if not InputValidator.validate_password(password):
            return {
                'success': False,
                'message': 'Password must be 12-30 characters with at least one uppercase, lowercase, digit, and special character.',
                'data': None
            }
        
        # Validate role
        if role not in ['system_admin', 'service_engineer']:
            return {
                'success': False,
                'message': 'Invalid role. Must be system_admin or service_engineer.',
                'data': None
            }
        
        # Validate names
        if not first_name or not first_name.strip():
            return {
                'success': False,
                'message': 'First name is required.',
                'data': None
            }
        
        if not last_name or not last_name.strip():
            return {
                'success': False,
                'message': 'Last name is required.',
                'data': None
            }
        
        return {'success': True, 'message': 'Validation passed.', 'data': None}
    
    def _username_exists(self, username):
        """Check if username already exists (case-insensitive)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        count = cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE LOWER(username) = ? AND is_active = 1
        ''', (username.lower(),)).fetchone()[0]
        
        conn.close()
        return count > 0
    
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
    
    def _generate_temporary_password(self):
        """Generate a secure temporary password"""
        # Ensure password meets requirements
        uppercase = secrets.choice(string.ascii_uppercase)
        lowercase = secrets.choice(string.ascii_lowercase)
        digit = secrets.choice(string.digits)
        special = secrets.choice("!@#$%&*")
        
        # Generate remaining characters
        remaining_chars = ''.join(secrets.choice(
            string.ascii_letters + string.digits + "!@#$%&*"
        ) for _ in range(8))
        
        # Combine and shuffle
        temp_password = uppercase + lowercase + digit + special + remaining_chars
        temp_password_list = list(temp_password)
        secrets.SystemRandom().shuffle(temp_password_list)
        
        return ''.join(temp_password_list)
