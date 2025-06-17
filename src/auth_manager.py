# auth_manager.py
from database_manager import DatabaseManager, InputValidator
from datetime import datetime
import time

class AuthenticationManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.current_user = None
        self.failed_attempts = {}  # Track failed login attempts
        self.max_attempts = 3
        self.lockout_time = 300  # 5 minutes in seconds
    
    def login(self, username, password):
        """Authenticate user and return user info if successful"""
        # Check if user is locked out
        if self._is_locked_out(username):
            remaining_time = self._get_remaining_lockout_time(username)
            self.db.log_activity(username, "Login attempt while locked out", 
                               f"Remaining lockout time: {remaining_time} seconds", suspicious=True)
            return {
                'success': False, 
                'message': f'Account locked. Try again in {remaining_time} seconds.',
                'user': None
            }
        
        # Convert username to lowercase for case-insensitive comparison
        username_lower = username.lower()
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check for super admin (hard-coded)
        if username_lower == 'super_admin':
            cursor.execute('SELECT * FROM users WHERE username = ?', ('super_admin',))
        else:
            # For other users, check both original and lowercase
            cursor.execute('''
                SELECT * FROM users WHERE LOWER(username) = ? AND is_active = 1
            ''', (username_lower,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user and self.db.verify_password(password, user[2]):  # user[2] is password_hash
            # Successful login
            self._reset_failed_attempts(username_lower)
            self.current_user = {
                'id': user[0],
                'username': user[1],
                'role': user[3],
                'first_name': user[4],
                'last_name': user[5],
                'registration_date': user[6]
            }
            
            self.db.log_activity(username, "Logged in")
            
            # Check for unread suspicious activities for admins
            unread_count = self._get_unread_suspicious_count()
            
            return {
                'success': True, 
                'message': 'Login successful',
                'user': self.current_user,
                'unread_suspicious': unread_count
            }
        else:
            # Failed login
            self._record_failed_attempt(username_lower)
            attempts = self.failed_attempts.get(username_lower, {}).get('count', 0)
            
            if attempts >= self.max_attempts:
                self.db.log_activity(username, "Account locked due to multiple failed attempts", 
                                   f"Failed attempts: {attempts}", suspicious=True)
                return {
                    'success': False, 
                    'message': f'Account locked due to {attempts} failed attempts. Try again in {self.lockout_time} seconds.',
                    'user': None
                }
            else:
                remaining = self.max_attempts - attempts
                additional_info = f"Failed attempts: {attempts}, remaining: {remaining}"
                
                if attempts > 1:
                    self.db.log_activity(username, "Multiple unsuccessful login attempts", 
                                       additional_info, suspicious=True)
                else:
                    self.db.log_activity(username, "Unsuccessful login", 
                                       f"username: '{username}' used with wrong password")
                
                return {
                    'success': False, 
                    'message': f'Invalid credentials. {remaining} attempts remaining.',
                    'user': None
                }
    
    def logout(self):
        """Logout current user"""
        if self.current_user:
            self.db.log_activity(self.current_user['username'], "Logged out")
            self.current_user = None
            return True
        return False
    
    def _record_failed_attempt(self, username):
        """Record a failed login attempt"""
        current_time = time.time()
        if username not in self.failed_attempts:
            self.failed_attempts[username] = {'count': 0, 'last_attempt': current_time}
        
        self.failed_attempts[username]['count'] += 1
        self.failed_attempts[username]['last_attempt'] = current_time
    
    def _reset_failed_attempts(self, username):
        """Reset failed attempts counter"""
        if username in self.failed_attempts:
            del self.failed_attempts[username]
    
    def _is_locked_out(self, username):
        """Check if user is currently locked out"""
        username_lower = username.lower()
        if username_lower not in self.failed_attempts:
            return False
        
        attempts_data = self.failed_attempts[username_lower]
        if attempts_data['count'] < self.max_attempts:
            return False
        
        time_passed = time.time() - attempts_data['last_attempt']
        if time_passed >= self.lockout_time:
            # Lockout period expired, reset attempts
            self._reset_failed_attempts(username_lower)
            return False
        
        return True
    
    def _get_remaining_lockout_time(self, username):
        """Get remaining lockout time in seconds"""
        username_lower = username.lower()
        if username_lower not in self.failed_attempts:
            return 0
        
        time_passed = time.time() - self.failed_attempts[username_lower]['last_attempt']
        remaining = max(0, self.lockout_time - time_passed)
        return int(remaining)
    
    def _get_unread_suspicious_count(self):
        """Get count of unread suspicious activities"""
        if not self.current_user or self.current_user['role'] not in ['super_admin', 'system_admin']:
            return 0
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        count = cursor.execute('''
            SELECT COUNT(*) FROM activity_logs 
            WHERE suspicious = 1 AND read_status = 0
        ''').fetchone()[0]
        conn.close()
        return count
    
    def is_authenticated(self):
        """Check if user is currently authenticated"""
        return self.current_user is not None
    
    def get_current_user(self):
        """Get current authenticated user"""
        return self.current_user


class AuthorizationManager:
    def __init__(self, auth_manager):
        self.auth = auth_manager
    
    def check_permission(self, required_permission):
        """Check if current user has required permission"""
        if not self.auth.is_authenticated():
            return False
        
        user_role = self.auth.current_user['role']
        return self._has_permission(user_role, required_permission)
    
    def require_permission(self, required_permission):
        """Decorator-like function to check permissions"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                if not self.check_permission(required_permission):
                    return {
                        'success': False,
                        'message': 'Access denied. Insufficient permissions.',
                        'data': None
                    }
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def _has_permission(self, user_role, permission):
        """Check if a role has a specific permission"""
        role_permissions = {
            'super_admin': [
                # All permissions
                'manage_system_admins', 'manage_service_engineers', 'manage_travellers',
                'manage_scooters', 'view_logs', 'create_backup', 'restore_backup',
                'generate_restore_code', 'revoke_restore_code', 'view_users',
                'search_travellers', 'search_scooters', 'update_scooter_info',
                'update_own_password'
            ],
            'system_admin': [
                'manage_service_engineers', 'manage_travellers', 'manage_scooters',
                'view_logs', 'create_backup', 'restore_specific_backup', 'view_users',
                'search_travellers', 'search_scooters', 'update_scooter_info',
                'update_own_password', 'update_own_profile', 'delete_own_account'
            ],
            'service_engineer': [
                'update_scooter_info', 'search_scooters', 'update_own_password'
            ]
        }
        
        return permission in role_permissions.get(user_role, [])
    
    def get_user_permissions(self):
        """Get list of permissions for current user"""
        if not self.auth.is_authenticated():
            return []
        
        user_role = self.auth.current_user['role']
        
        all_permissions = {
            'super_admin': [
                'manage_system_admins', 'manage_service_engineers', 'manage_travellers',
                'manage_scooters', 'view_logs', 'create_backup', 'restore_backup',
                'generate_restore_code', 'revoke_restore_code', 'view_users',
                'search_travellers', 'search_scooters', 'update_scooter_info'
            ],
            'system_admin': [
                'manage_service_engineers', 'manage_travellers', 'manage_scooters',
                'view_logs', 'create_backup', 'restore_specific_backup', 'view_users',
                'search_travellers', 'search_scooters', 'update_scooter_info',
                'update_own_profile', 'delete_own_account'
            ],
            'service_engineer': [
                'update_scooter_info', 'search_scooters'
            ]
        }
        
        return all_permissions.get(user_role, [])
    
    def can_manage_user_role(self, target_role):
        """Check if current user can manage users of target role"""
        if not self.auth.is_authenticated():
            return False
        
        user_role = self.auth.current_user['role']
        
        # Super admin can manage system admins and service engineers
        if user_role == 'super_admin':
            return target_role in ['system_admin', 'service_engineer']
        
        # System admin can manage service engineers
        if user_role == 'system_admin':
            return target_role == 'service_engineer'
        
        return False
    
    def can_edit_scooter_attribute(self, attribute):
        """Check if current user can edit specific scooter attribute"""
        if not self.auth.is_authenticated():
            return False
        
        user_role = self.auth.current_user['role']
        
        # Super admin and system admin can edit all attributes
        if user_role in ['super_admin', 'system_admin']:
            return True
        
        # Service engineer can only edit specific attributes
        if user_role == 'service_engineer':
            allowed_attributes = [
                'state_of_charge', 'target_range_soc_min', 'target_range_soc_max',
                'latitude', 'longitude', 'out_of_service_status', 'mileage',
                'last_maintenance_date'
            ]
            return attribute in allowed_attributes
        
        return False


class SessionManager:
    def __init__(self):
        self.auth = AuthenticationManager()
        self.authz = AuthorizationManager(self.auth)
        self.session_start_time = None
    
    def start_session(self):
        """Start a new session"""
        self.session_start_time = datetime.now()
    
    def end_session(self):
        """End current session"""
        if self.auth.current_user:
            session_duration = datetime.now() - self.session_start_time if self.session_start_time else None
            duration_str = str(session_duration).split('.')[0] if session_duration else "unknown"
            
            self.auth.db.log_activity(
                self.auth.current_user['username'], 
                "Session ended", 
                f"Session duration: {duration_str}"
            )
        
        self.auth.logout()
        self.session_start_time = None
    
    def get_session_info(self):
        """Get current session information"""
        if not self.auth.is_authenticated():
            return None
        
        session_duration = datetime.now() - self.session_start_time if self.session_start_time else None
        
        return {
            'user': self.auth.current_user,
            'session_start': self.session_start_time,
            'session_duration': session_duration,
            'permissions': self.authz.get_user_permissions()
        }


if __name__ == "__main__":
    # Test the authentication system
    session = SessionManager()
    
    # Test login
    print("Testing login system...")
    result = session.auth.login("super_admin", "Admin_123?")
    print(f"Login result: {result}")
    
    if result['success']:
        print(f"Current user: {session.auth.get_current_user()}")
        print(f"Permissions: {session.authz.get_user_permissions()}")
        
        # Test permissions
        print(f"Can manage system admins: {session.authz.check_permission('manage_system_admins')}")
        print(f"Can edit scooter location: {session.authz.can_edit_scooter_attribute('latitude')}")
    
    # Test failed login
    print("\nTesting failed login...")
    fail_result = session.auth.login("invalid_user", "wrong_password")
    print(f"Failed login result: {fail_result}")