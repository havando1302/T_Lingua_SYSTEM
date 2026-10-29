import sqlite3, bcrypt
conn = sqlite3.connect('backend/data/admin.db')
c = conn.cursor()
c.execute("SELECT id, username, password_hash, role, mfa_enabled FROM users")
rows = c.fetchall()
passwords = ["admin", "admin123", "Admin@123", "AdminSecure@2026", "123456", "doha123", "password", "Admin@2026"]
for r in rows:
    matched = None
    for p in passwords:
        if bcrypt.checkpw(p.encode(), r[2].encode()):
            matched = p
            break
    print(f"User: {r[1]}, Role: {r[3]}, MFA: {r[4]}, Matched Password: {matched}")
