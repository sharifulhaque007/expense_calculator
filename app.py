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
    # বাংলাদেশের টাইমজোন (UTC + 6 hours)
    tz_bd = timezone(timedelta(hours=6))
    ts = datetime.now(tz_bd).strftime("%I:%M %p | %d %b")
    pd.DataFrame([[sender, receiver, message, ts]], 
                 columns=["Sender", "Receiver", "Message", "Timestamp"]).to_csv(CHAT_DB, mode='a', header=False, index=False)

def check_permission(requester, receiver):
    df = pd.read_csv(PERMISSION_DB)
    row = df[(df['Requester']==requester) & (df['Receiver']==receiver)]
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
    with st.sidebar:
        st.markdown(f"### 👤 Welcome, {st.session_state.user_name}!")
        st.write(st.session_state.user_email)
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
                amt = st.number_input("Amount (TK)", min_value=0.0, step=10.0)
            with c2:
                cat = st.selectbox("Category", ["🍔 Food", "🚗 Transport", "🔌 Bills", "🏠 Rent", "🎁 Others"])
            
            if st.button("➕ Add Record", use_container_width=True, type="primary"):
                if amt > 0:
                    dt = datetime.now().strftime("%Y-%m-%d")
                    # সঠিক ইমেইল ফরম্যাটে সেভ করা হচ্ছে
                    pd.DataFrame([[st.session_state.user_email.lower().strip(), amt, cat, dt]], 
                                 columns=["Email", "Amount", "Category", "Date"]).to_csv(EXPENSE_DB, mode='a', header=False, index=False)
                    st.toast("Expense added successfully!", icon="✅")
                    time.sleep(0.5)
                    st.rerun()

        # --- এই অংশটি ফিক্স করা হয়েছে যাতে ডাটা দেখা যায় ---
        if os.path.exists(EXPENSE_DB):
            df = pd.read_csv(EXPENSE_DB)
            # ফিল্টারিং আরও শক্তিশালী করা হয়েছে
            my_df = df[df['Email'].astype(str).str.lower().str.strip() == st.session_state.user_email.lower().strip()]
            
            if not my_df.empty:
                st.subheader("📊 Spending Summary")
                st.metric("Total Spent", f"{my_df['Amount'].sum()} TK")
                st.bar_chart(my_df.groupby("Category")["Amount"].sum())
                with st.expander("📄 View History"):
                    st.dataframe(my_df[["Date", "Category", "Amount"]], use_container_width=True)
            else:
                st.info("No records found. Add your first expense above!")

    with m_col2:
        st.title("🌐 Connect")
        df_users = pd.read_csv(USER_DB)
        other_users = df_users[df_users['Email'].str.lower().str.strip() != st.session_state.user_email.lower().strip()]
        user_dict = dict(zip(other_users['Name'], other_users['Email']))
        
        target_name = st.selectbox("Find a Friend", ["Select User"] + list(user_dict.keys()))

        if target_name != "Select User":
            target_email = user_dict[target_name].lower().strip()
            t1, t2 = st.tabs(["💬 Chat", "👁️ View Expenses"])
            
            with t1:
                st.write(f"Messaging **{target_name}**")
                chat_df = pd.read_csv(CHAT_DB)
                # ইমেইল লোয়ারকেস করে ফিল্টার করা হচ্ছে
                my_mail = st.session_state.user_email.lower().strip()
                friend_mail = target_email
                
                mask = ((chat_df['Sender'].str.lower().str.strip() == my_mail) & (chat_df['Receiver'].str.lower().str.strip() == friend_mail)) | \
                       ((chat_df['Sender'].str.lower().str.strip() == friend_mail) & (chat_df['Receiver'].str.lower().str.strip() == my_mail))
                history = chat_df[mask]

                chat_container = st.container(height=300)
                for _, row in history.iterrows():
                    is_me = row['Sender'].lower().strip() == my_mail
                    # চ্যাটের কালার এবং টেক্সট ঠিক করা হয়েছে
                    bg_color = "#800080" if is_me else "#262730"
                    txt_color = "white"
                    align = "right" if is_me else "left"
                    
                    with chat_container:
                        st.markdown(f"""
                            <div style='text-align: {align};'>
                                <div style='display: inline-block; background: {bg_color}; color: {txt_color}; padding: 10px; border-radius: 10px; margin-bottom: 5px; max-width: 80%;'>
                                    <b>{'You' if is_me else target_name}:</b><br>{row['Message']} <br>
                                    <small style='font-size: 10px; opacity: 0.7;'>{row['Timestamp']}</small>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                msg = st.text_input("Type message...", key=f"in_{target_email}")
                if st.button("Send 🚀", key=f"btn_{target_email}"):
                    if msg.strip():
                        send_message(my_mail, friend_mail, msg)
                        st.rerun()

            with t2:
                perm = check_permission(st.session_state.user_email, target_email)
                if perm == "Accepted":
                    st.success(f"Access granted by {target_name}")
                    friend_data = df[df['Email'].str.lower().str.strip() == target_email]
                    if not friend_data.empty:
                        st.dataframe(friend_data[["Date", "Category", "Amount"]], use_container_width=True)
                    else:
                        st.info("Friend has no expense data.")
                elif perm == "Pending":
                    st.warning("Waiting for friend's approval...")
                else:
                    st.error("🔒 Expenses are private.")
                    if st.button("Request Access 🔑"):
                        pd.DataFrame([[st.session_state.user_email, target_email, "Pending"]], 
                                     columns=["Requester", "Receiver", "Status"]).to_csv(PERMISSION_DB, mode='a', header=False, index=False)
                        st.success("Request sent!")
                        st.rerun()

        st.divider()
        st.subheader("🔔 Notifications")
        p_df = pd.read_csv(PERMISSION_DB)
        incoming = p_df[(p_df['Receiver'] == st.session_state.user_email) & (p_df['Status'] == "Pending")]

        if not incoming.empty:
            for _, row in incoming.iterrows():
                r_mail = row['Requester']
                st.info(f"**{r_mail}** wants to see your expenses.")
                c1, c2 = st.columns(2)
                if c1.button("✅ Approve", key=f"acc_{r_mail}"):
                    p_df.loc[(p_df['Requester']==r_mail) & (p_df['Receiver']==st.session_state.user_email), 'Status'] = "Accepted"
                    p_df.to_csv(PERMISSION_DB, index=False)
                    st.rerun()
                if c2.button("❌ Deny", key=f"den_{r_mail}"):
                    p_df.loc[(p_df['Requester']==r_mail) & (p_df['Receiver']==st.session_state.user_email), 'Status'] = "Denied"
                    p_df.to_csv(PERMISSION_DB, index=False)
                    st.rerun()
        else:
            st.caption("No new access requests.")
