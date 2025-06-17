# um_members.py
"""
Urban Mobility Backend System
Main Entry Point

This is the main file that starts the Urban Mobility backend system.
Run this file to start the application.

Course: Analysis 8: Software Quality (INFSWQ01-A | INFSWQ21-A)
Educational Period 4 [2024-2025]

Security Features:
- Role-based access control
- Input validation and SQL injection protection
- Encrypted sensitive data storage
- Comprehensive activity logging
- Secure backup and restore system
"""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from console_interface import ConsoleInterface

def main():
    """Main application entry point"""
    try:
        # Initialize and run the console interface
        app = ConsoleInterface()
        app.run()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user.")
    except Exception as e:
        print(f"\nFatal error: {e}")
        print("Please contact system administrator.")
    finally:
        print("\nUrban Mobility Backend System - Session ended.")

if __name__ == "__main__":
    main()