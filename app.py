import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, timezone, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Expense Tracker Pro", page_icon="💰", layout="wide")

# --- DATABASE SETUP ---
USER_DB = "users.csv"
EXPENSE_DB = "expenses.csv"
CHAT_DB = "messages.csv" # মেসেজ ডাটাবেস

# ডাটাবেস ফাইলগুলো সঠিক ফরম্যাটে রিসেট করার ফাংশন
def init_db():
    # ইউজার ডাটাবেস
    if not os.path.exists(USER_DB):
        pd.DataFrame(columns=["Name", "Email", "Password"]).to_csv(USER_DB, index=False)
    
    # খরচ ডাটাবেস
    expected_exp_cols = ["Email", "Amount", "Category", "Date"]
    if not os.path.exists(EXPENSE_DB):
        pd.DataFrame(columns=expected_exp_cols).to_csv(EXPENSE_DB, index=False)
    
    # মেসেজ ডাটাবেস
    expected_chat_cols = ["Sender", "Receiver", "Message", "Timestamp"]
    if not os.path.exists(CHAT_DB):
        pd.DataFrame(columns=expected_chat_cols).to_csv(CHAT_DB, index=False)

init_db()

# --- CORE FUNCTIONS ---
def sign_in(email, password):
    try:
        if not os.path.exists(USER_DB): return None
        df = pd.read_csv(USER_DB)
        if df.empty: return None
        
        email = str(email).lower().strip()
        df['Email'] = df['Email'].astype(str).str.lower().str.strip()
        df['Password'] = df['Password'].astype(str).str.strip()
        
        mask = (df['Email'] == email) & (df['Password'] == str(password).strip())
        res = df[mask]
        
        return res.iloc[0]['Name'] if not res.empty else None
    except:
        return None

def send_message(sender, receiver, message):
    tz_bd = timezone(timedelta(hours=6))
    ts = datetime.now(tz_bd).strftime("%I:%M %p | %d %b")
    new_msg = pd.DataFrame([{"Sender": sender, "Receiver": receiver, "Message": message, "Timestamp": ts}])
    new_msg.to_csv(CHAT_DB, mode='a', header=False, index=False)

# --- UI LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("💰 Expense Tracker Login")
    le = st.text_input("Email")
    lp = st.text_input("Password", type="password")
    if st.button("Login", type="primary", use_container_width=True):
        un = sign_in(le, lp)
        if un:
            st.session_state.logged_in = True
            st.session_state.user_email = le.lower().strip()
            st.session_state.user_name = un
            st.rerun()
        else:
            st.error("Invalid email or password.")
else:
    # --- LOGGED IN UI ---
    with st.sidebar:
        st.markdown(f"### 👤 Welcome, {st.session_state.user_name}!")
        st.code(st.session_state.user_email, language="text")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # মেইন স্ক্রিন ২ কলামে ভাগ করা
    col_main1, col_main2 = st.columns([1, 1])

    with col_main1:
        st.title("💸 My Expenses")
        
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            amt = c1.number_input("Amount (TK)", min_value=1.0, step=10.0)
            cat = c2.selectbox("Category", ["🍔 Food", "🚗 Transport", "🔌 Bills", "🏠 Rent", "🎁 Others"])
            
            if c3.button("➕ Add", use_container_width=True, type="primary"):
                dt = datetime.now().strftime("%Y-%m-%d")
                user_mail = st.session_state.user_email.lower().strip()
                
                new_row = pd.DataFrame([{"Email": user_mail, "Amount": amt, "Category": cat, "Date": dt}])
                new_row.to_csv(EXPENSE_DB, mode='a', header=False, index=False)
                
                st.success("Added!")
                time.sleep(0.5)
                st.rerun()

        # --- DASHBOARD ---
        st.divider()
        if os.path.exists(EXPENSE_DB):
            df_exp = pd.read_csv(EXPENSE_DB)
            if not df_exp.empty:
                df_exp['Email'] = df_exp['Email'].astype(str).str.lower().str.strip()
                df_exp['Amount'] = pd.to_numeric(df_exp['Amount'], errors='coerce')
                
                current_user = st.session_state.user_email.lower().strip()
                my_df = df_exp[df_exp['Email'] == current_user].dropna(subset=['Amount'])
                
                if not my_df.empty:
                    st.metric("Total Spent", f"{my_df['Amount'].sum():,.2f} TK")
                    st.bar_chart(my_df.groupby("Category")["Amount"].sum())
                    
                    with st.expander("📄 History"):
                        st.dataframe(my_df[["Date", "Category", "Amount"]].sort_values("Date", ascending=False), use_container_width=True)
                else:
                    st.info("No records found.")
            else:
                st.info("Empty database.")

    # --- CONNECT & CHAT ---
    with col_main2:
        st.title("🌐 Connect")
        
        # ইউজার খোঁজা
        df_users = pd.read_csv(USER_DB)
        other_users = df_users[df_users['Email'] != st.session_state.user_email]
        user_dict = dict(zip(other_users['Name'], other_users['Email']))
        
        target_name = st.selectbox("Find a Friend", ["Select User"] + list(user_dict.keys()))

        if target_name != "Select User":
            target_email = user_dict[target_name].lower().strip()
            st.subheader(f"💬 Chat with {target_name}")
            
            # মেসেজ লোড করা
            if os.path.exists(CHAT_DB):
                chat_df = pd.read_csv(CHAT_DB)
                my_mail = st.session_state.user_email.lower().strip()
                
                # ফিল্টার: আমার এবং তার মেসেজ
                mask = ((chat_df['Sender'] == my_mail) & (chat_df['Receiver'] == target_email)) | \
                       ((chat_df['Sender'] == target_email) & (chat_df['Receiver'] == my_mail))
                history = chat_df[mask]

                # মেসেজ প্রদর্শন
                chat_container = st.container(height=300)
                for _, row in history.iterrows():
                    is_me = row['Sender'] == my_mail
                    align = "right" if is_me else "left"
                    bg = "#800080" if is_me else "#262730"
                    
                    with chat_container:
                        st.markdown(f"<div style='text-align: {align};'><div style='display: inline-block; background: {bg}; color: white; padding: 10px; border-radius: 10px; margin-bottom: 5px;'>{row['Message']}</div></div>", unsafe_allow_html=True)

                # মেসেজ পাঠানো
                msg = st.text_input("Type...", key="chat_input")
                if st.button("Send", key="send_btn"):
                    if msg:
                        send_message(my_mail, target_email, msg)
                        st.rerun()
