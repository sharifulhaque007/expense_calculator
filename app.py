import streamlit as st
import pandas as pd
import os
import time
import smtplib
import random
from email.message import EmailMessage
from datetime import datetime, timezone, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Expense Tracker Pro", page_icon="💰", layout="wide")

# --- DATABASE SETUP ---
USER_DB = "users.csv"
EXPENSE_DB = "expenses.csv"
CHAT_DB = "messages.csv"
PERMISSION_DB = "permissions.csv"

# প্রয়োজনীয় ফাইলগুলো সঠিক কলামসহ তৈরি করা
def init_db():
    db_configs = {
        USER_DB: ["Name", "Email", "Password"],
        EXPENSE_DB: ["Email", "Amount", "Category", "Date"],
        CHAT_DB: ["Sender", "Receiver", "Message", "Timestamp"],
        PERMISSION_DB: ["Requester", "Receiver", "Status"]
    }
    for db, cols in db_configs.items():
        if not os.path.exists(db):
            pd.DataFrame(columns=cols).to_csv(db, index=False)

init_db()

# --- CORE FUNCTIONS ---
def sign_in(email, password):
    df = pd.read_csv(USER_DB)
    email = str(email).lower().strip()
    mask = (df['Email'].astype(str).str.lower().str.strip() == email) & (df['Password'].astype(str).strip() == str(password).strip())
    res = df[mask]
    return res.iloc[0]['Name'] if not res.empty else None

def send_message(sender, receiver, message):
    tz_bd = timezone(timedelta(hours=6))
    ts = datetime.now(tz_bd).strftime("%I:%M %p | %d %b")
    new_msg = pd.DataFrame([[sender, receiver, message, ts]], columns=["Sender", "Receiver", "Message", "Timestamp"])
    new_msg.to_csv(CHAT_DB, mode='a', header=False, index=False)

# --- UI LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # লগইন পেজ (আপনার আগের কোডের মতোই থাকবে)
    st.title("💰 Expense Tracker Login")
    le = st.text_input("Email")
    lp = st.text_input("Password", type="password")
    if st.button("Login"):
        un = sign_in(le, lp)
        if un:
            st.session_state.logged_in = True
            st.session_state.user_email = le.lower().strip()
            st.session_state.user_name = un
            st.rerun()
else:
    # --- LOGGED IN UI ---
    with st.sidebar:
        st.markdown(f"### 👤 Welcome, {st.session_state.user_name}!")
        st.info(st.session_state.user_email)
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    m_col1, m_col2 = st.columns([1.5, 1])

    with m_col1:
        st.title("💸 My Expenses")
        
        with st.container(border=True):
            c1, c2 = st.columns(2)
            amt = c1.number_input("Amount (TK)", min_value=1.0, step=10.0)
            cat = c2.selectbox("Category", ["🍔 Food", "🚗 Transport", "🔌 Bills", "🏠 Rent", "🎁 Others"])
            
            if st.button("➕ Add Record", use_container_width=True, type="primary"):
                dt = datetime.now().strftime("%Y-%m-%d")
                user_mail = st.session_state.user_email
                
                # কলামের নাম উল্লেখ করে ডাটা সেভ (এতে কলাম উলটপালট হবে না)
                new_data = pd.DataFrame({"Email": [user_mail], "Amount": [amt], "Category": [cat], "Date": [dt]})
                new_data.to_csv(EXPENSE_DB, mode='a', header=False, index=False)
                
                st.success(f"Added {amt} TK to {cat}!")
                time.sleep(1)
                st.rerun()

        # --- DASHBOARD ---
        st.divider()
        if os.path.exists(EXPENSE_DB):
            df_exp = pd.read_csv(EXPENSE_DB)
            # ডাটা ক্লিনআপ
            df_exp['Email'] = df_exp['Email'].astype(str).str.lower().strip()
            current_user = st.session_state.user_email
            
            my_df = df_exp[df_exp['Email'] == current_user]
            
            if not my_df.empty:
                st.metric("Total Spent", f"{my_df['Amount'].sum():,.2f} TK")
                st.bar_chart(my_df.groupby("Category")["Amount"].sum())
                with st.expander("📄 History"):
                    st.dataframe(my_df[["Date", "Category", "Amount"]].sort_values("Date", ascending=False))
            else:
                st.info("No records found for this email. Add a record to see the dashboard.")
                
                # ডাটাবেস রিসেট বাটন (শুধুমাত্র যদি কলাম খুব বেশি এলোমেলো থাকে)
                if st.button("Clear Incorrect Database"):
                    pd.DataFrame(columns=["Email", "Amount", "Category", "Date"]).to_csv(EXPENSE_DB, index=False)
                    st.rerun()

    # মেইন কলাম ২ (Connect/Chat) সেকশন আগের মতোই থাকবে...
