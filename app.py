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

def create_data_connection():
    driver2 = st.secrets["driver2"]
    server2 = st.secrets["server2"]
    database2 = st.secrets["database2"]
    username2 = st.secrets["username2"]
    password2 = st.secrets["password2"]
    conn_str = f'DRIVER={driver2};SERVER={server2};PORT=1433;DATABASE={database2};UID={username2};PWD={password2}'
    return pyodbc.connect(conn_str)

def get_jobs_data():
    conn = create_connection()
    query = "SELECT * FROM Jobs"  
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_job_main_table_data(job_id):
    if job_id in jobs_df['JobID'].values:
        main_table_name = jobs_df.loc[jobs_df['JobID'] == job_id, 'mainTable'].values[0]
        if pd.isna(main_table_name):
            return None, None, None  
        conn = create_data_connection()
        
        top_query = f"SELECT Top 100 * FROM [{main_table_name}]"
        top_df = pd.read_sql(top_query, conn)
        
        count_query = f"SELECT COUNT(*) FROM [{main_table_name}]"
        cursor = conn.cursor()
        cursor.execute(count_query)
        total_row_count = cursor.fetchone()[0]
        
        conn.close()
        
        column_count = len(top_df.columns)
        
        return top_df, total_row_count, column_count
    else:
        print(f"No mainTable found for job_id: {job_id}")
        return None, None, None

    
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
            st.error('Kirjautuminen epäonnistui. Tarkasta käyttäjätunnus ja salasana.')
else:
    st.subheader(f"Olet kirjautunut sisään: {st.session_state.user[0]}")

st.title('Datalab Työt')
st.markdown('Tässä näkyvät Data-analytiikkakoulutuksen datalabrassa olevat työt. Jos olet kiinnostunut tekemään harjoittelun datalabrassa, ota yhteyttä tällä lomakkeella: [datalab työnhakulomake](https://forms.office.com/Pages/ResponsePage.aspx?id=vNbINpjpkEGmn8E0JAY0Y0qH5dIS22RHnqhKgPDmZkNUQU83UlM2VkVHQkxIVUg4RzZJRVBMM0wwRC4u). Kirjautuneet käyttäjät voivat tarkastella aineistoja sekä lisätä tunteja työtehtäville', unsafe_allow_html=True)
st.divider()
jobs_df = get_jobs_data()

with st.container():
    for index, row in jobs_df.iterrows():
        st.subheader(row['JobName'])

        if st.button("Työn tiedot", key=f"detail_info_{row['JobID']}"):
            st.session_state.selected_job_id = row['JobID']
            st.write(f"**Työn Kuvaus:** {row['JobDescription']}")

            if st.session_state.logged_in:
                hours = st.number_input("Tehdyt työtunnit", min_value=0.0, max_value=100.0, step=0.5, key=f"hours_input_{row['JobID']}")
                if st.button("Lisää tunnit", key=f"add_hours_{row['JobID']}"):
                    username = st.session_state.user[0]
                    job_id = row['JobID']
                    insert_hours(username, job_id, hours)
                    st.success("Tunnit kirjattu onnistuneesti")

        if st.session_state.logged_in and not pd.isna(row['mainTable']):
            if st.button('Näytä data', key=f"sample_data_{row['JobID']}"):
                main_table_df, total_row_count, column_count = get_job_main_table_data(row['JobID'])
                if main_table_df is not None and not main_table_df.empty:  # Correctly unpack and then check .empty
                    st.markdown(f"<b style='font-size: 20px;'>Kokonaisrivien määrä: {total_row_count}, Sarakkeiden määrä: {column_count}</b>", unsafe_allow_html=True)
                    st.write('taulukossa 100 ensimmäistä riviä')
                    st.dataframe(main_table_df)
                   
                else:
                    st.write("Ei esimerkkitietoja saatavilla.")

        st.divider()
