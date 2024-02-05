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

with st.sidebar:
    if not st.session_state.logged_in:
        with st.form("login_form"):
            username_input = st.text_input('Käyttäjänimi', max_chars=15)
            password_input = st.text_input('Salasana', type='password', max_chars=15)
            submit_button = st.form_submit_button('Kirjaudu')

        if submit_button:
            conn = create_connection()
            cursor = conn.cursor()
            hashed_password = hash_password(password_input)
            cursor.execute("SELECT * FROM Users WHERE Username = ? AND Password = ?", username_input, hashed_password)
            user = cursor.fetchone()
            conn.close()

            if user:
                st.success('Kirjautuminen onnistui')
                st.session_state.logged_in = True
                st.session_state.user = user
            else:
                st.error('Login failed. Check your username and password.')
    else:
        st.success('You are already logged in.')
        if st.button('Log out'):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.experimental_rerun()

main_page = st.empty()

with main_page.container():
    if st.session_state.logged_in:
        if st.session_state.selected_job_id is None:
            st.title('Datalab työt')
            jobs_df = get_jobs_data()
            for index, row in jobs_df.iterrows():
                with st.container():
                    left, right = st.columns([4, 1])
                    left.write(f"{row['JobName']}")
                    select_button = right.button("Valitse", key=row['JobID'])
                    if select_button:
                        st.session_state.selected_job_id = row['JobID']
                        main_page.empty()
                        st.experimental_rerun()
        else:
            selected_job = get_jobs_data().loc[get_jobs_data()['JobID'] == st.session_state.selected_job_id].iloc[0]
            st.write(f"Valittu Työ: {selected_job['JobName']}")
            st.write(f"Työn Kuvaus: {selected_job['JobDescription']}")

            hours = st.number_input("Tehdyt työtunnit", min_value=0.0, max_value=100.0, step=0.5)
            if st.button("Lisää tunnit"):
                username = st.session_state.user[0]  # Adjust index based on your user tuple structure
                insert_hours(username, selected_job['JobID'], hours)
                st.success("Tunnit kirjattu onnistuneesti")
                st.session_state.selected_job_id = None
                main_page.empty()
                st.experimental_rerun()
