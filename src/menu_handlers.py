# menu_handlers.py

class MenuHandlers:
    def __init__(self, console_interface):
        self.console = console_interface
        self.session = console_interface.session
        self.user_mgr = console_interface.user_mgr
        self.traveller_mgr = console_interface.traveller_mgr
        self.scooter_mgr = console_interface.scooter_mgr
    
    # ========== USER MANAGEMENT ==========
    
    def user_management_menu(self):
        """User management submenu"""
        while True:
            self.console.clear_screen()
            print("=== USER MANAGEMENT ===\n")
            print("1. Create New Service Engineer")
            print("2. List All Users")
            print("3. Search Users")
            print("4. Update User")
            print("5. Delete User")
            print("6. Reset User Password")
            print("\n0. Back to Main Menu")
            print("-" * 40)
            
            choice = input("Enter your choice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.create_user_submenu()
            elif choice == '2':
                self.list_users_submenu()
            elif choice == '3':
                self.search_users_submenu()
            elif choice == '4':
                self.update_user_submenu()
            elif choice == '5':
                self.delete_user_submenu()
            elif choice == '6':
                self.reset_password_submenu()
            else:
                print("Invalid choice.")
                input("Press Enter to continue...")
    
    def create_user_submenu(self):
        """Create new Service Engineer"""
        self.console.clear_screen()
        print("=== CREATE NEW SERVICE ENGINEER ===\n")
        
        username = input("Username (8-10 chars): ").strip()
        password = input("Password: ").strip()
        first_name = input("First Name: ").strip()
        last_name = input("Last Name: ").strip()
        
        result = self.user_mgr.create_user(username, password, 'service_engineer', first_name, last_name)
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def list_users_submenu(self):
        """List all users"""
        self.console.clear_screen()
        print("=== ALL USERS ===\n")
        
        result = self.user_mgr.list_users()
        if result['success']:
            if result['data']:
                print(f"{'Username':<15} {'Role':<20} {'Name':<25} {'Created'}")
                print("-" * 80)
                for user in result['data']:
                    role_display = user['role'].replace('_', ' ').title()
                    name = f"{user['first_name']} {user['last_name']}"
                    print(f"{user['username']:<15} {role_display:<20} {name:<25} {user['registration_date'][:10]}")
            else:
                print("No users found.")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")
    
    def search_users_submenu(self):
        """Search users"""
        self.console.clear_screen()
        print("=== SEARCH USERS ===\n")
        
        search_term = input("Enter search term (name or username): ").strip()
        if not search_term:
            print("Search term cannot be empty.")
            input("Press Enter to continue...")
            return
        
        result = self.user_mgr.search_users(search_term)
        if result['success']:
            if result['data']:
                print(f"\n{'Username':<15} {'Role':<20} {'Name':<25}")
                print("-" * 60)
                for user in result['data']:
                    role_display = user['role'].replace('_', ' ').title()
                    name = f"{user['first_name']} {user['last_name']}"
                    print(f"{user['username']:<15} {role_display:<20} {name:<25}")
            else:
                print("No users found matching your search.")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")
    
    def update_user_submenu(self):
        """Update user information"""
        self.console.clear_screen()
        print("=== UPDATE USER ===\n")
        
        username = input("Username to update: ").strip()
        if not username:
            print("Username cannot be empty.")
            input("Press Enter to continue...")
            return
        
        first_name = input("New First Name (leave empty to skip): ").strip() or None
        last_name = input("New Last Name (leave empty to skip): ").strip() or None
        
        result = self.user_mgr.update_user(username, first_name=first_name, last_name=last_name)
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def delete_user_submenu(self):
        """Delete user"""
        self.console.clear_screen()
        print("=== DELETE USER ===\n")
        
        username = input("Username to delete: ").strip()
        if not username:
            print("Username cannot be empty.")
            input("Press Enter to continue...")
            return
        
        confirm = input(f"Are you sure you want to delete user '{username}'? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            input("Press Enter to continue...")
            return
        
        result = self.user_mgr.delete_user(username)
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def reset_password_submenu(self):
        """Reset user password"""
        self.console.clear_screen()
        print("=== RESET USER PASSWORD ===\n")
        
        username = input("Username to reset password: ").strip()
        if not username:
            print("Username cannot be empty.")
            input("Press Enter to continue...")
            return
        
        result = self.user_mgr.reset_password(username)
        print(f"\n{result['message']}")
        if result['success']:
            print(f"Temporary password: {result['data']['temporary_password']}")
            print("⚠️  Please share this password securely with the user.")
        
        input("Press Enter to continue...")
    
    # ========== TRAVELLER MANAGEMENT ==========
    
    def traveller_management_menu(self):
        """Traveller management submenu"""
        while True:
            self.console.clear_screen()
            print("=== TRAVELLER MANAGEMENT ===\n")
            print("1. Register New Traveller")
            print("2. Search Travellers")
            print("3. Update Traveller")
            print("4. Delete Traveller")
            print("5. View Traveller Details")
            print("\n0. Back to Main Menu")
            print("-" * 40)
            
            choice = input("Enter your choice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.create_traveller_submenu()
            elif choice == '2':
                self.search_travellers_submenu()
            elif choice == '3':
                self.update_traveller_submenu()
            elif choice == '4':
                self.delete_traveller_submenu()
            elif choice == '5':
                self.view_traveller_details_submenu()
            else:
                print("Invalid choice.")
                input("Press Enter to continue...")
    
    def create_traveller_submenu(self):
        """Create new traveller"""
        self.console.clear_screen()
        print("=== REGISTER NEW TRAVELLER ===\n")
        
        print("Available cities:")
        cities = self.traveller_mgr.db.get_cities()
        for i, city in enumerate(cities, 1):
            print(f"{i}. {city}")
        
        print("\nEnter traveller information:")
        first_name = input("First Name: ").strip()
        last_name = input("Last Name: ").strip()
        birthday = input("Birthday (YYYY-MM-DD): ").strip()
        
        while True:
            gender = input("Gender (male/female): ").strip().lower()
            if gender in ['male', 'female']:
                break
            print("Please enter 'male' or 'female'")
        
        street_name = input("Street Name: ").strip()
        house_number = input("House Number: ").strip()
        zip_code = input("Zip Code (DDDDXX): ").strip().upper()
        
        while True:
            city = input("City: ").strip()
            if city in cities:
                break
            print(f"Please select from: {', '.join(cities)}")
        
        email_address = input("Email Address: ").strip()
        mobile_phone = input("Mobile Phone (8 digits): ").strip()
        driving_license = input("Driving License (XXDDDDDDD): ").strip().upper()
        
        result = self.traveller_mgr.create_traveller(
            first_name, last_name, birthday, gender, street_name,
            house_number, zip_code, city, email_address, mobile_phone, driving_license
        )
        
        print(f"\n{result['message']}")
        if result['success']:
            print(f"Customer ID: {result['data']['customer_id']}")
        
        input("Press Enter to continue...")
    
    def search_travellers_submenu(self):
        """Search travellers"""
        self.console.clear_screen()
        print("=== SEARCH TRAVELLERS ===\n")
        
        search_term = input("Enter search term (name or customer ID): ").strip()
        if not search_term:
            print("Search term cannot be empty.")
            input("Press Enter to continue...")
            return
        
        result = self.traveller_mgr.search_travellers(search_term)
        if result['success']:
            if result['data']:
                print(f"\n{'Customer ID':<15} {'Name':<25} {'City':<15} {'Registration'}")
                print("-" * 70)
                for traveller in result['data']:
                    name = f"{traveller['first_name']} {traveller['last_name']}"
                    print(f"{traveller['customer_id']:<15} {name:<25} {traveller['city']:<15} {traveller['registration_date'][:10]}")
            else:
                print("No travellers found matching your search.")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")
    
    def update_traveller_submenu(self):
        """Update traveller information"""
        self.console.clear_screen()
        print("=== UPDATE TRAVELLER ===\n")
        
        customer_id = input("Customer ID to update: ").strip()
        if not customer_id:
            print("Customer ID cannot be empty.")
            input("Press Enter to continue...")
            return
        
        print("Enter new information (leave empty to skip):")
        first_name = input("First Name: ").strip() or None
        last_name = input("Last Name: ").strip() or None
        email = input("Email Address: ").strip() or None
        mobile = input("Mobile Phone (8 digits): ").strip() or None
        
        updates = {}
        if first_name: updates['first_name'] = first_name
        if last_name: updates['last_name'] = last_name
        if email: updates['email_address'] = email
        if mobile: updates['mobile_phone'] = mobile
        
        if not updates:
            print("No updates provided.")
            input("Press Enter to continue...")
            return
        
        result = self.traveller_mgr.update_traveller(customer_id, **updates)
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def delete_traveller_submenu(self):
        """Delete traveller"""
        self.console.clear_screen()
        print("=== DELETE TRAVELLER ===\n")
        
        customer_id = input("Customer ID to delete: ").strip()
        if not customer_id:
            print("Customer ID cannot be empty.")
            input("Press Enter to continue...")
            return
        
        confirm = input(f"Are you sure you want to delete traveller '{customer_id}'? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            input("Press Enter to continue...")
            return
        
        result = self.traveller_mgr.delete_traveller(customer_id)
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def view_traveller_details_submenu(self):
        """View detailed traveller information"""
        self.console.clear_screen()
        print("=== TRAVELLER DETAILS ===\n")
        
        customer_id = input("Customer ID: ").strip()
        if not customer_id:
            print("Customer ID cannot be empty.")
            input("Press Enter to continue...")
            return
        
        result = self.traveller_mgr.get_traveller_details(customer_id)
        if result['success']:
            traveller = result['data']
            print(f"Customer ID: {traveller['customer_id']}")
            print(f"Name: {traveller['first_name']} {traveller['last_name']}")
            print(f"Birthday: {traveller['birthday']}")
            print(f"Gender: {traveller['gender']}")
            print(f"Address: {traveller['street_name']} {traveller['house_number']}")
            print(f"Zip/City: {traveller['zip_code']} {traveller['city']}")
            print(f"Email: {traveller['email_address']}")
            print(f"Phone: {traveller['mobile_phone']}")
            print(f"License: {traveller['driving_license_number']}")
            print(f"Registration: {traveller['registration_date']}")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")
    
    # ========== SCOOTER MANAGEMENT ==========
    
    def scooter_management_menu(self):
        """Scooter management submenu"""
        while True:
            self.console.clear_screen()
            print("=== SCOOTER MANAGEMENT ===\n")
            print("1. Add New Scooter")
            print("2. Search Scooters")
            print("3. Update Scooter")
            print("4. Delete Scooter")
            print("5. View Scooter Details")
            print("\n0. Back to Main Menu")
            print("-" * 40)
            
            choice = input("Enter your choice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.create_scooter_submenu()
            elif choice == '2':
                self.search_scooters_submenu()
            elif choice == '3':
                self.update_scooter_submenu()
            elif choice == '4':
                self.delete_scooter_submenu()
            elif choice == '5':
                self.view_scooter_details_submenu()
            else:
                print("Invalid choice.")
                input("Press Enter to continue...")
    
    def create_scooter_submenu(self):
        """Create new scooter"""
        self.console.clear_screen()
        print("=== ADD NEW SCOOTER ===\n")
        
        brand = input("Brand: ").strip()
        model = input("Model: ").strip()
        serial_number = input("Serial Number (10-17 alphanumeric): ").strip()
        
        try:
            top_speed = int(input("Top Speed (km/h): ").strip())
            battery_capacity = int(input("Battery Capacity (Wh): ").strip())
            state_of_charge = int(input("State of Charge (%): ").strip())
            target_min = int(input("Target Range SoC Min (%): ").strip())
            target_max = int(input("Target Range SoC Max (%): ").strip())
            latitude = float(input("Latitude (Rotterdam region): ").strip())
            longitude = float(input("Longitude (Rotterdam region): ").strip())
        except ValueError:
            print("Invalid numeric input.")
            input("Press Enter to continue...")
            return
        
        maintenance_date = input("Last Maintenance Date (YYYY-MM-DD, optional): ").strip()
        if not maintenance_date:
            maintenance_date = None
        
        result = self.scooter_mgr.create_scooter(
            brand, model, serial_number, top_speed, battery_capacity,
            state_of_charge, target_min, target_max, latitude, longitude, maintenance_date
        )
        
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def search_scooters_submenu(self):
        """Search scooters (used by both admin and service engineer)"""
        self.console.clear_screen()
        print("=== SEARCH SCOOTERS ===\n")
        
        search_term = input("Enter search term (serial, brand, or model): ").strip()
        if not search_term:
            print("Search term cannot be empty.")
            input("Press Enter to continue...")
            return
        
        result = self.scooter_mgr.search_scooters(search_term)
        if result['success']:
            if result['data']:
                print(f"\n{'Serial Number':<18} {'Brand':<12} {'Model':<15} {'Battery%':<10} {'Status'}")
                print("-" * 70)
                for scooter in result['data']:
                    status = "Out of Service" if scooter['out_of_service_status'] else "In Service"
                    print(f"{scooter['serial_number']:<18} {scooter['brand']:<12} {scooter['model']:<15} {scooter['state_of_charge']:<10} {status}")
            else:
                print("No scooters found matching your search.")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")
    
    def search_scooters_menu(self):
        """Search scooters menu (for Service Engineers)"""
        self.search_scooters_submenu()
    
    def update_scooter_submenu(self):
        """Update scooter information"""
        self.console.clear_screen()
        print("=== UPDATE SCOOTER ===\n")
        
        serial = input("Serial Number: ").strip()
        if not serial:
            print("Serial number cannot be empty.")
            input("Press Enter to continue...")
            return
        
        print("Enter new information (leave empty to skip):")
        try:
            soc_input = input("State of Charge (%): ").strip()
            soc = int(soc_input) if soc_input else None
            
            lat_input = input("Latitude: ").strip()
            lat = float(lat_input) if lat_input else None
            
            lon_input = input("Longitude: ").strip()
            lon = float(lon_input) if lon_input else None
            
            service_input = input("Out of service? (y/n): ").strip().lower()
            out_of_service = 1 if service_input == 'y' else 0 if service_input == 'n' else None
        except ValueError:
            print("Invalid numeric input.")
            input("Press Enter to continue...")
            return
        
        updates = {}
        if soc is not None: updates['state_of_charge'] = soc
        if lat is not None: updates['latitude'] = lat
        if lon is not None: updates['longitude'] = lon
        if out_of_service is not None: updates['out_of_service_status'] = out_of_service
        
        if not updates:
            print("No updates provided.")
            input("Press Enter to continue...")
            return
        
        result = self.scooter_mgr.update_scooter(serial, **updates)
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def update_scooter_menu(self):
        """Update scooter menu (for Service Engineers)"""
        self.update_scooter_submenu()
    
    def delete_scooter_submenu(self):
        """Delete scooter"""
        self.console.clear_screen()
        print("=== DELETE SCOOTER ===\n")
        
        serial = input("Serial Number to delete: ").strip()
        if not serial:
            print("Serial number cannot be empty.")
            input("Press Enter to continue...")
            return
        
        confirm = input(f"Are you sure you want to delete scooter '{serial}'? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            input("Press Enter to continue...")
            return
        
        result = self.scooter_mgr.delete_scooter(serial)
        print(f"\n{result['message']}")
        input("Press Enter to continue...")
    
    def view_scooter_details_submenu(self):
        """View detailed scooter information"""
        self.console.clear_screen()
        print("=== SCOOTER DETAILS ===\n")
        
        serial = input("Serial Number: ").strip()
        if not serial:
            print("Serial number cannot be empty.")
            input("Press Enter to continue...")
            return
        
        result = self.scooter_mgr.get_scooter_details(serial)
        if result['success']:
            scooter = result['data']
            print(f"Serial Number: {scooter['serial_number']}")
            print(f"Brand/Model: {scooter['brand']} {scooter['model']}")
            print(f"Top Speed: {scooter['top_speed']} km/h")
            print(f"Battery: {scooter['battery_capacity']} Wh")
            print(f"State of Charge: {scooter['state_of_charge']}%")
            print(f"Target SoC Range: {scooter['target_range_soc_min']}-{scooter['target_range_soc_max']}%")
            print(f"Location: {scooter['latitude']}, {scooter['longitude']}")
            print(f"Status: {'Out of Service' if scooter['out_of_service_status'] else 'In Service'}")
            print(f"Mileage: {scooter['mileage']} km")
            print(f"Last Maintenance: {scooter['last_maintenance_date'] or 'Not recorded'}")
            print(f"In Service Since: {scooter['in_service_date']}")
        else:
            print(f"Error: {result['message']}")
        
        input("\nPress Enter to continue...")