import os
from tempfile import NamedTemporaryFile
import base64

import streamlit as st
import extra_streamlit_components as stx
from st_supabase_connection import SupabaseConnection
import auth0_component as ac
from dotenv import load_dotenv
from openai import OpenAI
import fitz


load_dotenv()

st.set_page_config(page_title=None, page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)
st.markdown("""
<style>
    #MainMenu, header, footer {visibility: hidden;}
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
    }   
</style>
""",unsafe_allow_html=True)

st_supabase_client = st.connection(
    name="resumeai",
    type=SupabaseConnection,
    ttl=None,
    url=os.getenv("SUPABASE_URL"), # not needed if provided as a streamlit secret
    key=os.getenv("SUPABASE_KEY"), # not needed if provided as a streamlit secret
)

def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

if "current_step" not in st.session_state:
    st.session_state['current_step'] = 0
if "resume" not in st.session_state:
    st.session_state['resume'] = None
if "jd" not in st.session_state:
    st.session_state['jd'] = None
steps = ["Upload Resume", "Upload Job Description", "Get Feedback"]

def check_auth():
    if not cookie_manager.get("user"):
        user_info = ac.login_button(os.getenv("AUTH0_CLIENT_ID"), os.getenv("AUTH0_DOMAIN"))
        if user_info:
            cookie_manager.set("user", user_info)
        st.write(user_info)
    else:
        user_info = ac.isAuth(cookie_manager.get("user"), os.getenv("AUTH0_DOMAIN"))
        st.write(user_info)
        st.write(cookie_manager.get("user"))

def check_auth_bak():
    if not cookie_manager.get("auth"):
        tabs = st.tabs(["Login", "Signup"])
        with tabs[0]:
            email = st.text_input("Email", key="loginemail")
            password = st.text_input("Password", type="password", key="loginpassword")
            login = st.button("Login")
            if login:
                res = st_supabase_client.auth.sign_in_with_password(dict(email=email, password=password))
                st.write(res)     
                cookie_manager.set("auth", res.session.access_token)
        with tabs[1]:
            email = st.text_input("Email", key="email")
            password = st.text_input("Password", type="password", key="password")
            signup = st.button("Signup")
            if signup:
                res = st_supabase_client.auth.sign_up(dict(email=email, password=password))
                st.success('You have successfully signed up! Please check your email to verify your account.')
    else:
        st.write(cookie_manager.get("auth"))
        try:
            data = st_supabase_client.auth.get_user(cookie_manager.get("auth"))
            st.write(data)
        except Exception as e:
            cookie_manager.delete("auth")
    return None

def increment_step(step):
    st.session_state['current_step'] += step
    if st.session_state['current_step'] > len(steps) - 1:
        st.session_state['current_step'] = 0

def control_buttons():
    cols = st.columns(12)
    cols[0].button("Previous", on_click=increment_step, args=(-1,))
    cols[11].button("Next", on_click=increment_step, args=(1,))

def display_pdf(pdf_file, ele):
    bytes_data = pdf_file.getvalue()
    base64_pdf = base64.b64encode(bytes_data).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="850" type="application/pdf"></iframe>'
    ele.markdown(pdf_display, unsafe_allow_html=True)

def upload_resume():
    cols = st.columns(2)
    uploaded_file = cols[0].file_uploader("Upload a file")
    if uploaded_file:
        bytes_data = uploaded_file.read()
        with NamedTemporaryFile(delete=False) as tmp:  # open a named temporary file
            tmp.write(bytes_data)  # write data from the uploaded file into it
            
            if uploaded_file.type == "application/pdf":
                doc = fitz.open(tmp.name)
                text = ""
                for page in doc:
                    text += page.get_text()
                #st.write(text)
        os.remove(tmp.name)  # remove temp file
        st.session_state['resume'] = uploaded_file
        display_pdf(uploaded_file, cols[1])
    control_buttons()

def upload_jd():
    cols = st.columns(2)
    jd = cols[0].text_area("Job Description")
    display_pdf(st.session_state['resume'], cols[1])
    if jd:
        st.session_state['jd'] = jd
    control_buttons()

def ask_gpt():
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "You will be provided with a job description and a resume."
                    "Provide positive and constructive feedback on the resume in bullet point format."
                    "The feedback should be tailored to the job description."
                ),
            },
            {
                "role": "user",
                "content": f'''
                job_description: """{st.session_state['jd']}"""

                resume: """{st.session_state['resume']}"""
                ''',
            }
        ],
        model="gpt-3.5-turbo-0125",
    )
    st.write(chat_completion.choices[0].message.content)

with st.sidebar:
    st.button("Logout", on_click=cookie_manager.delete, args=("auth",))
if check_auth():
    if st.session_state['current_step'] == 0:
        upload_resume()
    elif st.session_state['current_step'] == 1:
        upload_jd()
    elif st.session_state['current_step'] == 2:
        ask_gpt()