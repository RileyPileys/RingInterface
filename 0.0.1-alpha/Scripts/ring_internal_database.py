import sqlite3
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import simpledialog
from datetime import datetime, timedelta
import pandas as pd

# Main Menu Class
class MainMenu:
    def __init__(self, master, user_id, is_admin):
        self.master = master
        self.user_id = user_id
        self.is_admin = is_admin
        self.master.title("Main Menu")

        # Handle the close event to ensure the app exits
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

        self.label = tk.Label(master, text=f"Welcome {user_id} to the Main Menu")
        self.label.pack()

        self.view_mode_button = tk.Button(master, text="View Mode", command=self.open_view_mode)
        self.view_mode_button.pack()

        self.edit_mode_button = tk.Button(master, text="Edit Mode", command=self.open_edit_mode)
        self.edit_mode_button.pack()

        self.schedule_mode_button = tk.Button(master, text="Schedule Mode", command=self.open_schedule_mode)
        self.schedule_mode_button.pack()

        # Only show the admin mode if the user is an admin
        if self.is_admin:
            self.admin_mode_button = tk.Button(master, text="Admin Mode", command=self.open_admin_mode)
            self.admin_mode_button.pack()

    def open_view_mode(self):
        self.master.withdraw()  # Close the main menu
        view_mode_screen = tk.Tk()  # Open new View Mode screen
        ViewModeScreen(view_mode_screen, self.user_id)

    def open_edit_mode(self):
        self.master.withdraw()  # Close the main menu
        edit_mode_screen = tk.Tk()  # Open new Edit Mode screen
        EditModeScreen(edit_mode_screen, self.user_id)

    def open_schedule_mode(self):
        self.master.withdraw()  # Close the main menu
        schedule_mode_screen = tk.Tk()  # Open new Schedule Mode screen
        ScheduleModeScreen(schedule_mode_screen, self.user_id)

    def open_admin_mode(self):
        self.master.withdraw()  # Close the main menu
        admin_screen = tk.Tk()  # Open new Admin screen
        AdminScreen(admin_screen, self.user_id)

        # Force the update of all widgets
        self.master.update_idletasks()  # Ensures the window and widgets are properly updated
        
    def on_close(self):
        # Close the root window when the main menu is closed
        root.quit()
        
# Initialize the database
def init_db():
    conn = sqlite3.connect('ring_internal_db.db')
    c = conn.cursor()

    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY,
                    name TEXT, age INTEGER, gender TEXT, priority TEXT,
                    risk_level TEXT, location TEXT, lives_alone TEXT,
                    date_of_commission TEXT, deadline TEXT, completed TEXT,
                    preferred_location TEXT, commissioner_name TEXT,
                    cost REAL, sold_staff TEXT, assigned_staff TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS commissioners (
                    id INTEGER PRIMARY KEY,
                    name TEXT, age INTEGER, gender TEXT, location TEXT, 
                    total_spent REAL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS staff (
                    id INTEGER PRIMARY KEY, name TEXT, age INTEGER, 
                    birthday TEXT, gender TEXT, location TEXT, 
                    total_sales REAL, tasks TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                    customer_id INTEGER, cost REAL, 
                    date_of_commission TEXT, delivery_date TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY, name TEXT, password TEXT, 
                    is_admin INTEGER, login_attempts INTEGER DEFAULT 0,
                    is_locked INTEGER DEFAULT 0)''')

    # Insert initial administrator account
    c.execute('''INSERT OR IGNORE INTO users (id, name, password, is_admin, login_attempts, is_locked)
                 VALUES (000, 'Testing', 'admin', 1, 0, 0)''')

    conn.commit()
    conn.close()

# Reminder popup
def show_reminder():
    reminder_text = ("Reminder: The 'Location' field is for the city/town the customer lives in. "
                     "'Preferred Location' is where the commissioner would like the task to be completed.")
    messagebox.showinfo("Reminder", reminder_text)

# Login system
class LoginScreen:
    def __init__(self, master):
        self.master = master
        self.master.title("Login")

        self.label = tk.Label(master, text="Enter User ID and Password")
        self.label.pack()

        self.id_label = tk.Label(master, text="User ID:")
        self.id_label.pack()
        self.id_entry = tk.Entry(master)
        self.id_entry.pack()

        self.password_label = tk.Label(master, text="Password:")
        self.password_label.pack()
        self.password_entry = tk.Entry(master, show="*")
        self.password_entry.pack()

        self.login_button = tk.Button(master, text="Login", command=self.login)
        self.login_button.pack()

        self.message_label = tk.Label(master, text="")
        self.message_label.pack()

    def login(self):
        user_id = self.id_entry.get()
        password = self.password_entry.get()

        conn = sqlite3.connect('ring_internal_db.db')
        c = conn.cursor()

        # Check if user exists and is locked
        c.execute("SELECT password, login_attempts, is_locked, is_admin FROM users WHERE id=?", (user_id,))
        user = c.fetchone()

        if user:
            if user[2] == 1:  # Check if locked
                self.message_label.config(text="Account is locked. Contact admin.")
                return
            elif user[0] == password:  # Successful login
                c.execute("UPDATE users SET login_attempts=0 WHERE id=?", (user_id,))
                conn.commit()
                if user[3] == 1:  # Admin login
                    self.master.withdraw()
                    admin_screen = tk.Tk()
                    AdminScreen(admin_screen, user_id)
                else:  # Staff login
                    self.master.withdraw()
                    staff_screen = tk.Tk()
                    StaffScreen(staff_screen, user_id)
            else:  # Wrong password
                attempts = user[1] + 1
                c.execute("UPDATE users SET login_attempts=? WHERE id=?", (attempts, user_id))
                conn.commit()
                if attempts >= 3:
                    c.execute("UPDATE users SET is_locked=1 WHERE id=?", (user_id,))
                    conn.commit()
                    self.message_label.config(text="Account locked due to 3 failed attempts.")
                else:
                    self.message_label.config(text=f"Incorrect password. {3 - attempts} attempts left.")
        else:
            self.message_label.config(text="User ID not found.")

        self.master.withdraw()  # Close the login window
        conn.close()

    def open_main_menu(self, user_id, is_admin):
        main_menu_screen = tk.Tk()  # Create a new main application window
        MainMenu(main_menu_screen, user_id, is_admin)
        main_menu_screen.mainloop()

# View mode for staff (view customer/commissioner data)
class ViewModeScreen:
    def __init__(self, master, user_id):
        self.master = master
        self.user_id = user_id
        self.master.title("View Mode")

        self.label = tk.Label(master, text="View Customer and Commissioner Information")
        self.label.pack()

        self.view_button = tk.Button(master, text="View Customer Data", command=self.view_customer_data)
        self.view_button.pack()

        self.view_commissioner_button = tk.Button(master, text="View Commissioner Data", command=self.view_commissioner_data)
        self.view_commissioner_button.pack()

        self.back_button = tk.Button(master, text="Back to Main Menu", command=self.back_to_menu)
        self.back_button.pack()

    def view_customer_data(self):
        conn = sqlite3.connect('ring_internal_db.db')
        c = conn.cursor()
        c.execute("SELECT * FROM customers")
        data = c.fetchall()
        df = pd.DataFrame(data, columns=["ID", "Name", "Age", "Gender", "Priority", "Risk Level", 
                                         "Location", "Lives Alone", "Date of Commission", "Deadline", 
                                         "Completed", "Preferred Location", "Commissioner Name", "Cost", 
                                         "Sold Staff", "Assigned Staff"])
        messagebox.showinfo("Customer Data", df.to_string())
        conn.close()

    def view_commissioner_data(self):
        conn = sqlite3.connect('ring_internal_db.db')
        c = conn.cursor()
        c.execute("SELECT * FROM commissioners")
        data = c.fetchall()
        df = pd.DataFrame(data, columns=["ID", "Name", "Age", "Gender", "Location", "Total Spent"])
        messagebox.showinfo("Commissioner Data", df.to_string())
        conn.close()

    def back_to_menu(self):
        self.master.withdraw()  # Close the current window
        main_menu_screen = tk.main_menu_screen = tk.Toplevel(self.master)  # Create a new main menu window using Toplevel  # Show the hidden main menu

# Edit mode for staff (edit customer data)
class EditModeScreen:
    def __init__(self, master, user_id):
        self.master = master
        self.user_id = user_id
        self.master.title("Edit Mode")

        self.label = tk.Label(master, text="Edit Customer Information")
        self.label.pack()

        self.edit_button = tk.Button(master, text="Edit Customer Data", command=self.edit_customer_data)
        self.edit_button.pack()

        self.back_button = tk.Button(master, text="Back to Main Menu", command=self.back_to_menu)
        self.back_button.pack()

    def edit_customer_data(self):
        # Implement editing functionality
        # For simplicity, let's just allow updating the customer's location
        customer_id = simpledialog.askinteger("Customer ID", "Enter Customer ID to edit:")
        new_location = simpledialog.askstring("New Location", "Enter new location for the customer:")
        conn = sqlite3.connect('ring_internal_db.db')
        c = conn.cursor()
        c.execute("UPDATE customers SET location=? WHERE id=?", (new_location, customer_id))
        conn.commit()
        messagebox.showinfo("Success", f"Customer {customer_id}'s location updated.")
        conn.close()

    def back_to_menu(self):
        self.master.withdraw()  # Close the current window
        main_menu_screen = tk.main_menu_screen = tk.Toplevel(self.master)  # Create a new main menu window using Toplevel  # Show the hidden main menu

# Schedule mode for staff (view upcoming tasks)
class ScheduleModeScreen:
    def __init__(self, master, user_id):
        self.master = master
        self.user_id = user_id
        self.master.title("Schedule Mode")

        self.label = tk.Label(master, text="View Upcoming Tasks")
        self.label.pack()

        self.view_tasks_button = tk.Button(master, text="View Tasks Due in Next 30 Days", command=self.view_tasks)
        self.view_tasks_button.pack()

        self.back_button = tk.Button(master, text="Back to Main Menu", command=self.back_to_menu)
        self.back_button.pack()

    def view_tasks(self):
        conn = sqlite3.connect('ring_internal_db.db')
        c = conn.cursor()
        today = datetime.today()
        next_30_days = today + timedelta(days=30)
        c.execute("SELECT * FROM tasks WHERE delivery_date BETWEEN ? AND ?", 
                  (today.strftime("%Y-%m-%d"), next_30_days.strftime("%Y-%m-%d")))
        data = c.fetchall()
        df = pd.DataFrame(data, columns=["Customer ID", "Cost", "Date of Commission", "Delivery Date"])
        messagebox.showinfo("Tasks", df.to_string())
        conn.close()

    def back_to_menu(self):
        self.master.withdraw()  # Close the current window
        main_menu_screen = tk.main_menu_screen = tk.Toplevel(self.master)  # Create a new main menu window using Toplevel  # Show the hidden main menu

# Administrator mode
class AdminScreen:
    def __init__(self, master, user_id):
        self.master = master
        self.user_id = user_id
        self.master.title("Administrator Mode")

        self.label = tk.Label(master, text=f"Welcome Admin {user_id}")
        self.label.pack()

        self.view_users_button = tk.Button(master, text="View All User Accounts", command=self.view_users)
        self.view_users_button.pack()

        self.suspend_user_button = tk.Button(master, text="Suspend User Account", command=self.suspend_user)
        self.suspend_user_button.pack()

        self.unlock_user_button = tk.Button(master, text="Unlock User Account", command=self.unlock_user)
        self.unlock_user_button.pack()

        self.back_button = tk.Button(master, text="Back to Main Menu", command=self.back_to_menu)
        self.back_button.pack()

    def view_users(self):
        # Create a new window to display user accounts
        user_window = tk.Toplevel(self.master)
        user_window.title("User Accounts")

        # Create a Treeview widget to display data in table format
        columns = ("ID", "Name", "Password", "Is Admin", "Login Attempts", "Is Locked")
        tree = ttk.Treeview(user_window, columns=columns, show="headings")
        tree.pack(fill=tk.BOTH, expand=True)

        # Define headings
        for col in columns:
            tree.heading(col, text=col)

        # Fetch user data from the database
        conn = sqlite3.connect('ring_internal_db.db')
        c = conn.cursor()
        c.execute("SELECT id, name, password, is_admin, login_attempts, is_locked FROM users")
        rows = c.fetchall()

        # Insert data into the Treeview
        for row in rows:
            tree.insert("", tk.END, values=row)

        conn.close()

        # Add scrollbar for the table
        scrollbar = ttk.Scrollbar(user_window, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def suspend_user(self):
        # Ask for the User ID to suspend
        user_id = simpledialog.askinteger("Suspend User", "Enter User ID to suspend:")
        
        if user_id is None:
            return  # If canceled, do nothing
        
        conn = sqlite3.connect('ring_internal_db.db')
        c = conn.cursor()
        c.execute("UPDATE users SET is_locked=1 WHERE id=?", (user_id,))
        conn.commit()
        conn.close()
        tk.messagebox.showinfo("Success", f"User {user_id} has been suspended.")

    def unlock_user(self):
        # Ask for the User ID to unlock
        user_id = simpledialog.askinteger("Unlock User", "Enter User ID to unlock:")
        
        if user_id is None:
            return  # If canceled, do nothing
        
        conn = sqlite3.connect('ring_internal_db.db')
        c = conn.cursor()
        c.execute("UPDATE users SET is_locked=0, login_attempts=0 WHERE id=?", (user_id,))
        conn.commit()
        conn.close()
        tk.messagebox.showinfo("Success", f"User {user_id} has been unlocked.")

    def back_to_menu(self):
        self.master.withdraw()  # Close the admin window
        main_menu_screen = tk.main_menu_screen = tk.Toplevel(self.master)  # Create a new main menu window using Toplevel  # Show the hidden main menu

# Staff mode
class StaffScreen:
    def __init__(self, master, user_id):
        self.master = master
        self.user_id = user_id
        self.master.title("Staff Mode")

        self.label = tk.Label(master, text=f"Welcome Staff {user_id}")
        self.label.pack()

        self.view_mode_button = tk.Button(master, text="View Mode", command=self.open_view_mode)
        self.view_mode_button.pack()

        self.edit_mode_button = tk.Button(master, text="Edit Mode", command=self.open_edit_mode)
        self.edit_mode_button.pack()

        self.schedule_mode_button = tk.Button(master, text="Schedule Mode", command=self.open_schedule_mode)
        self.schedule_mode_button.pack()

        self.back_button = tk.Button(master, text="Logout", command=self.master.withdraw)
        self.back_button.pack()

    def open_view_mode(self):
        view_mode_screen = tk.Toplevel(self.master)
        ViewModeScreen(view_mode_screen, self.user_id)

    def open_edit_mode(self):
        edit_mode_screen = tk.Toplevel(self.master)
        EditModeScreen(edit_mode_screen, self.user_id)

    def open_schedule_mode(self):
        schedule_mode_screen = tk.Toplevel(self.master)
        ScheduleModeScreen(schedule_mode_screen, self.user_id)

# Main App
if __name__ == '__main__':
    init_db()
    show_reminder()
    root = tk.Tk()
    app = LoginScreen(root)
    root.mainloop()
