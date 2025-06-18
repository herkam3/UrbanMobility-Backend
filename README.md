
# 🛵 Urban Mobility Backend System

A secure, console-based backend system for managing shared electric scooters across the Rotterdam region. Built with Python 3 and SQLite3, with a strong focus on software security best practices.

---

## 📚 Tech Stack

- Python 3
- SQLite3
- `cryptography` (for encryption using symmetric algorithms like Fernet)
- `bcrypt` (for secure password hashing)
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

## 👥 User Roles & Permissions

| Role              | Created By            | Permissions |
|-------------------|------------------------|-------------|
| **Super Admin**   | Hardcoded              | Full access. Create/manage System Admins, view logs, generate/revoke restore codes, full CRUD access on users/travellers/scooters. |
| **System Admin**  | Super Admin            | All Service Engineer permissions + CRUD on users, travellers, scooters. Can backup and restore with a restore code. |
| **Service Engineer** | Super Admin or System Admin | Can change own password, update scooter state, and search scooters. No ability to add/delete scooters. |

🛡️ **Note:**  
- The Super Admin credentials are hardcoded for grading purposes:  
  - **Username:** `super_admin`  
  - **Password:** `Admin_123?`  
- Travellers are **not** users of the backend system; their data is managed by admins.

---

## 🔐 Authentication & User Management

- Passwords are **hashed using bcrypt** before storing in the database.
- No plaintext or encrypted passwords are stored.
- Authentication is role-based and access is restricted per role.
- Failed login attempts are logged and suspicious activity is flagged.

### 🔏 Username Rules

- Length: 8–10 characters
- Starts with letter or underscore
- Allowed: a-z, 0–9, `_`, `.`, `'`
- Case-insensitive
- Must be unique

### 🔑 Password Rules

- Length: 12–30 characters
- At least: one lowercase, one uppercase, one digit, one special character
- Allowed special characters: `~!@#$%&_-+=\`|(){}[]:;'<>,.?/`

---

## 🧍 Traveller Data

Traveller records are managed by Super Admin or System Admin and must include the following validated and encrypted fields:

| Field               | Format |
|--------------------|--------|
| First Name         | Text |
| Last Name          | Text |
| Birthday           | Date |
| Gender             | Male or Female |
| Street Name        | Text |
| House Number       | Integer |
| Zip Code           | DDDDXX |
| City               | One of 10 predefined city names |
| Email Address      | Valid format, encrypted |
| Mobile Phone       | `+31-6-DDDDDDDD` (only DDDDDDDD entered), encrypted |
| Driving License No.| `XXDDDDDDD` or `XDDDDDDDD` |

---

## 🛴 Scooter Data

Scooter records include attributes managed based on role permissions:

| Attribute           | Format/Notes |
|---------------------|--------------|
| Brand               | Text |
| Model               | Text |
| Serial Number       | 10–17 alphanumeric characters |
| Top Speed           | km/h |
| Battery Capacity    | Wh |
| State of Charge     | % |
| Target-range SoC    | min–max range |
| Location            | GPS (latitude and longitude, 5 decimal places) |
| Out-of-service      | Boolean |
| Mileage             | km |
| Last Maintenance    | ISO 8601 (`YYYY-MM-DD`) |
| In-service date     | Auto-generated when created |

---

## 🔎 Search Functionality

- Users can search scooters and travellers using **partial matches** (e.g., "Thom", "3211", "mik").
- Search supports multiple attributes and is case-insensitive.

---

## 🧪 Input Validation

- All user input is **whitelisted** and validated using regex.
- Regex examples:
  - **Zip Code:** `\d{4}[A-Z]{2}`
  - **Phone:** `\+31-6-\d{8}`
  - **Driving License:** `([A-Z]{2}\d{7})|([A-Z]{1}\d{8})`
  - **Email:** Standard RFC-compliant pattern
  - **GPS Location:** 5 decimal places

---

## 🔐 Encryption

Symmetric encryption is used to protect sensitive data:

Encrypted Fields:
- Usernames
- Emails
- Phone numbers
- Traveller addresses
- Logs

Encrypted using **Fernet AES** (symmetric cryptography).

---

## 📝 Logging

- Logs every system action with timestamp and actor.
- Suspicious activities (e.g., failed logins, brute force attempts) are flagged.
- Upon login, System Admins and Super Admins are notified about unread suspicious logs.
- Logs are stored in encrypted format and only viewable from within the app.

---

## 🔁 Backup & Restore

- Backups are ZIP archives of the **encrypted** SQLite database.
- **System Admins** can only restore using a one-time restore code, generated by a Super Admin.
- **Super Admins** can restore any backup directly and generate or revoke restore codes.

---

## ✅ Features by Role

### Super Admin
- Full access
- Create/update/delete System Admins and Service Engineers
- Manage travellers and scooters
- Backup & restore database
- View all logs
- Generate/revoke restore codes
- Super Admin cannot change or delete their own account (as per assignment)

### System Admin
- All Service Engineer permissions
- Manage Service Engineers, travellers, and scooters
- View logs
- Backup & restore using assigned restore codes
- Update their own profile
- Delete their own account

### Service Engineer
- Update scooter status/location
- Search scooters
- Change own password

---

## 📦 Submission Requirements

Submit a `.zip` file named:
```
studentnumber1_studentnumber2_studentnumber3.zip
```

Contents:
- `um_members.pdf` – Team member names and student numbers
- `src/` – All code files
  - Must include `um_members.py` as the main entry point

📌 Do NOT include:
- Python virtual environments
- Unnecessary system files
- External libraries outside the allowed ones

---

## 🧠 Evaluation Criteria (Summary)

You will be evaluated on:

- ✅ Correct role-based authentication/authorization
- ✅ Secure password hashing
- ✅ Input validation (whitelisting)
- ✅ SQL injection protection (use of parameterized queries)
- ✅ Logging + Suspicious event detection
- ✅ Proper use of encryption
- ✅ Backup & restore system (with restore codes)
- ✅ Clear and working console UI
- ✅ Ability to present and explain your implementation

---

## 👋 Final Notes

This system was built as part of the **Software Quality course final project**. Its purpose is to demonstrate practical understanding of secure coding practices, encryption, and backend management for mobility services.

> We understand this is a simplified academic simulation. In production, many elements like the hardcoded credentials, encryption management, and role creation flow would be handled differently.
