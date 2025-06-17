# traveller_manager.py
from database_manager import DatabaseManager, InputValidator
from datetime import datetime

class TravellerManager:
    def __init__(self, session_manager):
        self.db = DatabaseManager()
        self.session = session_manager
        self.auth = session_manager.auth
        self.authz = session_manager.authz
    
    def create_traveller(self, first_name, last_name, birthday, gender, street_name, 
                        house_number, zip_code, city, email_address, mobile_phone, 
                        driving_license_number):
        """Create a new traveller record"""
        # Check permissions
        if not self.authz.check_permission('manage_travellers'):
            self.db.log_activity(
                self.auth.current_user['username'], 
                "Unauthorized traveller creation attempt", 
                f"Attempted to create traveller: {first_name} {last_name}", 
                suspicious=True
            )
            return {
                'success': False,
                'message': 'Access denied. Cannot create traveller records.',
                'data': None
            }
        
        # Validate inputs
        validation_result = self._validate_traveller_input(
            first_name, last_name, birthday, gender, street_name, house_number,
            zip_code, city, email_address, mobile_phone, driving_license_number
        )
        if not validation_result['success']:
            return validation_result
        
        # Check for duplicate email or driving license
        duplicate_check = self._check_traveller_duplicates(email_address, driving_license_number)
        if not duplicate_check['success']:
            return duplicate_check
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Generate unique customer ID
            customer_id = self.db.generate_customer_id()
            
            # Encrypt sensitive data
            encrypted_email = self.db.encrypt_data(email_address)
            encrypted_phone = self.db.encrypt_data(f"+31-6-{mobile_phone}")
            encrypted_street = self.db.encrypt_data(street_name)
            encrypted_house = self.db.encrypt_data(house_number)
            
            # Insert traveller
            cursor.execute('''
                INSERT INTO travellers (
                    customer_id, first_name, last_name, birthday, gender, 
                    street_name, house_number, zip_code, city, email_address, 
                    mobile_phone, driving_license_number, registration_date, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, first_name, last_name, birthday, gender,
                  encrypted_street, encrypted_house, zip_code, city, encrypted_email,
                  encrypted_phone, driving_license_number, 
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  self.auth.current_user['username']))
            
            conn.commit()
            traveller_id = cursor.lastrowid
            conn.close()
            
            # Log activity
            self.db.log_activity(
                self.auth.current_user['username'],
                "New traveller created",
                f"Customer ID: {customer_id}, Name: {first_name} {last_name}"
            )
            
            return {
                'success': True,
                'message': 'Traveller created successfully.',
                'data': {'traveller_id': traveller_id, 'customer_id': customer_id}
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error creating traveller: {str(e)}',
                'data': None
            }
    
    def update_traveller(self, customer_id, **kwargs):
        """Update traveller information"""
        # Check permissions
        if not self.authz.check_permission('manage_travellers'):
            self.db.log_activity(
                self.auth.current_user['username'], 
                "Unauthorized traveller update attempt", 
                f"Attempted to update traveller: {customer_id}", 
                suspicious=True
            )
            return {
                'success': False,
                'message': 'Access denied. Cannot update traveller records.',
                'data': None
            }
        
        # Check if traveller exists
        traveller = self._get_traveller_by_customer_id(customer_id)
        if not traveller:
            return {
                'success': False,
                'message': 'Traveller not found.',
                'data': None
            }
        
        # Validate update fields
        updates = []
        params = []
        
        for field, value in kwargs.items():
            if value is not None and field in [
                'first_name', 'last_name', 'birthday', 'gender', 'street_name',
                'house_number', 'zip_code', 'city', 'email_address', 'mobile_phone',
                'driving_license_number'
            ]:
                # Validate specific fields
                if field == 'zip_code' and not InputValidator.validate_zip_code(value):
                    return {'success': False, 'message': 'Invalid zip code format (DDDDXX).', 'data': None}
                elif field == 'mobile_phone' and not InputValidator.validate_mobile_phone(value):
                    return {'success': False, 'message': 'Invalid mobile phone format (8 digits).', 'data': None}
                elif field == 'email_address' and not InputValidator.validate_email(value):
                    return {'success': False, 'message': 'Invalid email address format.', 'data': None}
                elif field == 'driving_license_number' and not InputValidator.validate_driving_license(value):
                    return {'success': False, 'message': 'Invalid driving license format.', 'data': None}
                elif field == 'gender' and value not in ['male', 'female']:
                    return {'success': False, 'message': 'Gender must be male or female.', 'data': None}
                elif field == 'city' and value not in self.db.get_cities():
                    return {'success': False, 'message': 'Invalid city. Must be from predefined list.', 'data': None}
                
                # Encrypt sensitive fields
                if field in ['email_address', 'street_name', 'house_number']:
                    value = self.db.encrypt_data(value)
                elif field == 'mobile_phone':
                    value = self.db.encrypt_data(f"+31-6-{value}")
                
                updates.append(f"{field} = ?")
                params.append(value)
        
        if not updates:
            return {'success': False, 'message': 'No valid updates provided.', 'data': None}
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            params.append(customer_id)
            cursor.execute(f'''
                UPDATE travellers SET {", ".join(updates)}
                WHERE customer_id = ?
            ''', params)
            
            conn.commit()
            conn.close()
            
            # Log activity
            self.db.log_activity(
                self.auth.current_user['username'],
                "Traveller updated",
                f"Customer ID: {customer_id}, Fields: {', '.join(kwargs.keys())}"
            )
            
            return {
                'success': True,
                'message': 'Traveller updated successfully.',
                'data': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error updating traveller: {str(e)}',
                'data': None
            }
    
    def delete_traveller(self, customer_id):
        """Delete a traveller record"""
        # Check permissions
        if not self.authz.check_permission('manage_travellers'):
            self.db.log_activity(
                self.auth.current_user['username'], 
                "Unauthorized traveller deletion attempt", 
                f"Attempted to delete traveller: {customer_id}", 
                suspicious=True
            )
            return {
                'success': False,
                'message': 'Access denied. Cannot delete traveller records.',
                'data': None
            }
        
        # Check if traveller exists
        traveller = self._get_traveller_by_customer_id(customer_id)
        if not traveller:
            return {
                'success': False,
                'message': 'Traveller not found.',
                'data': None
            }
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM travellers WHERE customer_id = ?', (customer_id,))
            
            conn.commit()
            conn.close()
            
            # Log activity
            self.db.log_activity(
                self.auth.current_user['username'],
                "Traveller deleted",
                f"Customer ID: {customer_id}, Name: {traveller['first_name']} {traveller['last_name']}"
            )
            
            return {
                'success': True,
                'message': 'Traveller deleted successfully.',
                'data': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error deleting traveller: {str(e)}',
                'data': None
            }
    
    def search_travellers(self, search_term):
        """Search travellers by name, customer ID, or partial keys"""
        # Check permissions
        if not self.authz.check_permission('search_travellers'):
            return {
                'success': False,
                'message': 'Access denied. Cannot search travellers.',
                'data': None
            }
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Search by customer ID or name
            search_pattern = f'%{search_term.lower()}%'
            cursor.execute('''
                SELECT customer_id, first_name, last_name, birthday, gender, 
                       zip_code, city, registration_date
                FROM travellers
                WHERE customer_id LIKE ? OR 
                      LOWER(first_name) LIKE ? OR 
                      LOWER(last_name) LIKE ?
                ORDER BY last_name, first_name
            ''', (search_pattern, search_pattern, search_pattern))
            
            travellers = cursor.fetchall()
            conn.close()
            
            traveller_list = []
            for traveller in travellers:
                traveller_list.append({
                    'customer_id': traveller[0],
                    'first_name': traveller[1],
                    'last_name': traveller[2],
                    'birthday': traveller[3],
                    'gender': traveller[4],
                    'zip_code': traveller[5],
                    'city': traveller[6],
                    'registration_date': traveller[7]
                })
            
            return {
                'success': True,
                'message': f'Found {len(traveller_list)} travellers matching "{search_term}".',
                'data': traveller_list
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error searching travellers: {str(e)}',
                'data': None
            }
    
    def get_traveller_details(self, customer_id):
        """Get detailed traveller information"""
        if not self.authz.check_permission('search_travellers'):
            return {
                'success': False,
                'message': 'Access denied. Cannot view traveller details.',
                'data': None
            }
        
        traveller = self._get_traveller_by_customer_id(customer_id, decrypt=True)
        if not traveller:
            return {
                'success': False,
                'message': 'Traveller not found.',
                'data': None
            }
        
        return {
            'success': True,
            'message': 'Traveller details retrieved.',
            'data': traveller
        }
    
    def _validate_traveller_input(self, first_name, last_name, birthday, gender, street_name,
                                house_number, zip_code, city, email_address, mobile_phone,
                                driving_license_number):
        """Validate traveller input data"""
        # Required fields
        if not all([first_name, last_name, birthday, gender, street_name, house_number,
                   zip_code, city, email_address, mobile_phone, driving_license_number]):
            return {'success': False, 'message': 'All fields are required.', 'data': None}
        
        # Format validations
        if not InputValidator.validate_zip_code(zip_code):
            return {'success': False, 'message': 'Invalid zip code format (DDDDXX).', 'data': None}
        
        if not InputValidator.validate_mobile_phone(mobile_phone):
            return {'success': False, 'message': 'Invalid mobile phone format (8 digits).', 'data': None}
        
        if not InputValidator.validate_email(email_address):
            return {'success': False, 'message': 'Invalid email address format.', 'data': None}
        
        if not InputValidator.validate_driving_license(driving_license_number):
            return {'success': False, 'message': 'Invalid driving license format.', 'data': None}
        
        if gender not in ['male', 'female']:
            return {'success': False, 'message': 'Gender must be male or female.', 'data': None}
        
        if city not in self.db.get_cities():
            return {'success': False, 'message': 'Invalid city. Must be from predefined list.', 'data': None}
        
        # Date validation
        try:
            datetime.strptime(birthday, '%Y-%m-%d')
        except ValueError:
            return {'success': False, 'message': 'Invalid birthday format (YYYY-MM-DD).', 'data': None}
        
        return {'success': True, 'message': 'Validation passed.', 'data': None}
    
    def _check_traveller_duplicates(self, email_address, driving_license_number):
        """Check for duplicate email or driving license"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check driving license (not encrypted)
        license_count = cursor.execute(
            'SELECT COUNT(*) FROM travellers WHERE driving_license_number = ?',
            (driving_license_number,)
        ).fetchone()[0]
        
        if license_count > 0:
            conn.close()
            return {'success': False, 'message': 'Driving license number already exists.', 'data': None}
        
        # Check email (need to encrypt and compare)
        encrypted_email = self.db.encrypt_data(email_address)
        email_count = cursor.execute(
            'SELECT COUNT(*) FROM travellers WHERE email_address = ?',
            (encrypted_email,)
        ).fetchone()[0]
        
        conn.close()
        
        if email_count > 0:
            return {'success': False, 'message': 'Email address already exists.', 'data': None}
        
        return {'success': True, 'message': 'No duplicates found.', 'data': None}
    
    def _get_traveller_by_customer_id(self, customer_id, decrypt=False):
        """Get traveller by customer ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM travellers WHERE customer_id = ?', (customer_id,))
        traveller = cursor.fetchone()
        conn.close()
        
        if traveller:
            result = {
                'id': traveller[0],
                'customer_id': traveller[1],
                'first_name': traveller[2],
                'last_name': traveller[3],
                'birthday': traveller[4],
                'gender': traveller[5],
                'street_name': traveller[6] if not decrypt else self.db.decrypt_data(traveller[6]),
                'house_number': traveller[7] if not decrypt else self.db.decrypt_data(traveller[7]),
                'zip_code': traveller[8],
                'city': traveller[9],
                'email_address': traveller[10] if not decrypt else self.db.decrypt_data(traveller[10]),
                'mobile_phone': traveller[11] if not decrypt else self.db.decrypt_data(traveller[11]),
                'driving_license_number': traveller[12],
                'registration_date': traveller[13],
                'created_by': traveller[14]
            }
            return result
        return None


if __name__ == "__main__":
    # Test traveller management
    from auth_manager import SessionManager
    
    # Create session and login as super admin
    session = SessionManager()
    login_result = session.auth.login("super_admin", "Admin_123?")
    
    if login_result['success']:
        traveller_mgr = TravellerManager(session)
        
        # Test creating a traveller
        print("Testing traveller creation...")
        result = traveller_mgr.create_traveller(
            first_name="John",
            last_name="Doe",
            birthday="1990-05-15",
            gender="male",
            street_name="Coolsingel",
            house_number="100",
            zip_code="3012AB",
            city="Rotterdam",
            email_address="john.doe@example.com",
            mobile_phone="12345678",
            driving_license_number="AB1234567"
        )
        print(f"Create traveller result: {result}")
        
        # Test searching
        if result['success']:
            print("\nTesting traveller search...")
            search_result = traveller_mgr.search_travellers("john")
            print(f"Search result: {search_result}")
    else:
        print("Failed to login for testing")