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

st.title('Datalab Työt')

left_column, right_column = st.columns([3, 1])

with left_column:
    jobs_df = get_jobs_data()
    for index, row in jobs_df.iterrows():
        st.subheader(row['JobName'])  # Change to subheader for job titles
        if st.button("Valitse työ", key=f"select_job_{row['JobID']}"):
            st.session_state.selected_job_id = row['JobID']
            selected_job = jobs_df[jobs_df['JobID'] == st.session_state.selected_job_id].iloc[0]
            st.write(f"**Työn Kuvaus:** {selected_job['JobDescription']}")
            
            if st.session_state.logged_in:
                hours = st.number_input("Tehdyt työtunnit", min_value=0.0, max_value=100.0, step=0.5, key=f"hours_{row['JobID']}")
                if st.button("Lisää tunnit", key=f"add_hours_{row['JobID']}"):
                    username = st.session_state.user[0]  
                    job_id = int(selected_job['JobID'])  
                    insert_hours(username, job_id, hours)
                    st.success("Tunnit kirjattu onnistuneesti")
        st.divider()  # Add a divider after each job

with right_column:
    if not st.session_state.logged_in:
        st.subheader("Kirjaudu sisään")  # Use subheader for login section title
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
                st.experimental_rerun()
            else:
                st.error('Login failed. Check your username and password.')
    else:
        st.subheader("Olet kirjautunut sisään")  # Use subheader for logged-in message
