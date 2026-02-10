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

# প্রয়োজনীয় ফাইলগুলো তৈরি করা
for db, cols in [(USER_DB, ["Name", "Email", "Password"]),
                 (EXPENSE_DB, ["Email", "Amount", "Category", "Date"]),
                 (CHAT_DB, ["Sender", "Receiver", "Message", "Timestamp"]),
                 (PERMISSION_DB, ["Requester", "Receiver", "Status"])]:
    if not os.path.exists(db):
        pd.DataFrame(columns=cols).to_csv(db, index=False)

# --- EMAIL CONFIG ---
SENDER_EMAIL = "sharifulhaque403@gmail.com"
SENDER_PASSWORD = "dgul gpjt ikjk grte"

# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.user_name = ""
if 'generated_otp' not in st.session_state:
    st.session_state.generated_otp = None

# --- CORE FUNCTIONS ---

def send_otp(receiver_email):
    otp = str(random.randint(100000, 999999))
    msg = EmailMessage()
    msg.set_content(f"Your verification code is: {otp}")
    msg["Subject"] = "Expense Tracker Verification"
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

def send_message(sender, receiver, message):
    tz_bd = timezone(timedelta(hours=6))
    ts = datetime.now(tz_bd).strftime("%I:%M %p | %d %b")
    pd.DataFrame([[sender, receiver, message, ts]], 
                 columns=["Sender", "Receiver", "Message", "Timestamp"]).to_csv(CHAT_DB, mode='a', header=False, index=False)

def check_permission(requester, receiver):
    df = pd.read_csv(PERMISSION_DB)
    row = df[(df['Requester'].astype(str).str.lower().str.strip() == requester.lower().strip()) & 
             (df['Receiver'].astype(str).str.lower().str.strip() == receiver.lower().strip())]
    if not row.empty:
        return row.iloc[0]['Status']
    return None

# --- UI LOGIC ---

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #4A90E2;'>💰 Expense Tracker Pro</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔑 Sign In", "📝 Create Account"])
        with tab1:
            le = st.text_input("Email", key="log_e")
            lp = st.text_input("Password", type="password", key="log_p")
            if st.button("Login", use_container_width=True, type="primary"):
                un = sign_in(le, lp)
                if un:
                    st.session_state.logged_in = True
                    st.session_state.user_email = le.lower().strip()
                    st.session_state.user_name = un
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

        with tab2:
            n = st.text_input("Full Name", key="reg_name")
            e = st.text_input("Email", key="reg_e")
            p = st.text_input("Password", type="password", key="reg_p")
            if st.button("Get OTP", use_container_width=True):
                if e:
                    otp = send_otp(e)
                    if otp:
                        st.session_state.generated_otp = otp
                        st.success("OTP sent! Check your email.")
                else:
                    st.warning("Please enter your email first.")

            if st.session_state.generated_otp:
                u_otp = st.text_input("Enter 6-Digit OTP", key="otp_input")
                if st.button("Verify & Sign Up", use_container_width=True, type="primary"):
                    if u_otp == st.session_state.generated_otp:
                        if sign_up(n, e, p):
                            st.success("Registration successful! Go to Login tab.")
                            st.session_state.generated_otp = None
                        else:
                            st.error("This email is already registered.")
                    else:
                        st.error("Wrong OTP code.")

else:
    # --- LOGGED IN UI ---
    with st.sidebar:
        st.markdown(f"### 👤 Welcome, {st.session_state.user_name}!")
        st.code(st.session_state.user_email, language="text") # ইমেইল চেক করার জন্য
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    m_col1, m_col2 = st.columns([1.2, 1])

    with m_col1:
        st.title("💸 My Expenses")
        
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                amt = st.number_input("Amount (TK)", min_value=0.0, step=10.0, key="amt_val")
            with c2:
                cat = st.selectbox("Category", ["🍔 Food", "🚗 Transport", "🔌 Bills", "🏠 Rent", "🎁 Others"], key="cat_val")
            
            if st.button("➕ Add Record", use_container_width=True, type="primary"):
                if amt > 0:
                    dt = datetime.now().strftime("%Y-%m-%d")
                    # ডাটা সেভ করার সময় ইমেইল ক্লিন করা নিশ্চিত করা
                    save_email = str(st.session_state.user_email).lower().strip()
                    new_record = pd.DataFrame([[save_email, amt, cat, dt]], 
                                             columns=["Email", "Amount", "Category", "Date"])
                    new_record.to_csv(EXPENSE_DB, mode='a', header=False, index=False)
                    st.success(f"Added {amt} TK to {cat}!")
                    time.sleep(1)
                    st.rerun()

        st.divider()
        
        # --- DASHBOARD LOGIC (ROBUST VERSION) ---
        if os.path.exists(EXPENSE_DB):
            df_exp = pd.read_csv(EXPENSE_DB)
            
            # ডাটা টাইপ ঠিক করা
            df_exp['Email'] = df_exp['Email'].astype(str).str.lower().str.strip()
            df_exp['Amount'] = pd.to_numeric(df_exp['Amount'], errors='coerce')
            
            current_user = str(st.session_state.user_email).lower().strip()
            
            # ফিল্টার করা ডাটা
            my_df = df_exp[df_exp['Email'] == current_user]
            
            if not my_df.empty:
                total = my_df['Amount'].sum()
                st.metric(label="Total Spent", value=f"{total:,.2f} TK")
                
                # বার চার্ট
                st.subheader("📊 Category Distribution")
                chart_data = my_df.groupby("Category")["Amount"].sum()
                st.bar_chart(chart_data)
                
                # হিস্টোরি টেবিল
                with st.expander("📄 History Table"):
                    st.dataframe(my_df[["Date", "Category", "Amount"]].sort_values(by="Date", ascending=False), use_container_width=True)
            else:
                st.info("No expense data found. Add your first expense!")
                # DEBUG OPTION (নিচে আপনার ডাটাবেসে কি আছে তা দেখার জন্য)
                with st.expander("🛠️ Debug: View Raw Database (Only you see this)"):
                    st.write("Current User Email:", f"'{current_user}'")
                    st.write("All Records in CSV:", df_exp)
        else:
            st.warning("Database file missing.")

    with m_col2:
        st.title("🌐 Connect")
        # Social & Chat Logic
        df_users = pd.read_csv(USER_DB)
        other_users = df_users[df_users['Email'].astype(str).str.lower().str.strip() != st.session_state.user_email.lower().strip()]
        user_dict = dict(zip(other_users['Name'], other_users['Email']))
        
        target_name = st.selectbox("Find a Friend", ["Select User"] + list(user_dict.keys()))

        if target_name != "Select User":
            target_email = user_dict[target_name].lower().strip()
            t1, t2 = st.tabs(["💬 Chat", "👁️ View Expenses"])
            
            with t1:
                chat_df = pd.read_csv(CHAT_DB)
                my_mail = st.session_state.user_email.lower().strip()
                mask = ((chat_df['Sender'].astype(str).str.lower().str.strip() == my_mail) & (chat_df['Receiver'].astype(str).str.lower().str.strip() == target_email)) | \
                       ((chat_df['Sender'].astype(str).str.lower().str.strip() == target_email) & (chat_df['Receiver'].astype(str).str.lower().str.strip() == my_mail))
                history = chat_df[mask]

                chat_container = st.container(height=250)
                for _, row in history.iterrows():
                    is_me = str(row['Sender']).lower().strip() == my_mail
                    align = "right" if is_me else "left"
                    bg = "#800080" if is_me else "#262730"
                    with chat_container:
                        st.markdown(f"<div style='text-align: {align};'><div style='display: inline-block; background: {bg}; color: white; padding: 10px; border-radius: 10px; margin-bottom: 5px;'>{row['Message']}</div></div>", unsafe_allow_html=True)

                msg = st
