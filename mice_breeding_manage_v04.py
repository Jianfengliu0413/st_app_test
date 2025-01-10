import streamlit as st
import pandas as pd
import datetime
import time
import hashlib
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns

# Set up the app configuration
st.set_page_config(page_title="Mice Breeding Management", layout="wide")

# App Title
st.title("🐇 Mice Breeding Management System")

# File paths
USER_FILE = "./dat/users.json"
BREEDING_FILE = "./dat/breeding_data.csv"
REMINDERS_FILE = "./dat/reminders.json"

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Load User Data
def load_user_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {"admin": hash_password("admin123"), "user": hash_password("user123")}

# Load Breeding Data
def load_breeding_data(file_path):
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path, parse_dates=["Date Set Up", "Expected Delivery"])
        except Exception:
            return pd.DataFrame({
                "Breeding Pair": ["Pair 1", "Pair 2", "Pair 3"],
                "Male ID": ["M001", "M002", "M003"],
                "Female ID": ["F001", "F002", "F003"],
                "Date Set Up": [datetime.date(2024, 1, 1), datetime.date(2024, 1, 5), datetime.date(2024, 1, 10)],
                "Pregnancy Status": ["Pregnant", "Not Pregnant", "Pregnant"],
                "Expected Delivery": [datetime.date(2024, 1, 22), None, datetime.date(2024, 2, 1)],
                "Litter Size": [8, 0, 6]
            })
    return pd.DataFrame()

# Load Reminders
def load_reminders(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return []

# Initialize Session State
if "users" not in st.session_state:
    st.session_state.users = load_user_data(USER_FILE)

if "breeding_data" not in st.session_state:
    st.session_state.breeding_data = load_breeding_data(BREEDING_FILE)

if "reminders" not in st.session_state:
    st.session_state.reminders = load_reminders(REMINDERS_FILE)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "last_login_time" not in st.session_state:
    st.session_state.last_login_time = time.time()

# Save Data Functions
def save_users():
    with open(USER_FILE, "w") as f:
        json.dump(st.session_state.users, f)

def save_breeding_data():
    st.session_state.breeding_data.to_csv(BREEDING_FILE, index=False)

def save_reminders():
    with open(REMINDERS_FILE, "w") as f:
        json.dump(st.session_state.reminders, f)

# Calculate Weaning Date
def calculate_weaning_date(delivery_date):
    if isinstance(delivery_date, (datetime.date, datetime.datetime)):
        return delivery_date + datetime.timedelta(days=21)
    return None

# Login and Logout
auth_option = st.sidebar.radio('🔒 Login / Register', ["Login", "Register"]) if not st.session_state.authenticated else None

if st.session_state.authenticated:
    st.sidebar.write(f"Welcome, {st.session_state.username}!")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.last_login_time = None
else:
    if auth_option == "Login":
        username = st.sidebar.text_input("Username", placeholder="Enter username")
        password = st.sidebar.text_input("Password", type="password", placeholder="Enter password")
        if st.sidebar.button("Login"):
            if username in st.session_state.users and st.session_state.users[username] == hash_password(password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.last_login_time = time.time()
                st.sidebar.success(f"Welcome, {username}!")
            else:
                st.sidebar.error("Invalid username or password.")
        st.stop()
    elif auth_option == "Register":
        new_username = st.sidebar.text_input("Choose a Username")
        new_password = st.sidebar.text_input("Choose a Password", type="password")
        confirm_password = st.sidebar.text_input("Confirm Password", type="password")
        if st.sidebar.button("Register"):
            if new_username in st.session_state.users:
                st.sidebar.error("Username already exists.")
            elif new_password != confirm_password:
                st.sidebar.error("Passwords do not match.")
            else:
                st.session_state.users[new_username] = hash_password(new_password)
                save_users()
                st.sidebar.success("Registration successful!")
        st.stop()

# Logout after 2 minutes of inactivity
if st.session_state.authenticated and time.time() - st.session_state.last_login_time > 120:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.sidebar.warning("Session expired. Please log in again.")

# Main App Sections
if st.session_state.authenticated:
    # Display Data
    st.header("📋 Current Breeding Data")
    st.session_state.breeding_data["Weaning Date"] = st.session_state.breeding_data["Expected Delivery"].apply(
        lambda x: calculate_weaning_date(x) if pd.notnull(x) else None
    )
    st.table(st.session_state.breeding_data)

    # Add New Pair
    st.sidebar.header("➕ Add New Breeding Pair")
    with st.sidebar.form("add_pair_form"):
        male_id = st.text_input("Male ID", placeholder="M004")
        female_id = st.text_input("Female ID", placeholder="F004")
        date_set_up = st.date_input("Date Set Up", value=datetime.date.today())
        if st.form_submit_button("Add Pair"):
            new_pair = {
                "Breeding Pair": f"Pair {len(st.session_state.breeding_data) + 1}",
                "Male ID": male_id,
                "Female ID": female_id,
                "Date Set Up": date_set_up,
                "Pregnancy Status": "Not Pregnant",
                "Expected Delivery": None,
                "Litter Size": 0
            }
            st.session_state.breeding_data = pd.concat(
                [st.session_state.breeding_data, pd.DataFrame([new_pair])], ignore_index=True
            )
            save_breeding_data()
            st.success("✅ New breeding pair added!")

    # Update Pregnancy Status
    st.sidebar.header("✏️ Update Pregnancy Status")
    with st.sidebar.form("update_status_form"):
        pair_to_update = st.selectbox("Select Breeding Pair", st.session_state.breeding_data["Breeding Pair"])
        new_status = st.selectbox("Pregnancy Status", ["Not Pregnant", "Pregnant"])
        delivery_date = st.date_input("Expected Delivery Date", value=datetime.date.today())
        litter_size = st.number_input("Litter Size", min_value=0, value=0)
        if st.form_submit_button("Update Status"):
            st.session_state.breeding_data.loc[
                st.session_state.breeding_data["Breeding Pair"] == pair_to_update, ["Pregnancy Status", "Expected Delivery", "Litter Size"]
            ] = [new_status, delivery_date, litter_size]
            save_breeding_data()
            st.success("✅ Pregnancy status updated!")

    # Task Scheduler
    st.header("🗓️ Task Scheduler")
    with st.form("task_form"):
        task = st.text_input("Task Description", placeholder="E.g., Check Pair 1")
        task_date = st.date_input("Task Date", value=datetime.date.today())
        task_time = st.time_input("Task Time", value=datetime.time(9, 0))
        if st.form_submit_button("Add Task"):
            st.session_state.reminders.append({"Task": task, "Date": str(datetime.datetime.combine(task_date, task_time)), "Completed": False})
            save_reminders()
            st.success("✅ Task added!")

    # Active Reminders
    st.subheader("🔔 Active Reminders")
    for i, reminder in enumerate(st.session_state.reminders):
        col1, col2 = st.columns([0.8, 0.2])
        if col1.checkbox(f"{reminder['Task']} (Due: {reminder['Date']})", value=reminder.get("Completed", False), key=f"reminder_{i}"):
            st.session_state.reminders[i]["Completed"] = True
            save_reminders()
