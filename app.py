import os

import streamlit as st
from st_supabase_connection import SupabaseConnection
from dotenv import load_dotenv
from openai import OpenAI




load_dotenv()

st.title('📄 Resume AI')
st_supabase_client = st.connection(
    name="resumeai",
    type=SupabaseConnection,
    ttl=None,
    url=os.getenv("SUPABASE_URL"), # not needed if provided as a streamlit secret
    key=os.getenv("SUPABASE_KEY"), # not needed if provided as a streamlit secret
)

res = st_supabase_client.auth.get_session()

if not res:
    st.markdown("""## Login or Signup""")
    email = st.text_input('Enter your email')
    password = st.text_input('Enter your password', type='password')
    signup = st.button('signup')
    login = st.button('login')
    signout = st.button('signout')

    if signout:
        res = st_supabase_client.auth.sign_out()

    if email and password:
        if signup:
            res = st_supabase_client.auth.sign_up(
                dict(
                    email=email, 
                    password=password, 
                    options=dict(data=dict(fname='Siddhant',attribution='I made it :)'))))
        elif login:
            res = st_supabase_client.auth.sign_in_with_password(dict(email=email, password=password))
else:
    st.markdown(f"""hello, {res.user.email}""")
    jd = st.text_area("Job Description")
    submitted = st.button("🪄 Magic")
    if submitted:
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Say this is a test",
                }
            ],
            model="gpt-3.5-turbo",
        )
