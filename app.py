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
    st.session_state['selected_job_id'] = None
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = None

if not st.session_state.logged_in:
    cols = st.columns([1, 1])
    with cols[0]:
        username_input = st.text_input('Käyttäjänimi', key='username')
    with cols[1]:
        password_input = st.text_input('Salasana', type='password', key='password')
    if st.button('Kirjaudu', key='login'):
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
    st.subheader(f"Olet kirjautunut sisään: {st.session_state.user[0]}")
    
st.title('Datalab Työt')

jobs_df = get_jobs_data()

left_column, right_column = st.columns([3, 1])

with left_column:
    for index, row in jobs_df.iterrows():
        with st.container():  
            st.subheader(row['JobName'])
            select_button = st.button("Valitse työ", key=f"select_job_{row['JobID']}")

            if st.session_state.selected_job_id == row['JobID']:
                st.write(f"**Työn Kuvaus:** {row['JobDescription']}")

                if st.session_state.logged_in:
                    hours = st.number_input("Tehdyt työtunnit", min_value=0.0, max_value=100.0, step=0.5, key=f"hours_input_{row['JobID']}")
                    if st.button("Lisää tunnit", key=f"add_hours_{row['JobID']}"):
                        username = st.session_state.user[0]
                        job_id = row['JobID']
                        insert_hours(username, job_id, hours)
                        st.success("Tunnit kirjattu onnistuneesti")
            
            if select_button:
                st.session_state.selected_job_id = row['JobID']
                st.experimental_rerun()

        st.divider()


