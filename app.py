import streamlit as st
import pyodbc
import hashlib

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Establishing database connection
def create_connection():
    driver = st.secrets["driver"]
    server = st.secrets["server"]
    database = st.secrets["database"]
    username = st.secrets["username"]
    password = st.secrets["password"]
    return pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';PORT=1433;DATABASE=' + database + ';UID=' + username + ';PWD=' + password)

# Streamlit app for sign-in
st.title('User Login')

with st.form("login_form", clear_on_submit=True):
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')
    submit_button = st.form_submit_button('Login')

if submit_button:
    conn = create_connection()
    cursor = conn.cursor()
    
    # Hash the input password to compare with the stored hash
    hashed_password = hash_password(password)

    cursor.execute("SELECT * FROM Users WHERE Username = ? AND Password = ?", username, hashed_password)
    user = cursor.fetchone()

    if user:
        st.success('Login successful!')
        # Place your job tracking code or other functionalities here
    else:
        st.error('Login failed. Check your username and password.')
    
    conn.close()
