# #
# import streamlit as st
# import requests
# import json
# from datetime import datetime

# # Configure page
# st.set_page_config(
#     page_title="ChatBot Application",
#     page_icon="ðŸ¤–",
#     layout="wide"
# )

# # Backend URL
# BACKEND_URL = "http://localhost:5000"

# def init_session_state():
#     if 'logged_in' not in st.session_state:
#         st.session_state.logged_in = False
#     if 'user_type' not in st.session_state:
#         st.session_state.user_type = None
#     if 'username' not in st.session_state:
#         st.session_state.username = None
#     if 'token' not in st.session_state:
#         st.session_state.token = None

# def login_user(username, password, user_type):
#     try:
#         response = requests.post(
#             f"{BACKEND_URL}/auth/login",
#             json={
#                 "username": username,
#                 "password": password,
#                 "user_type": user_type
#             }
#         )
#         if response.status_code == 200:
#             data = response.json()
#             st.session_state.logged_in = True
#             st.session_state.user_type = user_type
#             st.session_state.username = username
#             st.session_state.token = data.get('token')
#             return True, "Login successful!"
#         else:
#             return False, response.json().get('message', 'Login failed')
#     except Exception as e:
#         return False, f"Connection error: {str(e)}"

# def signup_user(username, email, password, user_type):
#     try:
#         response = requests.post(
#             f"{BACKEND_URL}/auth/signup",
#             json={
#                 "username": username,
#                 "email": email,
#                 "password": password,
#                 "user_type": user_type
#             }
#         )
#         if response.status_code == 201:
#             return True, "Account created successfully!"
#         else:
#             return False, response.json().get('message', 'Signup failed')
#     except Exception as e:
#         return False, f"Connection error: {str(e)}"

# def logout():
#     st.session_state.logged_in = False
#     st.session_state.user_type = None
#     st.session_state.username = None
#     st.session_state.token = None

# def main():
#     init_session_state()

#     if not st.session_state.logged_in:
#         # Login/Signup Interface
#         st.title("ðŸ¤– ChatBot Application")
#         st.markdown("---")

#         # Create tabs for Login and Signup
#         login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

#         with login_tab:
#             st.header("Login")
#             col1, col2 = st.columns(2)

#             with col1:
#                 if st.button("ðŸ” Regular User Login", use_container_width=True, type="primary"):
#                     st.session_state.login_type = "regular"

#             with col2:
#                 if st.button("ðŸ‘¨â€ðŸ’¼ Admin User Login", use_container_width=True, type="secondary"):
#                     st.session_state.login_type = "admin"

#             if 'login_type' in st.session_state:
#                 st.markdown("---")
#                 with st.form("login_form"):
#                     username = st.text_input("Username")
#                     password = st.text_input("Password", type="password")
#                     submitted = st.form_submit_button("Login")

#                     if submitted:
#                         if username and password:
#                             success, message = login_user(username, password, st.session_state.login_type)
#                             if success:
#                                 st.success(message)
#                                 st.rerun()
#                             else:
#                                 st.error(message)
#                         else:
#                             st.error("Please fill in all fields")

#         with signup_tab:
#             st.header("Create New Account")
#             with st.form("signup_form"):
#                 new_username = st.text_input("Username", key="signup_username")
#                 new_email = st.text_input("Email", key="signup_email")
#                 new_password = st.text_input("Password", type="password", key="signup_password")
#                 confirm_password = st.text_input("Confirm Password", type="password")
#                 user_type = st.selectbox("Account Type", ["regular", "admin"])

#                 signup_submitted = st.form_submit_button("Create Account")

#                 if signup_submitted:
#                     if new_username and new_email and new_password and confirm_password:
#                         if new_password == confirm_password:
#                             success, message = signup_user(new_username, new_email, new_password, user_type)
#                             if success:
#                                 st.success(message)
#                                 st.info("Please go to the Login tab to sign in.")
#                             else:
#                                 st.error(message)
#                         else:
#                             st.error("Passwords do not match")
#                     else:
#                         st.error("Please fill in all fields")

#     else:
#         # Dashboard based on user type
#         st.sidebar.success(f"Logged in as: {st.session_state.username} ({st.session_state.user_type})")
#         if st.sidebar.button("Logout"):
#             logout()
#             st.rerun()

#         if st.session_state.user_type == "admin":
#             show_admin_dashboard()
#         else:
#             show_user_dashboard()

# def show_admin_dashboard():
#     st.title("ðŸ‘¨â€ðŸ’¼ Admin Dashboard")
#     st.markdown("---")

#     # File Upload Section
#     st.header("ðŸ“ File Upload & Processing")

#     # Model initialization section for txt files
#     st.subheader("ðŸ¤– AI Model Status")
#     col1, col2 = st.columns([2, 1])

#     with col1:
#         st.info("For TXT file uploads, the AI model needs to be initialized first. This is a one-time process that may take a few minutes.")

#     with col2:
#         if st.button("Initialize AI Model"):
#             with st.spinner("Initializing AI model... This may take a few minutes on first run."):
#                 try:
#                     headers = {"Authorization": f"Bearer {st.session_state.token}"}
#                     response = requests.post(
#                         f"{BACKEND_URL}/admin/init-model",
#                         headers=headers,
#                         timeout=600  # 10 minutes timeout for model initialization
#                     )

#                     if response.status_code == 200:
#                         result = response.json()
#                         if result.get('success'):
#                             st.success("âœ… AI model initialized successfully!")
#                         else:
#                             st.warning(f"âš ï¸ {result.get('message', 'Model initialization completed with warnings')}")
#                     else:
#                         st.error(f"âŒ Model initialization failed: {response.json().get('message', 'Unknown error')}")

#                 except requests.exceptions.Timeout:
#                     st.error("â±ï¸ Model initialization timed out. The process may still be running in the background.")
#                 except Exception as e:
#                     st.error(f"âŒ Error initializing model: {str(e)}")

#     st.markdown("---")

#     uploaded_file = st.file_uploader(
#         "Choose a file to upload",
#         type=['csv', 'txt'],
#         help="Upload CSV files for database storage or TXT files for vector database"
#     )

#     if uploaded_file is not None:
#         file_details = {
#             "filename": uploaded_file.name,
#             "filetype": uploaded_file.type,
#             "filesize": uploaded_file.size
#         }

#         st.write("File Details:")
#         st.json(file_details)

#         if st.button("Process File"):
#             with st.spinner("Processing file..."):
#                 try:
#                     files = {"file": uploaded_file.getvalue()}
#                     headers = {"Authorization": f"Bearer {st.session_state.token}"}

#                     # Set longer timeout for file processing (especially for txt files that need model download)
#                     timeout_seconds = 600  # 10 minutes timeout

#                     response = requests.post(
#                         f"{BACKEND_URL}/admin/upload",
#                         files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
#                         headers=headers,
#                         timeout=timeout_seconds
#                     )

#                     if response.status_code == 200:
#                         result = response.json()
#                         st.success("File processed successfully!")
#                         st.json(result)
#                     else:
#                         error_msg = "Unknown error"
#                         try:
#                             error_msg = response.json().get('message', 'Unknown error')
#                         except:
#                             error_msg = f"HTTP {response.status_code}: {response.text}"
#                         st.error(f"Processing failed: {error_msg}")

#                 except requests.exceptions.Timeout:
#                     st.error("Request timed out. File processing is taking longer than expected. This may happen on first upload of txt files as the system downloads required models. Please try again in a few minutes.")
#                 except requests.exceptions.ConnectionError as e:
#                     st.error(f"Connection error: {str(e)}. Please check if the backend server is running and try again.")
#                 except requests.exceptions.RequestException as e:
#                     st.error(f"Request error: {str(e)}")
#                 except Exception as e:
#                     st.error(f"Unexpected error: {str(e)}")

#     # Database Management Section
#     st.markdown("---")
#     st.header("ðŸ—„ï¸ Database Management")

#     col1, col2 = st.columns(2)

#     with col1:
#         if st.button("View Tables"):
#             try:
#                 headers = {"Authorization": f"Bearer {st.session_state.token}"}
#                 response = requests.get(f"{BACKEND_URL}/admin/tables", headers=headers)
#                 if response.status_code == 200:
#                     tables = response.json()
#                     st.write("Database Tables:")
#                     for table in tables.get('tables', []):
#                         st.write(f"- {table}")
#                 else:
#                     st.error("Failed to fetch tables")
#             except Exception as e:
#                 st.error(f"Error: {str(e)}")

#     with col2:
#         if st.button("View Vector Store"):
#             try:
#                 headers = {"Authorization": f"Bearer {st.session_state.token}"}
#                 response = requests.get(f"{BACKEND_URL}/admin/vectors", headers=headers)
#                 if response.status_code == 200:
#                     vectors = response.json()
#                     st.write("Vector Database Info:")
#                     st.json(vectors)
#                 else:
#                     st.error("Failed to fetch vector info")
#             except Exception as e:
#                 st.error(f"Error: {str(e)}")

# def show_user_dashboard():
#     st.title("ðŸ‘¤ User Dashboard")
#     st.markdown("---")

#     # Chat Interface
#     st.header("ðŸ’¬ Chat Interface")

#     # Initialize chat history
#     if "messages" not in st.session_state:
#         st.session_state.messages = []

#     # Display chat messages
#     for message in st.session_state.messages:
#         with st.chat_message(message["role"]):
#             st.markdown(message["content"])

#     # Chat input
#     if prompt := st.chat_input("What would you like to know?"):
#         print(prompt)
#         # Add user message to chat history
#         st.session_state.messages.append({"role": "user", "content": prompt})
#         print(st.session_state.messages)
#         with st.chat_message("user"):
#             st.markdown(prompt)

#         # Get bot response
#         with st.chat_message("assistant"):
#             with st.spinner("Thinking..."):
#                 try:
#                     headers = {"Authorization": f"Bearer {st.session_state.token}"}
#                     response = requests.post(
#                         f"{BACKEND_URL}/user/chat",
#                         json={"message": prompt},
#                         headers=headers
#                     )
#                     print("response ",response, response.json())
#                     if response.status_code == 200:
#                         bot_response = response.json().get('response', 'Sorry, I could not process your request.')
#                     else:
#                         bot_response = "Sorry, there was an error processing your request."


#                     st.markdown(bot_response)
#                     st.session_state.messages.append({"role": "assistant", "content": bot_response})

#                 except Exception as e:
#                     error_msg = f"Error: {str(e)}"
#                     st.markdown(error_msg)
#                     st.session_state.messages.append({"role": "assistant", "content": error_msg})

# if __name__ == "__main__":
#     main()


import streamlit as st
import requests
import json
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="ChatBot Application",
    page_icon="🤖",
    layout="wide"
)

# Backend URL
BACKEND_URL = "http://localhost:5000"

def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'token' not in st.session_state:
        st.session_state.token = None

def login_user(username, password, user_type):
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={
                "username": username,
                "password": password,
                "user_type": user_type
            }
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.logged_in = True
            st.session_state.user_type = user_type
            st.session_state.username = username
            st.session_state.token = data.get('token')
            return True, "Login successful!"
        else:
            return False, response.json().get('message', 'Login failed')
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def signup_user(username, email, password, user_type):
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/signup",
            json={
                "username": username,
                "email": email,
                "password": password,
                "user_type": user_type
            }
        )
        if response.status_code == 201:
            return True, "Account created successfully!"
        else:
            return False, response.json().get('message', 'Signup failed')
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def logout():
    st.session_state.logged_in = False
    st.session_state.user_type = None
    st.session_state.username = None
    st.session_state.token = None

def load_chat_history():
    """Load chat history from backend"""
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.get(f"{BACKEND_URL}/user/chat/history", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"user_id": "unknown", "history": [], "created_at": datetime.now().isoformat()}
    except Exception as e:
        st.error(f"Error loading chat history: {str(e)}")
        return {"user_id": "unknown", "history": [], "created_at": datetime.now().isoformat()}

def display_chat_history_sidebar():
    """Display chat history in sidebar"""
    with st.sidebar:
        st.header("📄 Chat History")

        # Load chat history
        chat_data = load_chat_history()

        if chat_data and chat_data.get("history"):
            # Display chat history metadata
            st.subheader("History Info")
            st.write(f"**User ID:** {chat_data.get('user_id', 'Unknown')}")
            st.write(f"**Total Messages:** {len(chat_data.get('history', []))}")
            st.write(f"**Created:** {chat_data.get('created_at', 'Unknown')[:10]}")
            st.write(f"**Last Updated:** {chat_data.get('last_updated', 'Unknown')[:10]}")

            # Download chat history as JSON
            st.subheader("Download History")
            json_str = json.dumps(chat_data, indent=2, ensure_ascii=False)
            st.download_button(
                label="📥 Download JSON",
                data=json_str,
                file_name=f"chat_history_{st.session_state.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

            # Display recent messages
            st.subheader("Recent Messages")
            recent_messages = chat_data.get("history", [])[-10:]  # Last 10 messages

            for i, msg in enumerate(recent_messages):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")[:16]  # Show date and time

                if role == "user":
                    st.markdown(f"**👤 User** _{timestamp}_")
                    st.markdown(f"> {content[:100]}{'...' if len(content) > 100 else ''}")
                else:
                    agent = msg.get("agent", "Bot")
                    confidence = msg.get("confidence", 0)
                    st.markdown(f"**🤖 {agent}** _{timestamp}_ (Conf: {confidence:.2f})")
                    st.markdown(f"> {content[:100]}{'...' if len(content) > 100 else ''}")

                st.markdown("---")
        else:
            st.info("No chat history available yet. Start a conversation!")

def main():
    init_session_state()

    if not st.session_state.logged_in:
        # Login/Signup Interface (same as before)
        st.title("🤖 ChatBot Application")
        st.markdown("---")

        # Create tabs for Login and Signup
        login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

        with login_tab:
            st.header("Login")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("🔐 Regular User Login", use_container_width=True, type="primary"):
                    st.session_state.login_type = "regular"

            with col2:
                if st.button("👨‍💼 Admin User Login", use_container_width=True, type="secondary"):
                    st.session_state.login_type = "admin"

            if 'login_type' in st.session_state:
                st.markdown("---")
                with st.form("login_form"):
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    submitted = st.form_submit_button("Login")

                    if submitted:
                        if username and password:
                            success, message = login_user(username, password, st.session_state.login_type)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                        else:
                            st.error("Please fill in all fields")

        with signup_tab:
            st.header("Create New Account")
            with st.form("signup_form"):
                new_username = st.text_input("Username", key="signup_username")
                new_email = st.text_input("Email", key="signup_email")
                new_password = st.text_input("Password", type="password", key="signup_password")
                confirm_password = st.text_input("Confirm Password", type="password")
                user_type = st.selectbox("Account Type", ["regular", "admin"])
                signup_submitted = st.form_submit_button("Create Account")

                if signup_submitted:
                    if new_username and new_email and new_password and confirm_password:
                        if new_password == confirm_password:
                            success, message = signup_user(new_username, new_email, new_password, user_type)
                            if success:
                                st.success(message)
                                st.info("Please go to the Login tab to sign in.")
                            else:
                                st.error(message)
                        else:
                            st.error("Passwords do not match")
                    else:
                        st.error("Please fill in all fields")

    else:
        # Dashboard based on user type
        st.sidebar.success(f"Logged in as: {st.session_state.username} ({st.session_state.user_type})")

        # Display chat history in sidebar for all users
        display_chat_history_sidebar()

        if st.sidebar.button("Logout"):
            logout()
            st.rerun()

        if st.session_state.user_type == "admin":
            show_admin_dashboard()
        else:
            show_user_dashboard()

def show_admin_dashboard():
    st.title("👨‍💼 Admin Dashboard")
    st.markdown("---")

    # File Upload Section (same as before)
    st.header("📁 File Upload & Processing")

    # Model initialization section for txt files
    st.subheader("🤖 AI Model Status")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.info("For TXT file uploads, the AI model needs to be initialized first. This is a one-time process that may take a few minutes.")

    with col2:
        if st.button("Initialize AI Model"):
            with st.spinner("Initializing AI model... This may take a few minutes on first run."):
                try:
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    response = requests.post(
                        f"{BACKEND_URL}/admin/init-model",
                        headers=headers,
                        timeout=600
                    )

                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            st.success("✅ AI model initialized successfully!")
                        else:
                            st.warning(f"⚠️ {result.get('message', 'Model initialization completed with warnings')}")
                    else:
                        st.error(f"❌ Model initialization failed: {response.json().get('message', 'Unknown error')}")
                except requests.exceptions.Timeout:
                    st.error("⏱️ Model initialization timed out. The process may still be running in the background.")
                except Exception as e:
                    st.error(f"❌ Error initializing model: {str(e)}")

    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Choose a file to upload",
        type=['csv', 'txt'],
        help="Upload CSV files for database storage or TXT files for vector database"
    )

    if uploaded_file is not None:
        file_details = {
            "filename": uploaded_file.name,
            "filetype": uploaded_file.type,
            "filesize": uploaded_file.size
        }

        st.write("File Details:")
        st.json(file_details)

        if st.button("Process File"):
            with st.spinner("Processing file..."):
                try:
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    timeout_seconds = 600

                    response = requests.post(
                        f"{BACKEND_URL}/admin/upload",
                        files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                        headers=headers,
                        timeout=timeout_seconds
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.success("File processed successfully!")
                        st.json(result)
                    else:
                        error_msg = "Unknown error"
                        try:
                            error_msg = response.json().get('message', 'Unknown error')
                        except:
                            error_msg = f"HTTP {response.status_code}: {response.text}"
                        st.error(f"Processing failed: {error_msg}")
                except requests.exceptions.Timeout:
                    st.error("Request timed out. File processing is taking longer than expected. This may happen on first upload of txt files as the system downloads required models. Please try again in a few minutes.")
                except requests.exceptions.ConnectionError as e:
                    st.error(f"Connection error: {str(e)}. Please check if the backend server is running and try again.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Request error: {str(e)}")
                except Exception as e:
                    st.error(f"Unexpected error: {str(e)}")

    # Database Management Section
    st.markdown("---")
    st.header("🗄️ Database Management")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("View Tables"):
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(f"{BACKEND_URL}/admin/tables", headers=headers)
                if response.status_code == 200:
                    tables = response.json()
                    st.write("Database Tables:")
                    for table in tables.get('tables', []):
                        st.write(f"- {table}")
                else:
                    st.error("Failed to fetch tables")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    with col2:
        if st.button("View Vector Store"):
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(f"{BACKEND_URL}/admin/vectors", headers=headers)
                if response.status_code == 200:
                    vectors = response.json()
                    st.write("Vector Database Info:")
                    st.json(vectors)
                else:
                    st.error("Failed to fetch vector info")
            except Exception as e:
                st.error(f"Error: {str(e)}")

def show_user_dashboard():
    st.title("👤 User Dashboard")
    st.markdown("---")

    # Chat Interface
    st.header("💬 Chat Interface")
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🗑️ Clear Chat", type="secondary", help="Clear all chat messages"):
            # Clear frontend chat history
            st.session_state.messages = []
            st.success("Chat history cleared!")
            st.rerun()

    # Initialize chat history from backend
    if "messages" not in st.session_state:
        chat_data = load_chat_history()
        st.session_state.messages = []
        # Convert backend history to frontend format
        for msg in chat_data.get("history", []):
            if msg.get("role") in ["user", "assistant"]:
                st.session_state.messages.append({
                    "role": msg.get("role"),
                    "content": msg.get("content", "")
                })

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    response = requests.post(
                        f"{BACKEND_URL}/user/chat",
                        json={"message": prompt},
                        headers=headers
                    )

                    if response.status_code == 200:
                        bot_response = response.json().get('response', 'Sorry, I could not process your request.')
                    else:
                        bot_response = "Sorry, there was an error processing your request."

                    st.markdown(bot_response)
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.markdown(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    main()
