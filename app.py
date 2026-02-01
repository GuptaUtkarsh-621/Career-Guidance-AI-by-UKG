import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import plotly.express as px
import sqlite3
import hashlib
from datetime import datetime
import pyttsx3

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="CareerAI Pro", layout="wide")

# --- 2. DATABASE SETUP ---
conn = sqlite3.connect('final_mca_db.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
c.execute('''CREATE TABLE IF NOT EXISTS results 
             (username TEXT, career TEXT, logical INTEGER, coding INTEGER, 
              communication INTEGER, creativity INTEGER, timestamp TEXT)''')
conn.commit()

# --- 3. SECURITY (Hashing) ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

# --- 4. ML MODEL TRAINING ---
@st.cache_resource
def train_model():
    data = {
        'Logical': [90, 60, 80, 50, 95, 40, 70, 85, 45, 65, 30, 88, 92, 35, 78],
        'Coding': [95, 40, 85, 20, 90, 10, 30, 80, 15, 50, 10, 92, 96, 5, 82],
        'Comm': [50, 90, 60, 85, 40, 95, 70, 55, 80, 75, 95, 45, 40, 98, 55],
        'Crea': [40, 70, 50, 90, 30, 95, 80, 45, 85, 60, 90, 40, 30, 92, 45],
        'Role': ['Software Engineer', 'HR Manager', 'Data Scientist', 'Graphic Designer', 
                'Backend Dev', 'Public Speaker', 'Digital Marketer', 'ML Engineer', 
                'UI/UX Designer', 'Project Manager', 'Content Creator', 'Full Stack Dev',
                'Cybersecurity Specialist', 'Event Manager', 'Cloud Architect']
    }
    df = pd.DataFrame(data)
    model = RandomForestClassifier(n_estimators=100).fit(df.drop('Role', axis=1), df['Role'])
    return model, df

model, df = train_model()

# --- 5. APP UI & AUTH ---
st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>🚀 CareerAI: Professional Guidance System</h1>", unsafe_allow_html=True)
st.write("---")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

menu = ["Home", "Login", "SignUp"]
choice = st.sidebar.selectbox("Navigation Menu", menu)

if choice == "Home":
    st.subheader("Welcome to the AI Career Portal")
    st.info("Please Login or SignUp from the sidebar to access assessment tools.")

elif choice == "SignUp":
    st.subheader("Create New Account")
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type='password')
    if st.button("Register Now"):
        try:
            c.execute('INSERT INTO users VALUES (?,?)', (new_user, make_hashes(new_pass)))
            conn.commit()
            st.success("Registration Successful! Please Login.")
        except:
            st.error("Username already exists.")

elif choice == "Login":
    st.subheader("Login Section")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type='password')
    if st.button("Secure Login"):
        c.execute('SELECT password FROM users WHERE username=?', (user,))
        data = c.fetchone()
        if data and check_hashes(pwd, data[0]):
            st.session_state['logged_in'] = True
            st.session_state['user'] = user
            st.rerun()
        else:
            st.error("Invalid Credentials.")

# --- 6. PROTECTED DASHBOARD ---
if st.session_state['logged_in']:
    st.sidebar.success(f"Welcome, {st.session_state['user']}")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["🎯 Skill Analysis", "📜 My Records", "📊 Market Trends"])

    with tab1:
        col1, col2 = st.columns([1, 1.2])
        with col1:
            st.subheader("Adjust Your Skills")
            l = st.slider("Logical Reasoning", 0, 100, 50)
            co = st.slider("Coding Proficiency", 0, 100, 50)
            cm = st.slider("Communication Skills", 0, 100, 50)
            cr = st.slider("Creativity Level", 0, 100, 50)
            
            if st.button("Analyze Career"):
                # Prediction & Probability
                prediction = model.predict([[l, co, cm, cr]])[0]
                probs = model.predict_proba([[l, co, cm, cr]])[0]
                max_prob = max(probs) * 100
                
                curr_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                c.execute('INSERT INTO results VALUES (?,?,?,?,?,?,?)', 
                         (st.session_state['user'], prediction, l, co, cm, cr, curr_time))
                conn.commit()
                
                st.balloons()
                st.success(f"### Suggested: {prediction}")
                st.metric(label="AI Confidence Score", value=f"{max_prob:.2f}%")
                
                # Expert Recommendations (Analysis)
                st.subheader("💡 Expert Recommendations")
                if co < 60:
                    st.warning("⚠️ Coding score kam hai. DSA par dhyan dein.")
                if cm < 60:
                    st.warning("⚠️ Communication skills sudharein.")
                if l > 80 and co > 80:
                    st.info("🌟 Excellence Alert: High-end AI roles ke liye fit hain!")

                # Voice Output
                try:
                    engine = pyttsx3.init()
                    engine.say(f"Recommended career is {prediction}")
                    engine.runAndWait()
                except:
                    pass

        with col2:
            st.subheader("Analysis Visuals")
            # Radar Chart
            skills_df = pd.DataFrame(dict(r=[l, co, cm, cr], 
                                          theta=['Logic', 'Coding', 'Comm', 'Creativity']))
            fig = px.line_polar(skills_df, r='r', theta='theta', line_close=True, color_discrete_sequence=['#ff4b4b'])
            fig.update_traces(fill='toself')
            st.plotly_chart(fig, use_container_width=True)

            # Benchmark Comparison
            benchmark_data = pd.DataFrame({
                'Metric': ['Logic', 'Coding', 'Comm', 'Crea'],
                'Your Score': [l, co, cm, cr],
                'Industry Avg': [75, 70, 65, 60]
            })
            fig_comp = px.bar(benchmark_data, x='Metric', y=['Your Score', 'Industry Avg'], barmode='group')
            st.plotly_chart(fig_comp, use_container_width=True)

    with tab2:
        st.subheader(f"Historical Data for {st.session_state['user']}")
        
        # Database se user ka sara data fetch karna
        hist_df = pd.read_sql_query(f"SELECT * FROM results WHERE username='{st.session_state['user']}' ORDER BY timestamp DESC", conn)
        
        if not hist_df.empty:
            # Table display karna
            st.dataframe(hist_df, use_container_width=True)
            
            st.write("---")
            # --- DOWNLOAD FUNCTIONALITY ---
            # Data ko CSV format mein convert karna
            csv = hist_df.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="📥 Download My Career Report (CSV)",
                data=csv,
                file_name=f"{st.session_state['user']}_career_report.csv",
                mime="text/csv",
                help="Click here to download your full assessment history as a CSV file."
            )
        else:
            st.warning("Abhi tak koi records nahi mile. Pehle 'Skill Analysis' tab mein jaakar prediction karein!")

    with tab3:
        st.subheader("Industry Insights")
        fig_bar = px.bar(df, x='Role', y='Coding', color='Role')
        st.plotly_chart(fig_bar, use_container_width=True)