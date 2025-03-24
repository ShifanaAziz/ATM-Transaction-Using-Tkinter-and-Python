import tkinter as tk
from tkinter import messagebox
from tkinter import ttk  # Import ttk for Treeview widget
import sqlite3
import hashlib
from datetime import datetime

# Database setup
conn = sqlite3.connect('atm.db')
c = conn.cursor()

# Create necessary tables if they don't exist
c.execute('''CREATE TABLE IF NOT EXISTS users (
            account_number TEXT PRIMARY KEY,
            pin TEXT,
            balance REAL
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS transactions (
            account_number TEXT,
            transaction_type TEXT,
            amount REAL,
            date TIMESTAMP
            )''')

conn.commit()

# Function to hash the pin
def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()

# Function to register a new user (for demo purposes)
def register_user(account_number, pin, initial_balance=0):
    hashed_pin = hash_pin(pin)
    c.execute("INSERT INTO users (account_number, pin, balance) VALUES (?, ?, ?)",
              (account_number, hashed_pin, initial_balance))
    conn.commit()

# Insert a sample user if table is empty
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    register_user('123456', '1234', 1000.0)

# Functions to handle ATM logic
def login():
    account_number = entry_account.get()
    pin = entry_pin.get()
    hashed_pin = hash_pin(pin)
    
    # Check if account exists and pin matches
    c.execute("SELECT * FROM users WHERE account_number = ? AND pin = ?", (account_number, hashed_pin))
    user = c.fetchone()
    
    if user:
        messagebox.showinfo("Login Success", "Login Successful!")
        open_account_window(account_number)
    else:
        messagebox.showerror("Login Failed", "Incorrect account number or pin!")

def open_account_window(account_number):
    # Main account window
    account_window = tk.Toplevel(root)
    account_window.title("ATM - Account")
    
    def show_balance():
        c.execute("SELECT balance FROM users WHERE account_number = ?", (account_number,))
        balance = c.fetchone()[0]
        messagebox.showinfo("Balance", f"Your balance is: ₹{balance}")

    def withdraw():
        amount = float(entry_amount.get())
        if amount <= 0:
            messagebox.showerror("Invalid Amount", "Amount must be greater than 0.")
            return

        c.execute("SELECT balance FROM users WHERE account_number = ?", (account_number,))
        balance = c.fetchone()[0]
        
        if amount > balance:
            messagebox.showerror("Insufficient Funds", "You do not have enough balance!")
        else:
            new_balance = balance - amount
            c.execute("UPDATE users SET balance = ? WHERE account_number = ?", (new_balance, account_number))
            # Log the transaction with formatted date (without microseconds)
            formatted_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute("INSERT INTO transactions (account_number, transaction_type, amount, date) VALUES (?, ?, ?, ?)",
                      (account_number, 'withdrawal', amount, formatted_date))
            conn.commit()
            messagebox.showinfo("Withdrawal Success", f"Successfully withdrew ₹{amount}. New balance: ₹{new_balance}")
            entry_amount.delete(0, tk.END)  # Clear the amount field

    def deposit():
        amount = float(entry_amount.get())
        if amount <= 0:
            messagebox.showerror("Invalid Amount", "Amount must be greater than 0.")
            return
        
        c.execute("SELECT balance FROM users WHERE account_number = ?", (account_number,))
        balance = c.fetchone()[0]
        new_balance = balance + amount
        c.execute("UPDATE users SET balance = ? WHERE account_number = ?", (new_balance, account_number))
        # Log the transaction with formatted date (without microseconds)
        formatted_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("INSERT INTO transactions (account_number, transaction_type, amount, date) VALUES (?, ?, ?, ?)",
                  (account_number, 'deposit', amount, formatted_date))
        conn.commit()
        messagebox.showinfo("Deposit Success", f"Successfully deposited ₹{amount}. New balance: ₹{new_balance}")
        entry_amount.delete(0, tk.END)  # Clear the amount field

    def show_transaction_history():
        # Create new window to show transaction history in a table
        history_window = tk.Toplevel(account_window)
        history_window.title("Transaction History")

        # Create a Style object to customize the Treeview appearance
        style = ttk.Style()
        style.configure("Treeview",
                        font=("Arial", 12),  # Increase font size to increase row height
                        rowheight=35)  # Adjust the row height by setting the rowheight

        # Create Treeview widget with adjusted row height
        tree = ttk.Treeview(history_window, columns=("Type", "Amount", "Date"), show="headings", height=15)

        tree.heading("Type", text="Transaction Type")
        tree.heading("Amount", text="Amount (₹)")
        tree.heading("Date", text="Date")
        
        tree.column("Type", width=250)  # Increased the width for better visibility
        tree.column("Amount", width=150)
        tree.column("Date", width=350)

        # Query the transactions for the account
        c.execute("SELECT transaction_type, amount, date FROM transactions WHERE account_number = ? ORDER BY date DESC", (account_number,))
        transactions = c.fetchall()

        # Insert each transaction into the Treeview
        for transaction in transactions:
            tree.insert("", "end", values=(transaction[0], f"₹{transaction[1]}", transaction[2]))

        # Add scrollbars
        scrollbar = ttk.Scrollbar(history_window, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        tree.pack(pady=20, padx=20)

    # Account balance
    label_account_balance = tk.Label(account_window, text="ATM Account", font=("Helvetica", 14))
    label_account_balance.pack(pady=10)
    
    btn_balance = tk.Button(account_window, text="Check Balance", width=20, command=show_balance)
    btn_balance.pack(pady=10)

    # Transaction History Button
    btn_history = tk.Button(account_window, text="Transaction History", width=20, command=show_transaction_history)
    btn_history.pack(pady=10)

    # Amount input field
    label_amount = tk.Label(account_window, text="Amount:")
    label_amount.pack(pady=5)
    entry_amount = tk.Entry(account_window)
    entry_amount.pack(pady=5)

    # Withdraw Button
    btn_withdraw = tk.Button(account_window, text="Withdraw", width=20, command=withdraw)
    btn_withdraw.pack(pady=10)

    # Deposit Button
    btn_deposit = tk.Button(account_window, text="Deposit", width=20, command=deposit)
    btn_deposit.pack(pady=10)

    # Exit Button
    btn_exit = tk.Button(account_window, text="Logout", width=20, command=account_window.destroy)
    btn_exit.pack(pady=10)

def register():
    # Register new user window
    register_window = tk.Toplevel(root)
    register_window.title("Register New User")

    label_account = tk.Label(register_window, text="New Account Number:")
    label_account.pack(pady=10)
    entry_account = tk.Entry(register_window)
    entry_account.pack(pady=5)

    label_pin = tk.Label(register_window, text="New PIN:")
    label_pin.pack(pady=10)
    entry_pin = tk.Entry(register_window, show="*")
    entry_pin.pack(pady=5)

    label_balance = tk.Label(register_window, text="Initial Balance:")
    label_balance.pack(pady=10)
    entry_balance = tk.Entry(register_window)
    entry_balance.pack(pady=5)

    def save_registration():
        account_number = entry_account.get()
        pin = entry_pin.get()
        initial_balance = float(entry_balance.get())

        # Ensure that the account number doesn't already exist
        c.execute("SELECT * FROM users WHERE account_number = ?", (account_number,))
        existing_user = c.fetchone()
        if existing_user:
            messagebox.showerror("Registration Failed", "Account number already exists!")
        else:
            register_user(account_number, pin, initial_balance)
            messagebox.showinfo("Registration Success", f"Account {account_number} created successfully!")
            register_window.destroy()

    btn_register = tk.Button(register_window, text="Register", command=save_registration)
    btn_register.pack(pady=20)

# Main window
root = tk.Tk()
root.title("ATM Application")

# Account number entry
label_account = tk.Label(root, text="Account Number:")
label_account.pack(pady=10)
entry_account = tk.Entry(root)
entry_account.pack(pady=5)

# Pin entry
label_pin = tk.Label(root, text="PIN:")
label_pin.pack(pady=10)
entry_pin = tk.Entry(root, show="*")
entry_pin.pack(pady=5)

# Login button
btn_login = tk.Button(root, text="Login", width=20, command=login)
btn_login.pack(pady=20)

# Register button
btn_register = tk.Button(root, text="Register New User", width=20, command=register)
btn_register.pack(pady=10)

root.mainloop()

# Close the database connection when the program ends
conn.close()
