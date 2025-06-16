# 🛵 Urban Mobility Backend System

A secure, console-based backend system for managing shared electric scooters across the Rotterdam region. Built with Python 3 and SQLite3, with a strong focus on software security best practices.

---

## 📚 Tech Stack
- Python 3
- SQLite3
- `cryptography` (for encryption)
- `hashlib` or `bcrypt` (for hashing)
- `re` (regex for input validation)

---

## 📁 Project Structure

```
src/
├── um_members.py               # Main entry point
├── db_handler.py               # DB setup and queries
├── auth.py                     # Authentication and access control
├── encryption.py               # Symmetric encryption logic
├── validation.py               # Input validation
├── logging_handler.py          # Encrypted logging
├── backup_handler.py           # Backup and restore system
├── utils.py                    # Common utility functions
├── data/
│   └── urban_mobility.db       # Encrypted SQLite DB
├── logs/
│   └── logs.enc                # Encrypted logs
```

---

## 👥 User Roles

| Role              | Description |
|-------------------|-------------|
| Super Admin       | Hardcoded login. Can manage everything. |
| System Admin      | Manages users, scooters, and travellers. |
| Service Engineer  | Manages scooters (limited). |

Hardcoded Super Admin:
- Username: `super_admin`
- Password: `Admin_123?`

---

## 🔐 Authentication

- Passwords hashed using a secure algorithm (e.g., bcrypt).
- **Username rules:**
  - 8–10 characters
  - Start with letter or `_`
  - Allowed: a-z, 0-9, `_`, `.`, `'`
  - Case-insensitive

- **Password rules:**
  - 12–30 characters
  - At least one lowercase, one uppercase, one digit, one special character

---

## 🧪 Input Validation

- Use whitelisting.
- Regex checks:
  - Zip Code: `DDDDXX`
  - Phone: `+31-6-DDDDDDDD`
  - Driving License: `XXDDDDDDD` or `XDDDDDDDD`
  - Email format
  - Latitude/Longitude (5 decimal places)
  - 10 predefined cities

---

## 🔐 Encryption

Encrypt sensitive fields:
- Usernames
- Emails
- Phone numbers
- Logs
- Traveller address
Use symmetric encryption (e.g., Fernet AES).

---

## 🗃️ Database Schema

- `users` – stores user data and roles
- `travellers` – stores traveller details
- `scooters` – scooter information
- `logs` – encrypted logs with timestamps
- `restore_codes` – one-time backup restore tokens

---

## ✅ Features

### Super Admin
- All privileges
- Manage all users
- Generate/revoke restore codes
- View logs
- Backup & restore

### System Admin
- All engineer actions
- Manage Service Engineers
- CRUD on Travellers and Scooters
- Backup & restore with code

### Service Engineer
- Update scooter state info
- Search scooter info
- Change own password

---

## 🔁 Backup & Restore

- Zip-based backups of the encrypted DB
- Restore requires one-time code (except for Super Admin)
- Only affected System Admin can restore

---

## 📝 Logging

- Log every action securely (encrypted logs)
- Flag suspicious events (e.g., failed logins)
- Only System Admin and Super Admin can view logs through the app

---

## 📦 Submission Requirements

Submit:
- A `.zip` named `student1_student2_student3.zip`
- Contains:
  - `um_members.pdf` with names & student numbers
  - `src/` folder with:
    - Full codebase
    - `um_members.py` as main entry

---

## 🧠 Evaluation Criteria

You will be evaluated on:
- Correctness and completeness of functionality
- Security measures
- Input validation
- Proper handling of backups and logs
- Presentation and explanation of your code