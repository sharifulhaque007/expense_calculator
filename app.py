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

# ডাটাবেস ফাইলগুলো সঠিক ফরম্যাটে রিসেট করার ফাংশন
def init_db():
    # ইউজার ডাটাবেস
    if not os.path.exists(USER_DB):
        pd.DataFrame(columns=["Name", "Email", "Password"]).to_csv(USER_DB, index=False)
    
    # খরচ ডাটাবেস
    expected_cols = ["Email", "Amount", "Category", "Date"]
    if not os.path.exists(EXPENSE_DB):
        pd.DataFrame(columns=expected_cols).to_csv(EXPENSE_DB, index=False)
    else:
        # যদি ফাইল থাকে কিন্তু কলাম ভুল থাকে, তবে কলামগুলো জোর করে ঠিক করা
        df = pd.read_csv(EXPENSE_DB)
        if list(df.columns) != expected_cols:
             pd.DataFrame(columns=expected_cols).to_csv(EXPENSE_DB, index=False)

init_db()

# --- CORE FUNCTIONS (UPDATED) ---
def sign_in(email, password):
    try:
        # ফাইলটি চেক করা
        if not os.path.exists(USER_DB): return None
        
        df = pd.read_csv(USER_DB)
        
        # ডাটাফ্রেম খালি থাকলে
        if df.empty: return None
        
        # কলামের নাম ঠিক আছে কিনা নিশ্চিত হওয়া এবং টাইপ ঠিক করা
        if 'Email' not in df.columns or 'Password' not in df.columns: return None
        
        email = str(email).lower().strip()
        
        # সঠিক টাইপ কাস্টিং
        df['Email'] = df['Email'].astype(str).str.lower().str.strip()
        # পাসওয়ার্ড চেক করার আগে এটি নিশ্চিত করা যে এটি একটি সিরিজ
        df['Password'] = df['Password'].astype(str).str.strip()
        
        mask = (df['Email'] == email) & (df['Password'] == str(password).strip())
        res = df[mask]
        
        return res.iloc[0]['Name'] if not res.empty else None
    except Exception as e:
        st.error(f"Sign in error: {e}")
        return None

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
    # --- LOGGED IN UI (আগের মতোই থাকবে) ---
    with st.sidebar:
        st.markdown(f"### 👤 Welcome, {st.session_state.user_name}!")
        st.code(st.session_state.user_email, language="text")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    st.title("💸 My Expenses")
    
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        amt = c1.number_input("Amount (TK)", min_value=1.0, step=10.0)
        cat = c2.selectbox("Category", ["🍔 Food", "🚗 Transport", "🔌 Bills", "🏠 Rent", "🎁 Others"])
        
        if c3.button("➕ Add Record", use_container_width=True, type="primary"):
            dt = datetime.now().strftime("%Y-%m-%d")
            user_mail = st.session_state.user_email.lower().strip()
            
            new_row = pd.DataFrame([{"Email": user_mail, "Amount": amt, "Category": cat, "Date": dt}])
            new_row.to_csv(EXPENSE_DB, mode='a', header=False, index=False)
            
            st.success("Record Added!")
            time.sleep(1)
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
                col_m1, col_m2 = st.columns([1, 2])
                with col_m1:
                    st.metric("Total Spent", f"{my_df['Amount'].sum():,.2f} TK")
                    st.subheader("📊 Category Wise")
                    st.bar_chart(my_df.groupby("Category")["Amount"].sum())
                
                with col_m2:
                    st.subheader("📄 Recent History")
                    st.dataframe(my_df[["Date", "Category", "Amount"]].sort_values("Date", ascending=False), use_container_width=True)
            else:
                st.info(f"No records found for {current_user}. Please add an expense.")
        else:
            st.info("The database is currently empty.")
