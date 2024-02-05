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
    return pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';PORT=1433;DATABASE=' + database + ';UID=' + username + ';PWD=' + password)

def get_jobs_data():
    conn = create_connection()
    query = "SELECT * FROM Jobs"  
    df = pd.read_sql(query, conn)
    conn.close()
    return df
    
def insert_hours(job_id, user_id, hours):
    conn = create_connection()
    cursor = conn.cursor()
    query = "INSERT INTO JobHours (Username, JobID, Hours) VALUES (?, ?, ?)"
    cursor.execute(query, job_id, user_id, hours)
    conn.commit()
    conn.close()

if 'selected_job_id' not in st.session_state:
    st.session_state.selected_job_id = None

def show_job_details(job_id):
    """Function to set the selected job ID in session state."""
    st.session_state.selected_job_id = job_id
    
#layout
left_col, right_col = st.columns([2, 1])

with right_col:
    with st.form("login_form", clear_on_submit=True):
        username_input = st.text_input('Käyttäjänimi', max_chars=15)
        password_input = st.text_input('Salasana', type='password', max_chars=15)
        submit_button = st.form_submit_button('Kirjaudu')

st.title('Datalab työt')
jobs_df = get_jobs_data()

for index, row in jobs_df.iterrows():
    with st.container():
        left, right = st.columns([4, 1])
        left.write(f"{row['JobName']}")
        select_button = right.button("Valitse", key=row['JobID'])
        if select_button:
            show_job_details(row['JobID'])

if st.session_state.selected_job_id is not None:
    selected_job = jobs_df[jobs_df['JobID'] == st.session_state.selected_job_id].iloc[0]
    st.write(f"Valittu Työ: {selected_job['JobName']}")
    st.write(f"Työn Kuvaus: {selected_job['JobDescription']}")
    
if submit_button:
    conn = create_connection()
    cursor = conn.cursor()
    hashed_password = hash_password(password_input) 
    cursor.execute("SELECT * FROM Users WHERE Username = ? AND Password = ?", username_input, hashed_password)
    user = cursor.fetchone()
    conn.close()

    if user:
        st.sidebar.success('Kirjautuminen onnistui')
        if st.session_state.selected_job_id is not None:
            selected_job = jobs_df[jobs_df['JobID'] == st.session_state.selected_job_id].iloc[0]
            hours = st.number_input("Tehdyt työtunnit", min_value=0.0, max_value=100.0, step=0.5)
            if st.button("Lisää tunnit"):
                job_id = selected_job['JobID']
                user_id = user[1]  
                insert_hours(job_id, user_id, hours)
                st.success("Tunnit kirjattu onnistuneesti")
    else:
        st.sidebar.error('Login failed. Check your username and password.')
