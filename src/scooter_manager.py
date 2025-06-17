# scooter_manager.py
from database_manager import DatabaseManager, InputValidator
from datetime import datetime

class ScooterManager:
    def __init__(self, session_manager):
        self.db = DatabaseManager()
        self.session = session_manager
        self.auth = session_manager.auth
        self.authz = session_manager.authz
    
    def create_scooter(self, brand, model, serial_number, top_speed, battery_capacity,
                      state_of_charge, target_range_soc_min, target_range_soc_max,
                      latitude, longitude, last_maintenance_date=None):
        """Create a new scooter record"""
        # Check permissions
        if not self.authz.check_permission('manage_scooters'):
            self.db.log_activity(
                self.auth.current_user['username'], 
                "Unauthorized scooter creation attempt", 
                f"Attempted to create scooter: {serial_number}", 
                suspicious=True
            )
            return {
                'success': False,
                'message': 'Access denied. Cannot create scooter records.',
                'data': None
            }
        
        # Validate inputs
        validation_result = self._validate_scooter_input(
            brand, model, serial_number, top_speed, battery_capacity,
            state_of_charge, target_range_soc_min, target_range_soc_max,
            latitude, longitude, last_maintenance_date
        )
        if not validation_result['success']:
            return validation_result
        
        # Check for duplicate serial number
        if self._serial_number_exists(serial_number):
            return {
                'success': False,
                'message': 'Serial number already exists.',
                'data': None
            }
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO scooters (
                    brand, model, serial_number, top_speed, battery_capacity,
                    state_of_charge, target_range_soc_min, target_range_soc_max,
                    latitude, longitude, out_of_service_status, mileage,
                    last_maintenance_date, in_service_date, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (brand, model, serial_number, top_speed, battery_capacity,
                  state_of_charge, target_range_soc_min, target_range_soc_max,
                  latitude, longitude, 0, 0.0, last_maintenance_date,
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  self.auth.current_user['username']))
            
            conn.commit()
            scooter_id = cursor.lastrowid
            conn.close()
            
            # Log activity
            self.db.log_activity(
                self.auth.current_user['username'],
                "New scooter created",
                f"Serial: {serial_number}, Brand: {brand}, Model: {model}"
            )
            
            return {
                'success': True,
                'message': 'Scooter created successfully.',
                'data': {'scooter_id': scooter_id, 'serial_number': serial_number}
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error creating scooter: {str(e)}',
                'data': None
            }
    
    def update_scooter(self, serial_number, **kwargs):
        """Update scooter information with role-based attribute editing"""
        # Check basic permission
        if not self.authz.check_permission('update_scooter_info'):
            self.db.log_activity(
                self.auth.current_user['username'], 
                "Unauthorized scooter update attempt", 
                f"Attempted to update scooter: {serial_number}", 
                suspicious=True
            )
            return {
                'success': False,
                'message': 'Access denied. Cannot update scooter information.',
                'data': None
            }
        
        # Check if scooter exists
        scooter = self._get_scooter_by_serial(serial_number)
        if not scooter:
            return {
                'success': False,
                'message': 'Scooter not found.',
                'data': None
            }
        
        # Validate and filter updates based on user role
        updates = []
        params = []
        
        for field, value in kwargs.items():
            if value is not None:
                # Check if user can edit this attribute
                if not self.authz.can_edit_scooter_attribute(field):
                    return {
                        'success': False,
                        'message': f'Access denied. Cannot edit {field}.',
                        'data': None
                    }
                
                # Validate field-specific values
                if field in ['state_of_charge', 'target_range_soc_min', 'target_range_soc_max']:
                    if not (0 <= value <= 100):
                        return {'success': False, 'message': f'{field} must be between 0-100%.', 'data': None}
                elif field in ['latitude', 'longitude']:
                    lat = value if field == 'latitude' else scooter['latitude']
                    lon = kwargs.get('longitude', scooter['longitude']) if field == 'latitude' else value
                    if not InputValidator.validate_coordinates(lat, lon):
                        return {'success': False, 'message': 'Invalid coordinates for Rotterdam region.', 'data': None}
                elif field == 'last_maintenance_date':
                    if not InputValidator.validate_date_iso(value):
                        return {'success': False, 'message': 'Invalid date format (YYYY-MM-DD).', 'data': None}
                elif field == 'serial_number':
                    if not InputValidator.validate_serial_number(value):
                        return {'success': False, 'message': 'Invalid serial number format.', 'data': None}
                    if value != serial_number and self._serial_number_exists(value):
                        return {'success': False, 'message': 'Serial number already exists.', 'data': None}
                
                updates.append(f"{field} = ?")
                params.append(value)
        
        if not updates:
            return {'success': False, 'message': 'No valid updates provided.', 'data': None}
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            params.append(serial_number)
            cursor.execute(f'''
                UPDATE scooters SET {", ".join(updates)}
                WHERE serial_number = ?
            ''', params)
            
            conn.commit()
            conn.close()
            
            # Log activity
            self.db.log_activity(
                self.auth.current_user['username'],
                "Scooter updated",
                f"Serial: {serial_number}, Fields: {', '.join(kwargs.keys())}"
            )
            
            return {
                'success': True,
                'message': 'Scooter updated successfully.',
                'data': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error updating scooter: {str(e)}',
                'data': None
            }
    
    def delete_scooter(self, serial_number):
        """Delete a scooter record"""
        # Check permissions
        if not self.authz.check_permission('manage_scooters'):
            self.db.log_activity(
                self.auth.current_user['username'], 
                "Unauthorized scooter deletion attempt", 
                f"Attempted to delete scooter: {serial_number}", 
                suspicious=True
            )
            return {
                'success': False,
                'message': 'Access denied. Cannot delete scooter records.',
                'data': None
            }
        
        # Check if scooter exists
        scooter = self._get_scooter_by_serial(serial_number)
        if not scooter:
            return {
                'success': False,
                'message': 'Scooter not found.',
                'data': None
            }
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM scooters WHERE serial_number = ?', (serial_number,))
            
            conn.commit()
            conn.close()
            
            # Log activity
            self.db.log_activity(
                self.auth.current_user['username'],
                "Scooter deleted",
                f"Serial: {serial_number}, Brand: {scooter['brand']}, Model: {scooter['model']}"
            )
            
            return {
                'success': True,
                'message': 'Scooter deleted successfully.',
                'data': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error deleting scooter: {str(e)}',
                'data': None
            }
    
    def search_scooters(self, search_term):
        """Search scooters by serial number, brand, model, or partial keys"""
        # Check permissions
        if not self.authz.check_permission('search_scooters'):
            return {
                'success': False,
                'message': 'Access denied. Cannot search scooters.',
                'data': None
            }
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            search_pattern = f'%{search_term.lower()}%'
            cursor.execute('''
                SELECT serial_number, brand, model, state_of_charge, latitude, longitude,
                       out_of_service_status, mileage, in_service_date
                FROM scooters
                WHERE LOWER(serial_number) LIKE ? OR 
                      LOWER(brand) LIKE ? OR 
                      LOWER(model) LIKE ?
                ORDER BY brand, model, serial_number
            ''', (search_pattern, search_pattern, search_pattern))
            
            scooters = cursor.fetchall()
            conn.close()
            
            scooter_list = []
            for scooter in scooters:
                scooter_list.append({
                    'serial_number': scooter[0],
                    'brand': scooter[1],
                    'model': scooter[2],
                    'state_of_charge': scooter[3],
                    'latitude': scooter[4],
                    'longitude': scooter[5],
                    'out_of_service_status': bool(scooter[6]),
                    'mileage': scooter[7],
                    'in_service_date': scooter[8]
                })
            
            return {
                'success': True,
                'message': f'Found {len(scooter_list)} scooters matching "{search_term}".',
                'data': scooter_list
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error searching scooters: {str(e)}',
                'data': None
            }
    
    def get_scooter_details(self, serial_number):
        """Get detailed scooter information"""
        if not self.authz.check_permission('search_scooters'):
            return {
                'success': False,
                'message': 'Access denied. Cannot view scooter details.',
                'data': None
            }
        
        scooter = self._get_scooter_by_serial(serial_number)
        if not scooter:
            return {
                'success': False,
                'message': 'Scooter not found.',
                'data': None
            }
        
        return {
            'success': True,
            'message': 'Scooter details retrieved.',
            'data': scooter
        }
    
    def _validate_scooter_input(self, brand, model, serial_number, top_speed, battery_capacity,
                               state_of_charge, target_range_soc_min, target_range_soc_max,
                               latitude, longitude, last_maintenance_date):
        """Validate scooter input data"""
        # Required fields
        if not all([brand, model, serial_number]):
            return {'success': False, 'message': 'Brand, model, and serial number are required.', 'data': None}
        
        # Serial number format
        if not InputValidator.validate_serial_number(serial_number):
            return {'success': False, 'message': 'Invalid serial number format (10-17 alphanumeric).', 'data': None}
        
        # Numeric validations
        if not (0 <= state_of_charge <= 100):
            return {'success': False, 'message': 'State of charge must be between 0-100%.', 'data': None}
        
        if not (0 <= target_range_soc_min <= 100) or not (0 <= target_range_soc_max <= 100):
            return {'success': False, 'message': 'Target range SoC values must be between 0-100%.', 'data': None}
        
        if target_range_soc_min >= target_range_soc_max:
            return {'success': False, 'message': 'Target range SoC min must be less than max.', 'data': None}
        
        # Coordinates validation
        if not InputValidator.validate_coordinates(latitude, longitude):
            return {'success': False, 'message': 'Invalid coordinates for Rotterdam region.', 'data': None}
        
        # Date validation
        if last_maintenance_date and not InputValidator.validate_date_iso(last_maintenance_date):
            return {'success': False, 'message': 'Invalid maintenance date format (YYYY-MM-DD).', 'data': None}
        
        return {'success': True, 'message': 'Validation passed.', 'data': None}
    
    def _serial_number_exists(self, serial_number):
        """Check if serial number already exists"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        count = cursor.execute(
            'SELECT COUNT(*) FROM scooters WHERE serial_number = ?',
            (serial_number,)
        ).fetchone()[0]
        
        conn.close()
        return count > 0
    
    def _get_scooter_by_serial(self, serial_number):
        """Get scooter by serial number"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM scooters WHERE serial_number = ?', (serial_number,))
        scooter = cursor.fetchone()
        conn.close()
        
        if scooter:
            return {
                'id': scooter[0],
                'brand': scooter[1],
                'model': scooter[2],
                'serial_number': scooter[3],
                'top_speed': scooter[4],
                'battery_capacity': scooter[5],
                'state_of_charge': scooter[6],
                'target_range_soc_min': scooter[7],
                'target_range_soc_max': scooter[8],
                'latitude': scooter[9],
                'longitude': scooter[10],
                'out_of_service_status': bool(scooter[11]),
                'mileage': scooter[12],
                'last_maintenance_date': scooter[13],
                'in_service_date': scooter[14],
                'created_by': scooter[15]
            }
        return None


if __name__ == "__main__":
    # Test scooter management
    from auth_manager import SessionManager
    
    # Create session and login as super admin
    session = SessionManager()
    login_result = session.auth.login("super_admin", "Admin_123?")
    
    if login_result['success']:
        scooter_mgr = ScooterManager(session)
        
        # Test creating a scooter
        print("Testing scooter creation...")
        result = scooter_mgr.create_scooter(
            brand="Segway",
            model="Ninebot ES2",
            serial_number="SG123456789AB",
            top_speed=25,
            battery_capacity=5100,
            state_of_charge=85,
            target_range_soc_min=20,
            target_range_soc_max=90,
            latitude=51.9225,
            longitude=4.47917,
            last_maintenance_date="2025-06-01"
        )
        print(f"Create scooter result: {result}")
        
        # Test searching
        if result['success']:
            print("\nTesting scooter search...")
            search_result = scooter_mgr.search_scooters("segway")
            print(f"Search result: {search_result}")
            
            # Test scooter update
            print("\nTesting scooter update...")
            update_result = scooter_mgr.update_scooter(
                "SG123456789AB",
                state_of_charge=75,
                latitude=51.9230,
                longitude=4.47920
            )
            print(f"Update result: {update_result}")
    else:
        print("Failed to login for testing")