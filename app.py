import streamlit as st
import pandas as pd
import os
import time
import smtplib
import random
from email.message import EmailMessage
from datetime import datetime

# --- DATABASE SETUP ---
USER_DB = "users.csv"
EXPENSE_DB = "expenses.csv"
CHAT_DB = "messages.csv"
PERMISSION_DB = "permissions.csv"

# Create CSVs if not exist
for db, cols in [(USER_DB, ["Name", "Email", "Password"]),
                 (EXPENSE_DB, ["Email", "Amount", "Category"]),
                 (CHAT_DB, ["Sender", "Receiver", "Message", "Timestamp"]),
                 (PERMISSION_DB, ["Requester", "Receiver", "Status"])]:
    if not os.path.exists(db):
        pd.DataFrame(columns=cols).to_csv(db, index=False)

# --- CONFIGURATION ---
SENDER_EMAIL = "sharifulhaque403@gmail.com"
SENDER_PASSWORD = "dgul gpjt ikjk grte"  # App password

# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.user_name = ""
if 'generated_otp' not in st.session_state:
    st.session_state.generated_otp = None

# --- FUNCTIONS ---

# OTP sending
def send_otp(receiver_email):
    otp = str(random.randint(100000, 999999))
    msg = EmailMessage()
    msg.set_content(f"Your code is: {otp}")
    msg["Subject"] = "Verification Code"
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return otp
    except Exception as e:
        st.error(f"Mail error: {e}")
        return None

# User signup
def sign_up(name, email, password):
    df = pd.read_csv(USER_DB)
    email = str(email).lower().strip()
    if email in df['Email'].astype(str).str.lower().str.strip().values:
        return False
    new_user = pd.DataFrame([[name, email, password.strip()]], columns=["Name", "Email", "Password"])
    new_user.to_csv(USER_DB, mode='a', header=False, index=False)
    return True

# User login
def sign_in(email, password):
    df = pd.read_csv(USER_DB)
    email = str(email).lower().strip()
    password = str(password).strip()
    mask = (df['Email'].astype(str).str.lower().str.strip() == email) & (df['Password'].astype(str).str.strip() == password)
    res = df[mask]
    return res.iloc[0]['Name'] if not res.empty else None

# Clear expenses
def clear_user_data(email):
    df = pd.read_csv(EXPENSE_DB)
    df = df[df['Email'].astype(str).str.lower().str.strip() != email.lower().strip()]
    df.to_csv(EXPENSE_DB, index=False)

# Chat functions
def send_message(sender, receiver, message):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pd.DataFrame([[sender, receiver, message, ts]], 
                 columns=["Sender", "Receiver", "Message", "Timestamp"]).to_csv(CHAT_DB, mode='a', header=False, index=False)

def get_messages(user1, user2):
    df = pd.read_csv(CHAT_DB)
    mask = ((df['Sender'] == user1) & (df['Receiver'] == user2)) | ((df['Sender'] == user2) & (df['Receiver'] == user1))
    return df[mask].sort_values("Timestamp")

# Permission functions
def request_permission(requester, receiver):
    df = pd.read_csv(PERMISSION_DB)
    existing = df[(df['Requester']==requester) & (df['Receiver']==receiver)]
    if not existing.empty:
        return False
    pd.DataFrame([[requester, receiver, "Pending"]], columns=["Requester","Receiver","Status"]).to_csv(PERMISSION_DB, mode='a', header=False, index=False)
    return True

def update_permission(requester, receiver, status):
    df = pd.read_csv(PERMISSION_DB)
    df.loc[(df['Requester']==requester) & (df['Receiver']==receiver), 'Status'] = status
    df.to_csv(PERMISSION_DB, index=False)

def check_permission(requester, receiver):
    df = pd.read_csv(PERMISSION_DB)
    row = df[(df['Requester']==requester) & (df['Receiver']==receiver)]
    if not row.empty:
        return row.iloc[0]['Status']
    return None

# --- UI LOGIC ---

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
    
    # --- Sign Up ---
    with tab2:
        st.header("Register")
        n = st.text_input("Name")
        e = st.text_input("Email", key="reg_e")
        p = st.text_input("Password", type="password")
        
        if st.button("Send OTP"):
            if e:
                with st.spinner("Sending OTP..."):
                    otp = send_otp(e)
                    if otp:
                        st.session_state.generated_otp = otp
                        st.success("OTP sent!")
            else:
                st.warning("Enter your email first.")

        if st.session_state.generated_otp:
            u_otp = st.text_input("Enter OTP")
            if st.button("Verify OTP"):
                if u_otp == st.session_state.generated_otp:
                    if sign_up(n, e, p):
                        st.session_state.logged_in = True
                        st.session_state.user_email = e
                        st.session_state.user_name = n
                        st.session_state.generated_otp = None
                        st.success("Verified! Entering Dashboard...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Email already exists.")
                else:
                    st.error("Wrong OTP.")

    # --- Sign In ---
    with tab1:
        st.header("Login")
        le = st.text_input("Email", key="log_e")
        lp = st.text_input("Password", type="password", key="log_p")
        if st.button("Login"):
            un = sign_in(le, lp)
            if un:
                st.session_state.logged_in = True
                st.session_state.user_email = le
                st.session_state.user_name = un
                st.rerun()
            else:
                st.error("Wrong email or password.")

else:
    # --- DASHBOARD ---
    st.sidebar.title(f"Hi, {st.session_state.user_name}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("💰 Expense Tracker")
    
    # Add Expense
    with st.container():
        amt = st.number_input("Amount (TK):", min_value=0.0)
        cat = st.selectbox("Category:", ["Food", "Transport", "Bills", "Rent", "Others"])
        if st.button("Add Expense"):
            if amt > 0:
                pd.DataFrame([[st.session_state.user_email, amt, cat]], 
                             columns=["Email", "Amount", "Category"]).to_csv(EXPENSE_DB, mode='a', header=False, index=False)
                st.toast("Added Successfully!")
                time.sleep(0.5)
                st.rerun()

    st.divider()
    
    # Load Expenses
    df = pd.read_csv(EXPENSE_DB)
    my_df = df[df['Email'].astype(str).str.lower().str.strip() == st.session_state.user_email.lower().strip()]

    if not my_df.empty:
        st.subheader("📊 Spending Analysis")
        chart_data = my_df.groupby("Category")["Amount"].sum()
        col1, col2 = st.columns([2, 1])
        with col1:
            st.bar_chart(chart_data)
        with col2:
            total = my_df['Amount'].sum()
            st.metric("Total Spent", f"{total} TK")
        
        st.subheader("📜 Detail History")
        st.table(my_df[["Category", "Amount"]])
    else:
        st.info("No data yet. Start adding expenses!")

    # --- CHAT & PERMISSION SYSTEM ---
    st.divider()
    st.subheader("💬 Chat & Permission System")

    # Users list
    df_users = pd.read_csv(USER_DB)
    other_users = df_users[df_users['Email'].str.lower().str.strip() != st.session_state.user_email.lower().strip()]
    user_map = dict(zip(other_users['Name'], other_users['Email']))

    chat_with = st.selectbox("Select a user:", [""] + list(user_map.keys()))

    if chat_with:
        receiver_email = user_map[chat_with]

        # Check permission
        perm_status = check_permission(st.session_state.user_email, receiver_email)

        if perm_status != "Accepted":
            st.info(f"You don't have access to {chat_with}'s expense data.")
            if st.button("Request Access"):
                if request_permission(st.session_state.user_email, receiver_email):
                    st.success("Permission requested! Waiting for approval.")
                else:
                    st.warning("Request already sent.")
        else:
            # Show receiver's expense data
            df = pd.read_csv(EXPENSE_DB)
            their_df = df[df['Email'].astype(str).str.lower().str.strip() == receiver_email.lower().strip()]
            if not their_df.empty:
                st.subheader(f"📊 {chat_with}'s Expenses")
                st.table(their_df)
            else:
                st.info(f"{chat_with} has no expense data yet.")

        # Show chat history
        messages = get_messages(st.session_state.user_email, receiver_email)
        if not messages.empty:
            for _, row in messages.iterrows():
                sender = "You" if row['Sender'] == st.session_state.user_email else chat_with
                st.markdown(f"**{sender}**: {row['Message']}")

        # Input new message
        new_msg = st.text_input("Type a message")
        if st.button("Send", key=f"send_msg_{receiver_email.replace('@','_at_')}"):
            if new_msg.strip():
                send_message(st.session_state.user_email, receiver_email, new_msg.strip())
                st.experimental_rerun()

    # Incoming permission requests
    st.subheader("📝 Pending Permission Requests")
    perm_df = pd.read_csv(PERMISSION_DB)
    incoming = perm_df[(perm_df['Receiver']==st.session_state.user_email) & (perm_df['Status']=="Pending")]

    for _, row in incoming.iterrows():
        requester_email = row['Requester']
        requester_name = df_users[df_users['Email']==requester_email].iloc[0]['Name']
        col1, col2 = st.columns(2)
        with col1:
            accept_key = f"accept_{requester_email.replace('@','_at_')}"
            if st.button(f"Accept {requester_name}", key=accept_key):
                update_permission(requester_email, st.session_state.user_email, "Accepted")
                st.success(f"Permission granted to {requester_name}")
                st.experimental_rerun()
        with col2:
            deny_key = f"deny_{requester_email.replace('@','_at_')}"
            if st.button(f"Deny {requester_name}", key=deny_key):
                update_permission(requester_email, st.session_state.user_email, "Denied")
                st.info(f"Permission denied to {requester_name}")
                st.experimental_rerun()

    # --- DANGER ZONE ---
    st.divider()
    with st.expander("🚨 Danger Zone - Clear All My Records"):
        if st.button("Clear My All Records"):
            clear_user_data(st.session_state.user_email)
            st.success("All your expense records have been cleared!")
            st.experimental_rerun()
