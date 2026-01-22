import streamlit as st
import pandas as pd
import os
import time
import smtplib
import random
from email.message import EmailMessage

# --- DATABASE SETUP ---
USER_DB = "users.csv"
EXPENSE_DB = "expenses.csv"

# --- CONFIGURATION ---
SENDER_EMAIL = "sharifulhaque403@gmail.com"
SENDER_PASSWORD = "dgul gpjt ikjk grte"
ADMIN_EMAIL = "sharifulhaque403@gmail.com"

if not os.path.exists(USER_DB):
    pd.DataFrame(columns=["Name", "Email", "Password"]).to_csv(USER_DB, index=False)
if not os.path.exists(EXPENSE_DB):
    pd.DataFrame(columns=["Email", "Amount", "Category"]).to_csv(EXPENSE_DB, index=False)

# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.user_name = ""
if 'generated_otp' not in st.session_state:
    st.session_state.generated_otp = None

# --- FUNCTIONS ---
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

def sign_up(name, email, password):
    df = pd.read_csv(USER_DB)
    email = str(email).lower().strip()
    if email in df['Email'].astype(str).str.lower().str.strip().values:
        return False
    new_user = pd.DataFrame([[name, email, password.strip()]], columns=["Name", "Email", "Password"])
    new_user.to_csv(USER_DB, mode='a', header=False, index=False)
    return True

def sign_in(email, password):
    df = pd.read_csv(USER_DB)
    email = str(email).lower().strip()
    password = str(password).strip()
    mask = (df['Email'].astype(str).str.lower().str.strip() == email) & (df['Password'].astype(str).str.strip() == password)
    res = df[mask]
    return res.iloc[0]['Name'] if not res.empty else None

def clear_user_data(email):
    df = pd.read_csv(EXPENSE_DB)
    df = df[df['Email'].astype(str).str.lower().str.strip() != email.lower().strip()]
    df.to_csv(EXPENSE_DB, index=False)

# --- UI LOGIC ---
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
    with tab2:
        st.header("Register")
        n = st.text_input("Name")
        e = st.text_input("Email", key="reg_e")
        p = st.text_input("Pass", type="password")
        if st.button("send OTP"):
            if e:
                with st.spinner("Sending..."):
                    otp = send_otp(e)
                    if otp: 
                        st.session_state.generated_otp = otp
                        st.success("Code sent!")
            else:
                st.warning("Enter email first.")

        if st.session_state.generated_otp:
            u_otp = st.text_input("Enter OTP")
            if st.button("Verify"):
                if u_otp == st.session_state.generated_otp:
                    if sign_up(n, e, p): 
                        # --- Registration por Auto-Login logic ---
                        st.session_state.logged_in = True
                        st.session_state.user_email = e
                        st.session_state.user_name = n
                        st.session_state.generated_otp = None
                        st.success("Verified! Entering Dashboard...")
                        time.sleep(1)
                        st.rerun()
                    else: 
                        st.error("Email exists.")
                else: 
                    st.error("Wrong OTP.")

    with tab1:
        st.header("Login")
        le = st.text_input("Email", key="log_e")
        lp = st.text_input("Pass", type="password", key="log_p")
        if st.button("Login"):
            un = sign_in(le, lp)
            if un:
                st.session_state.logged_in, st.session_state.user_email, st.session_state.user_name = True, le, un
                st.rerun()
            else: 
                st.error("Wrong password try again.")
else:
    # --- DASHBOARD UI ---
    st.sidebar.title(f"Hi, {st.session_state.user_name}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("💰 Expense Tracker")
    
    # Input container
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
    
    # Load and Filter Data
    df = pd.read_csv(EXPENSE_DB)
    my_df = df[df['Email'].astype(str).str.lower().str.strip() == st.session_state.user_email.lower().strip()]

    if not my_df.empty:
        st.subheader("📊 Spending Analysis")
        # Calculation for chart
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

    with st.expander("🚨 Danger Zone"):
        if st.button("Clear My All Records"):
            clear_user_data(st.session_state.user_email)
            st.rerun()
