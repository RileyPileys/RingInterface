import sqlite3

# Connect to the database
conn = sqlite3.connect('ring_internal_db.db')
c = conn.cursor()

# Reset the admin password and unlock the account
c.execute('''UPDATE users 
             SET password = ?, login_attempts = 0, is_locked = 0 
             WHERE id = ?''', ('new_admin_password', '000'))

conn.commit()
conn.close()

print("Admin account unlocked and password reset.")
