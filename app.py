import os
from tempfile import NamedTemporaryFile
import base64

import streamlit as st
import extra_streamlit_components as stx
from streamlit_extras.stylable_container import stylable_container
#from st_supabase_connection import SupabaseConnection
import auth0_component as ac
from dotenv import load_dotenv
from openai import OpenAI
import fitz

from tweaker import st_tweaker


load_dotenv()

st.set_page_config(
    page_title="Hippo Resume", 
    page_icon="🦛", 
    layout="wide", 
    initial_sidebar_state="auto", 
    menu_items=None
)
st.markdown("""
<style>
    #MainMenu, header, footer {visibility: hidden;}
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
    }   
</style>
""",unsafe_allow_html=True)

# st_supabase_client = st.connection(
#     name="resumeai",
#     type=SupabaseConnection,
#     ttl=None,
#     url=os.getenv("SUPABASE_URL"), # not needed if provided as a streamlit secret
#     key=os.getenv("SUPABASE_KEY"), # not needed if provided as a streamlit secret
# )

def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

if "current_step" not in st.session_state:
    st.session_state['current_step'] = 0
if "resume" not in st.session_state:
    st.session_state['resume'] = None
if "jd" not in st.session_state:
    st.session_state['jd'] = None
steps = ["Upload Resume", "Upload Job Description", "Suggestion Preference", "Get Feedback"]

def check_auth():
    if not cookie_manager.get("user"):
        cols = st.columns(2)
        with cols[0]:
            st.title("Welcome to Hippo Resume!")
            st.subheader("Please login to continue")
        with cols[1]:
            st.markdown('<div style="height: 300px;"></div>', unsafe_allow_html=True)
            cols = st.columns(3)
            with cols[1]:
                user_info = ac.login_button(os.getenv("AUTH0_CLIENT_ID"), os.getenv("AUTH0_DOMAIN"))
                if user_info:
                    cookie_manager.set("user", user_info)
        #st.write(user_info)
    else:
        try:
            is_auth = ac.isAuth(cookie_manager.get("user"), os.getenv("AUTH0_DOMAIN"))
            if is_auth:
                user_info = cookie_manager.get("user")
        except Exception as e:
            st.write(e)
            user_info = None
    if user_info:
        pass
    return user_info

def logout():
    cookie_manager.delete("user")
    st.rerun()

def increment_step(step):
    st.session_state['current_step'] += step
    if st.session_state['current_step'] > len(steps) - 1:
        st.session_state['current_step'] = 0

def control_buttons():
    cols = st.columns(2)
    with cols[0]:
        st.button("Previous", on_click=increment_step, args=(-1,))
    with cols[1]:
        st_tweaker.button("Next", id="next-btn", cls="next-btn", css="#next-btn button {float: right;}", on_click=increment_step, args=(1,), )

def display_pdf(pdf_file, ele):
    bytes_data = pdf_file.getvalue()
    base64_pdf = base64.b64encode(bytes_data).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="850" type="application/pdf"></iframe>'
    ele.markdown(pdf_display, unsafe_allow_html=True)

def upload_resume():
    
    cols = st.columns(2)
    cols[0].markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
    cols[0].markdown("""### Thanks for joining Hippo Resume! Our promise to you is that we'll get you closer toyour career goals, faster.
### Let's get started by uploading your resume.""")
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
                st.session_state['resume_text'] = text
                #st.write(text)
        os.remove(tmp.name)  # remove temp file
        st.session_state['resume'] = uploaded_file
        display_pdf(uploaded_file, cols[1])
    with cols[0]:
        control_buttons()

def upload_jd():
    st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
    cols = st.columns([10, 2])
    cols[0].markdown("""### Do you have any targeted role or company?
### We can help you to tailor your resume to the job description.""")
    cols = st.columns(2)
    job_title = cols[0].text_input("Job Title")
    company = cols[0].text_input("Company Name")
    jd = cols[0].text_area("Job Description")
    #display_pdf(st.session_state['resume'], cols[1])
    if jd:
        st.session_state['jd'] = jd
    if job_title:
        st.session_state['job_title'] = job_title
    if company:
        st.session_state['company'] = company
    control_buttons()

def suggestion_preferences():
    st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
    cols = st.columns(2)
    cols[0].markdown("""### What do you care most about the resume?""")
    control_buttons()

def ask_gpt():
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    qa_prompt = """You will be provided with a job description and a resume.
                    Please help the condidate to refine the resume by asking them five questions that can help them to tailor their experience to the job description.
                    Please output your response in the following format:
                    - Please ask the candidate a specific question that can trigger the candidate to think of whether having these kinds of experience that can tailored to the job description. Please be more focused on guiding the candidate to think of the experience that he/she may not think would align with the job description.
                    - The reason why you ask this question to the candidate
                    - Please list down the exact content from the job description that you refer to for asking the candidate this question.
                    
                    Separate each question with a new line and a title.
                    """
    
    qualitative_prompt = """You will be provided with a job description and a resume.

1. Give me a 100 words summary of job description on what kind of people they are looking for.
2. Give me 5 key words of job description
3. Give me detailed feedbacks based on my resume and the fitness of this job
more than three reasons of why I am a good fit
4. Give me detailed feedbacks based on my resume and the fitness of this job
more than three reasons of why I am not a good fit.
5. One summary: Am I a good fit? You can give me answer from perfect fit, good fit, not fit.
"""

    messages = [
            {
                "role": "system",
                "content": (
                    qualitative_prompt
                ),
            },
            {
                "role": "user",
                "content": f'''
                job_description: """{st.session_state['jd']}"""

                resume: """{st.session_state['resume_text']}"""
                ''',
            }
        ]
    
    #print(messages)

    with st.spinner("Generating feedback..."):
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="gpt-3.5-turbo-0125",
        )

        cols = st.columns(2)

        with cols[0]:
            st.write(chat_completion.choices[0].message.content)

        with cols[1]:
            tabs = st.tabs(["Resume", "Job Description"])
            display_pdf(st.session_state['resume'], tabs[0])
            with tabs[1]:
                st.write(st.session_state['jd'])

        control_buttons()

st.sidebar.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
st.sidebar.markdown("""### Hippo Resume""")
st.sidebar.markdown("""#### Menu""")

if check_auth():
    st.sidebar.button("Logout", on_click=logout)
    if st.session_state['current_step'] == 0:
        upload_resume()
    elif st.session_state['current_step'] == 1:
        upload_jd()
    elif st.session_state['current_step'] == 2:
        suggestion_preferences()
    elif st.session_state['current_step'] == 3:
        ask_gpt()