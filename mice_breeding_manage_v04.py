import streamlit as st
import pandas as pd
import datetime
import time
import hashlib
import os
import json
from py2ls.ips import fsave
from py2ls import plot
from streamlit_autorefresh import st_autorefresh

import matplotlib.pyplot as plt
import seaborn as sns 
# Set up the app configuration
st.set_page_config(page_title="Mice Breeding Management", layout="wide")

# App Title
st.title("🐇 Management System")

# # initial dat
# if not os.path.isfile("./dat/users.json"):
#     fsave("./dat/users.json",{})
# if not os.path.isfile("./dat/reminders.json"):
#     fsave("./dat/reminders.json",{})
# if os.path.isfile("./dat/breeding_data.csv"):
#     fsave("./dat/breeding_data.csv",pd.DataFrame())
# File paths
USER_FILE = "./dat/users.json"
BREEDING_FILE = "./dat/breeding_data.csv"
REMINDERS_FILE = "./dat/reminders.json"

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

 
@st.cache_data
def load_user_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {"admin": hash_password("admin123"), "user": hash_password("user123")}

if "users" not in st.session_state:
    st.session_state.users = load_user_data(USER_FILE)

# Load or initialize breeding data
@st.cache_data
def load_breeding_data(file_path):
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path, parse_dates=["Date Set Up", "Expected Delivery"])
        except Exception:
            # Default DataFrame in case of error
            return pd.DataFrame({
                "Breeding Pair": ["Pair 1", "Pair 2", "Pair 3"],
                "Male ID": ["M001", "M002", "M003"],
                "Female ID": ["F001", "F002", "F003"],
                "Date Set Up": [datetime.date(2024, 1, 1), datetime.date(2024, 1, 5), datetime.date(2024, 1, 10)],
                "Pregnancy Status": ["Pregnant", "Not Pregnant", "Pregnant"],
                "Expected Delivery": [datetime.date(2024, 1, 22), None, datetime.date(2024, 2, 1)],
                "Litter Size": [8, 0, 6]
            })
    return pd.DataFrame()  # Empty DataFrame if the file doesn't exist

if "breeding_data" not in st.session_state:
    st.session_state.breeding_data = load_breeding_data(BREEDING_FILE)


# Load or initialize reminders
@st.cache_data
def load_reminders(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return []

if "reminders" not in st.session_state:
    st.session_state.reminders = load_reminders(REMINDERS_FILE)


# Function to save data
def save_users():
    with open(USER_FILE, "w") as f:
        json.dump(st.session_state.users, f)

def save_breeding_data():
    st.session_state.breeding_data.to_csv(BREEDING_FILE, index=False)

def save_reminders():
    with open(REMINDERS_FILE, "w") as f:
        json.dump(st.session_state.reminders, f)

time_out=12000 # 2min

# Login System
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
# Track login time for refresh logic
if "last_login_time" not in st.session_state:
    st.session_state.last_login_time = time.time()

# Sidebar for Login and Registration
auth_option = st.sidebar.radio('🔒 Login / Register', ["Login", "Register"]) if not st.session_state.authenticated else None

if st.session_state.authenticated:
    # If the user is authenticated, show their username instead of login options
    st.sidebar.write(f"Dear {st.session_state.username}:")
    st.session_state.authenticated = True
    # logout button
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.last_login_time = None
else:
    user_login = None
    if auth_option == "Login":
        username = st.sidebar.text_input("Username", placeholder='username')
        password = st.sidebar.text_input("Password", type="password", placeholder='**********')
        login_clicked = st.sidebar.button("Login")

        if login_clicked:
            if username in st.session_state.users and st.session_state.users[username] == hash_password(password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.last_login_time = time.time()  # Update login time
                st.sidebar.success(f"Hi {username}, Successfully login")
            else:
                st.sidebar.error("Invalid credentials.")
        st.stop()

    elif auth_option == "Register":
        new_username = st.sidebar.text_input("Choose a Username")
        new_password = st.sidebar.text_input("Choose a Password", type="password")
        confirm_password = st.sidebar.text_input("Confirm Password", type="password")
        register_clicked = st.sidebar.button("Register")

        if register_clicked:
            if not new_username or not new_password:
                st.sidebar.error("Please fill in all fields.")
            elif new_username in st.session_state.users:
                st.sidebar.error("Username already exists.")
            elif new_password != confirm_password:
                st.sidebar.error("Passwords do not match.")
            else:
                st.session_state.users[new_username] = hash_password(new_password)
                save_users()  # Save to file
                st.sidebar.success("Registration successful! You can now log in.")
        st.stop()

# Check if 2 minutes have passed since the last login and auto-logout after timeout
if st.session_state.authenticated and time.time() - st.session_state.last_login_time > time_out:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.last_login_time = None
    st.sidebar.warning("Session expired. Please log in again.")
# * data management
st.header("📋 Data Management")
st.write("Welcome to the advanced mice breeding management system!")
st_autorefresh(interval=time_out, limit=100, key="fizzbuzzcounter")

# Function: Calculate Weaning Dates 
@st.cache_data
def calculate_weaning_date(delivery_date):
    if isinstance(delivery_date, (datetime.date, datetime.datetime)):
        return delivery_date + datetime.timedelta(days=21)
    return None

breeding_df = st.session_state.breeding_data
breeding_df["Weaning Date"] = breeding_df["Expected Delivery"].apply(
    lambda x: calculate_weaning_date(x) if pd.notnull(x) else None
)
 

# Section 1: Display Current Breeding Data
st.header("📋 Current Breeding Data")
# st.dataframe(breeding_df.tail(5))
st.table(breeding_df.iloc[-5:,:])
#! plot section
df2plot=breeding_df.copy()
st.bar_chart(data=df2plot.tail(10),x="Pregnancy Status",y='Litter Size')
for col in ["Date Set Up","Expected Delivery","Weaning Date"]:
    df2plot[col]=df2plot[col].astype(str)
fig, ax  = plt.subplots(figsize=[4,2])
sns.lineplot(data=df2plot, x='Date Set Up',y="Litter Size",ax=ax)
sns.lineplot(data=df2plot, x='Expected Delivery',y="Litter Size",ax=ax)
sns.lineplot(data=df2plot, x='Weaning Date',y="Litter Size",ax=ax)
plot.figsets(xangle=90,ax=ax,figsize=8)
st.pyplot(fig)
# Section 2: Add a New Breeding Pair
st.sidebar.header("➕ Add New Breeding Pair")
with st.sidebar.form("add_pair_form"):
    male_id = st.text_input("Male ID", placeholder="M004")
    female_id = st.text_input("Female ID", placeholder="F004")
    date_set_up = st.date_input("Date Set Up", value=datetime.date.today())
    submit_new_pair = st.form_submit_button("Add Pair")
    if submit_new_pair:
        new_pair = {
            "Breeding Pair": f"Pair {len(breeding_df) + 1}",
            "Male ID": male_id,
            "Female ID": female_id,
            "Date Set Up": date_set_up,
            "Pregnancy Status": "Not Pregnant",
            "Expected Delivery": None,
            "Litter Size": 0
        }
        breeding_df = pd.concat([breeding_df, pd.DataFrame([new_pair])], ignore_index=True)
        st.session_state.breeding_data = breeding_df
        save_breeding_data()  # Save to file
        st.success("✅ New breeding pair added!")

# Section 3: Update Pregnancy Status
st.sidebar.header("✏️ Update Pregnancy Status")
with st.sidebar.form("update_status_form"):
    pair_to_update = st.selectbox("Select Breeding Pair", breeding_df.sort_index(ascending=False)["Breeding Pair"])
    new_status = st.selectbox("Pregnancy Status", ["Not Pregnant", "Pregnant"])
    delivery_date = st.date_input("Expected Delivery Date", value=datetime.date.today())
    litter_size = st.number_input("Litter Size (if known)", min_value=0, value=5)
    submit_status_update = st.form_submit_button("Update Status")
    if submit_status_update:
        breeding_df.loc[breeding_df["Breeding Pair"] == pair_to_update, "Pregnancy Status"] = new_status
        breeding_df.loc[breeding_df["Breeding Pair"] == pair_to_update, "Expected Delivery"] = delivery_date
        breeding_df.loc[breeding_df["Breeding Pair"] == pair_to_update, "Litter Size"] = litter_size
        st.session_state.breeding_data = breeding_df
        save_breeding_data()  # Save to file
        st.success("✅ Pregnancy status updated!")

# Section 4: Task Scheduler with Tick List
st.sidebar.header("🗓️ Task Scheduler")
# Add Reminder
with st.sidebar.form("task_form"):
    reminder_text = st.text_input("Task Description", placeholder="E.g., Check Pair 1")
    reminder_date = st.date_input("Date", 
                                  value=datetime.date.today()
                                  )
    reminder_time = st.time_input("Time", 
                                  value=datetime.time(8, 45),#None,#
                                  step=3600
                                  )
    add_reminder = st.form_submit_button("Set Reminder")
    if add_reminder:
        reminder_date = datetime.datetime.combine(reminder_date, reminder_time)  # Combine date and time
        new_reminder = {"Task": reminder_text, "Date": str(reminder_date), "Completed": False}
        if isinstance(st.session_state.reminders, list):
            # Append the new reminder
            st.session_state.reminders.append(new_reminder)
        else:
            # Reinitialize as a list if it's not
            st.session_state.reminders = [new_reminder]
        save_reminders()  # Save to file
        st.sidebar.success("✅ Reminder added successfully!")


# Show reminders as a tickable list
st.header("🔔 Active Reminders")
if st.button("Clear Completed Reminders"):
    st.session_state.reminders = [r for r in st.session_state.reminders if not r["Completed"]]
    save_reminders()  # Save to file
    st.success("✅ Completed reminders cleared!")
for i, reminder in enumerate(st.session_state.reminders):
    col1, col2 = st.columns([20, 1])
    if reminder["Completed"]:
        # col1.markdown(f"<span style='color:#00BB00;background-color:yellow'>~~{reminder['Task']} (Due: {reminder['Date']})~~", unsafe_allow_html=True)
        col1.markdown(f"""{reminder['Task']} ~~:rainbow[(Due: {reminder['Date']})]~~""", unsafe_allow_html=True)
    else:
        completed = col1.checkbox(f"{reminder['Task']} (Due: {reminder['Date']})", key=f"reminder_{i}")
        if completed:
            st.session_state.reminders[i]["Completed"] = True
            save_reminders()  # Save to file

