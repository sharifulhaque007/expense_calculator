diff --git a/app.py b/app.py
index db14333138064cf6c323c1355da24062c98bdda3..c79739ca6498aaeb05b66dbe2a30a0db15b182a0 100644
--- a/app.py
+++ b/app.py
@@ -182,71 +182,92 @@ else:
                 st.rerun()
 
     st.divider()
     
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
         st.dataframe(my_df[["Category", "Amount"]], use_container_width=True)
     else:
         st.info("No data yet. Start adding expenses!")
 
     # --- CHAT (NO PERMISSION REQUIRED) ---
     st.divider()
     st.subheader("💬 Direct Messages")
+    st.caption("Collaborate with teammates in a clean, business-friendly chat panel.")
 
     df_users = pd.read_csv(USER_DB)
     other_users = df_users[df_users['Email'].str.lower().str.strip() != st.session_state.user_email.lower().strip()]
     user_map = dict(zip(other_users['Name'], other_users['Email']))
 
-    chat_with = st.selectbox("Select a user to message:", [""] + list(user_map.keys()))
+    dm_left, dm_right = st.columns([3, 1], gap="large")
 
-    if chat_with:
-        receiver_email = user_map[chat_with]
+    with dm_right:
+        with st.container(border=True):
+            st.markdown("#### Conversation Panel")
+            chat_with = st.selectbox("Choose teammate", [""] + list(user_map.keys()))
 
-        st.write(f"--- Chat with {chat_with} ---")
-        messages = get_messages(st.session_state.user_email, receiver_email)
-        for _, row in messages.iterrows():
-            role = "You" if row['Sender'] == st.session_state.user_email else chat_with
-            st.markdown(f"**{role}**: {row['Message']}")
-
-        new_msg = st.text_input("Type a message", key=f"input_{receiver_email}")
-        if st.button("Send", key=f"btn_{receiver_email}"):
-            if new_msg.strip():
-                send_message(st.session_state.user_email, receiver_email, new_msg.strip())
-                st.rerun()
+            if chat_with:
+                receiver_email = user_map[chat_with]
+                messages = get_messages(st.session_state.user_email, receiver_email)
+                st.metric("Messages", len(messages))
+                if not messages.empty:
+                    st.caption(f"Last activity: {messages.iloc[-1]['Timestamp']}")
+            else:
+                st.caption("Select a teammate to open conversation.")
+
+    with dm_left:
+        with st.container(border=True):
+            if chat_with:
+                receiver_email = user_map[chat_with]
+                st.markdown(f"#### Chat with {chat_with}")
+
+                messages = get_messages(st.session_state.user_email, receiver_email)
+                for _, row in messages.iterrows():
+                    role = "You" if row['Sender'] == st.session_state.user_email else chat_with
+                    st.markdown(f"**{role}** · {row['Timestamp']}  ")
+                    st.markdown(f"{row['Message']}")
+                    st.markdown("---")
+
+                new_msg = st.text_input("Type your message", key=f"input_{receiver_email}", placeholder="Write a clear business message...")
+                if st.button("Send Message", key=f"btn_{receiver_email}", use_container_width=True):
+                    if new_msg.strip():
+                        send_message(st.session_state.user_email, receiver_email, new_msg.strip())
+                        st.rerun()
+            else:
+                st.info("Select a teammate from the right panel to start direct messaging.")
 
     # --- EXPENSE VIEW PERMISSION SYSTEM ---
     st.divider()
     st.subheader("🔐 Expense View Permissions")
 
     view_user = st.selectbox("Select a user to view expenses:", [""] + list(user_map.keys()))
     if view_user:
         view_user_email = user_map[view_user]
         perm_status = check_permission(st.session_state.user_email, view_user_email)
 
         if perm_status != "Accepted":
             st.info(f"You need {view_user}'s permission to view expense data.")
             if st.button("Request Expense Access"):
                 if request_permission(st.session_state.user_email, view_user_email):
                     st.success("Request sent!")
                 else:
                     st.warning("Request already exists.")
         else:
             their_df = df[df['Email'].astype(str).str.lower().str.strip() == view_user_email.lower().strip()]
             if not their_df.empty:
                 st.subheader(f"📊 {view_user}'s Expenses")
                 st.table(their_df[["Category", "Amount"]])
             else:
                 st.info(f"{view_user} has no data.")
 
