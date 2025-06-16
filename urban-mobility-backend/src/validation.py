import re

def validate_username(username):
    """
    Username rules:
    - 8–10 characters
    - Start with letter or '_'
    - Allowed: a-z, 0-9, '_', '.', "'"
    - Case-insensitive: always convert to lowercase before storing/comparing
    """
    username = username.lower()
    pattern = r"^[a-z_][a-z0-9_.']{7,9}$"
    return bool(re.match(pattern, username))

def validate_password(password):
    """
    Password rules:
    - 12–30 characters
    - At least one lowercase, one uppercase, one digit, one special character
    """
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{12,30}$'
    return bool(re.match(pattern, password))

def validate_zip_code(zip_code):
    """Dutch zip code: 4 digits + 2 uppercase letters (no space)"""
    pattern = r'^\d{4}[A-Z]{2}$'
    return bool(re.match(pattern, zip_code))

def validate_phone(phone):
    """Dutch mobile: +31-6-XXXXXXXX"""
    pattern = r'^\+31-6-\d{8}$'
    return bool(re.match(pattern, phone))

def validate_driving_license(license_number):
    """Driving license: XXDDDDDDD or XDDDDDDDD"""
    pattern = r'^(?:[A-Z]{2}\d{7}|[A-Z]\d{8})$'
    return bool(re.match(pattern, license_number))

def validate_email(email):
    """Basic email format validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_latitude(latitude):
    """Latitude: -90 to 90, 5 decimal places"""
    try:
        lat = float(latitude)
        if not (-90 <= lat <= 90):
            return False
        # Check for 5 decimal places
        return re.match(r'^-?\d{1,2}\.\d{5}$', str(latitude)) is not None
    except ValueError:
        return False

def validate_longitude(longitude):
    """Longitude: -180 to 180, 5 decimal places"""
    try:
        lon = float(longitude)
        if not (-180 <= lon <= 180):
            return False
        # Check for 5 decimal places
        return re.match(r'^-?\d{1,3}\.\d{5}$', str(longitude)) is not None
    except ValueError:
        return False

def validate_city(city, predefined_cities):
    """City must be in the predefined whitelist."""
    return city in predefined_cities

# Predefined cities for validation (whitelist)
PREDEFINED_CITIES = [
    "Rotterdam", "Amsterdam", "The Hague", "Utrecht", "Eindhoven",
    "Groningen", "Breda", "Nijmegen", "Haarlem", "Tilburg"
]