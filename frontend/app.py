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

def main():
    init_session_state()

    if not st.session_state.logged_in:
        # Login/Signup Interface
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

    # File Upload Section
    st.header("📁 File Upload & Processing")

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
                    files = {"file": uploaded_file.getvalue()}
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}

                    response = requests.post(
                        f"{BACKEND_URL}/admin/upload",
                        files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                        headers=headers
                    )
                    print(response.json())
                    if response.status_code == 200:
                        result = response.json()
                        st.success("File processed successfully!")
                        st.json(result)
                    else:
                        st.error(f"Processing failed: {response.json().get('message', 'Unknown error')}")

                except Exception as e:
                    st.error(f"Error: {str(e)}")

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

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

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
