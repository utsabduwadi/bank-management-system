import streamlit as st
import os
import hashlib
import json
from datetime import datetime

# File to store user data persistently
USER_DATA_FILE = "bank_users.json"

# Function to hash passwords for security
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Load user data from a file
def load_users():
    if not os.path.exists(USER_DATA_FILE):  # Check if file exists before loading
        return {}
    with open(USER_DATA_FILE, "r") as file:
        return json.load(file)

# Save user data to a file
def save_users(users):
    with open(USER_DATA_FILE, "w") as file:
        json.dump(users, file, indent=4)

# Function to reset a user's password
def forget_password(username, new_password):
    users = load_users()
    if username not in users:
        return False, "User not found."
    users[username]["password"] = hash_password(new_password)
    save_users(users)
    return True, "Password reset successful!"

# Perform a transaction between two users
def perform_transaction(sender, recipient, amount):
    users = load_users()
    if sender not in users or recipient not in users:
        return False, "Sender or recipient not found."
    if users[sender]["balance"] < amount:
        return False, "Insufficient funds."
    
    users[sender]["balance"] -= amount  # Deduct from sender
    users[recipient]["balance"] += amount  # Add to recipient
    transaction_time = str(datetime.now())
    
    # Record transaction history
    users[sender]["transactions"].append({"type": "Sent", "to": recipient, "amount": amount, "time": transaction_time})
    users[recipient]["transactions"].append({"type": "Received", "from": sender, "amount": amount, "time": transaction_time})
    
    save_users(users)
    return True, f"Transferred {amount} to {recipient} successfully."

# Function to create a new user account
def signup(username, password, account_type):
    users = load_users()
    if username in users:
        return False, "Username already exists."
    
    users[username] = {
        "password": hash_password(password),
        "account_type": account_type,
        "balance": 0.0,
        "transactions": []
    }
    save_users(users)
    return True, "Signup successful! You can now log in."

# Change password function
def change_password(username, current_password, new_password):
    users = load_users()
    if username not in users:
        return False, "User not found."
    if users[username]["password"] == hash_password(current_password):
        users[username]["password"] = hash_password(new_password)
        save_users(users)
        return True, "Password changed successfully."
    return False, "Incorrect current password."

# Streamlit app setup
st.title("Banking Management System")

# Session state for login management
if "username" not in st.session_state:
    st.session_state.username = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# User login interface
if st.session_state.username is None:
    st.sidebar.title("Login Options")
    user_type = st.sidebar.radio("Login as:", ["Customer", "Admin"])

    if user_type == "Customer":
        st.subheader("Customer Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            users = load_users()
            if username in users and users[username]["password"] == hash_password(password):
                st.session_state.username = username
                st.session_state.is_admin = False
                st.success("Login successful!")
            else:
                st.error("Invalid username or password.")
        
        st.markdown("---")
        st.subheader("Signup")
        signup_username = st.text_input("New Username")
        signup_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        account_type = st.selectbox("Account Type", ["Saving", "Current"])
        
        if st.button("Signup"):
            if signup_password == confirm_password:
                success, message = signup(signup_username, signup_password, account_type)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.error("Passwords do not match.")
    
    elif user_type == "Admin":
        st.subheader("Admin Login")
        username = st.text_input("Admin Username")
        password = st.text_input("Admin Password", type="password")
        if st.button("Login"):
            if username == "admin" and password == "admin123":
                st.session_state.username = username
                st.session_state.is_admin = True
                st.success("Admin login successful!")
            else:
                st.error("Invalid admin credentials.")

# If user is logged in
else:
    if st.session_state.is_admin:
        st.sidebar.title("Admin Menu")
        admin_choice = st.sidebar.radio("Choose an option:", ["Home", "Change Customer Password", "Logout"])
        
        if admin_choice == "Change Customer Password":
            st.subheader("Change Customer Password")
            username = st.text_input("Customer Username")
            new_password = st.text_input("New Password", type="password")
            if st.button("Change Password"):
                users = load_users()
                if username in users:
                    users[username]["password"] = hash_password(new_password)
                    save_users(users)
                    st.success("Password updated successfully!")
                else:
                    st.error("User not found.")
        
        elif admin_choice == "Logout" and st.button("Confirm Logout"):
            st.session_state.username = None
            st.session_state.is_admin = False
            st.success("Logged out successfully!")
    
    else:
        st.sidebar.title("Customer Menu")
        customer_choice = st.sidebar.radio("Choose an option:", ["Home", "Make Transaction", "View Balance", "Transaction History", "Change Password", "Logout"])
        
        if customer_choice == "Make Transaction":
            st.subheader("Make a Transaction")
            recipient = st.text_input("Recipient Username")
            amount = st.number_input("Enter Amount", min_value=0.0, step=0.01)
            if st.button("Transfer Money"):
                success, message = perform_transaction(st.session_state.username, recipient, amount)
                st.success(message) if success else st.error(message)
        
        elif customer_choice == "View Balance":
            users = load_users()
            balance = users[st.session_state.username]["balance"]
            st.subheader("Your Balance")
            st.info(f"Current Balance: {balance}")
        
        elif customer_choice == "Transaction History":
            users = load_users()
            transactions = users[st.session_state.username]["transactions"]
            st.subheader("Transaction History")
            if transactions:
                for t in transactions:
                    st.write(f"{t['time']} - {t['type']} {t.get('to', t.get('from', '') )}: {t['amount']}")
            else:
                st.info("No transactions found.")
        
        elif customer_choice == "Logout" and st.button("Confirm Logout"):
            st.session_state.username = None
            st.success("Logged out successfully!")
