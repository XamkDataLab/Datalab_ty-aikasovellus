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
    query = "INSERT INTO JobHours (JobID, Username, Hours) VALUES (?, ?, ?)"
    cursor.execute(query, job_id, user_id, hours)
    conn.commit()
    conn.close()

st.title('Datalab työt')
jobs_df = get_jobs_data()
st.dataframe(jobs_df)

st.sidebar.title('User Login')

with st.sidebar.form("login_form", clear_on_submit=True):
    username = st.text_input('Username', max_chars=20)
    password = st.text_input('Password', type='password', max_chars=20)
    submit_button = st.form_submit_button('Login')

if submit_button:
    conn = create_connection()
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    cursor.execute("SELECT * FROM Users WHERE Username = ? AND Password = ?", username, hashed_password)
    user = cursor.fetchone()
    conn.close()

    if user:
        st.sidebar.success('Kirjautuminen onnistui')
        job_list = jobs_df['JobName'].tolist()  
        selected_job = st.selectbox("Valitse työ", job_list)

        if selected_job:
            hours = st.number_input("Tehdyt työtunnit", min_value=0.0, max_value=100.0, step=0.5)
            if st.button("Lisää tunnit"):
                
                job_id = jobs_df[jobs_df['JobName'] == selected_job]['JobID'].iloc[0]  
                user_id = user['Username']  
                insert_hours(job_id, user_id, hours)
                st.success("Tunnit kirjattu onnistuneesti")

    else:
        st.sidebar.error('Login failed. Check your username and password.')

