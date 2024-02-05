import streamlit as st
import pyodbc
import pandas as pd
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_connection():
    driver = st.secrets["driver"]
    server = st.secrets["server"]
    database = st.secrets["database"]
    username = st.secrets["username"]
    password = st.secrets["password"]
    conn_str = f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}'
    return pyodbc.connect(conn_str)

def get_jobs_data():
    conn = create_connection()
    query = "SELECT * FROM Jobs"  
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def insert_hours(username, job_id, hours):
    conn = create_connection()
    cursor = conn.cursor()
    query = "INSERT INTO JobHours (Username, JobID, Hours) VALUES (?, ?, ?)"
    cursor.execute(query, username, job_id, hours)
    conn.commit()
    conn.close()

if 'selected_job_id' not in st.session_state:
    st.session_state.selected_job_id = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None

def login_form():
    with st.sidebar:
        username_input = st.text_input('Käyttäjänimi', max_chars=15)
        password_input = st.text_input('Salasana', type='password', max_chars=15)
        submit_button = st.button('Kirjaudu')
        
        if submit_button:
            conn = create_connection()
            cursor = conn.cursor()
            hashed_password = hash_password(password_input)
            cursor.execute("SELECT * FROM Users WHERE Username = ? AND Password = ?", username_input, hashed_password)
            user = cursor.fetchone()
            conn.close()
            
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.success('Kirjautuminen onnistui')
                st.experimental_rerun()
            else:
                st.error('Login failed. Check your username and password.')

st.title('Datalab työt')
jobs_df = get_jobs_data()

for index, row in jobs_df.iterrows():
    with st.container():
        st.write(f"{row['JobName']}")
        if st.button("Näytä tiedot", key=f"details_{row['JobID']}"):
            st.session_state.selected_job_id = row['JobID']
            selected_job = jobs_df[jobs_df['JobID'] == st.session_state.selected_job_id].iloc[0]
            st.write(f"Työn Kuvaus: {selected_job['JobDescription']}")
            
            # Only show hours input for logged-in users
            if st.session_state.logged_in:
                hours = st.number_input("Tehdyt työtunnit", min_value=0.0, max_value=100.0, step=0.5, key=f"hours_{row['JobID']}")
                if st.button("Lisää tunnit", key=f"add_{row['JobID']}"):
                    username = st.session_state.user[0]  # Assuming username is the first item in the user tuple
                    insert_hours(username, selected_job['JobID'], hours)
                    st.success("Tunnit kirjattu onnistuneesti")

if not st.session_state.logged_in:
    login_form()
