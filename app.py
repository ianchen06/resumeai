import os

import streamlit as st
from st_supabase_connection import SupabaseConnection
from dotenv import load_dotenv

load_dotenv()

st.title('Hello World')
st_supabase_client = st.connection(
    name="YOUR_CONNECTION_NAME",
    type=SupabaseConnection,
    ttl=None,
    url=os.getenv("SUPABASE_URL"), # not needed if provided as a streamlit secret
    key=os.getenv("SUPABASE_KEY"), # not needed if provided as a streamlit secret
)

res = st_supabase_client.auth.get_session()
st.write(res)

email = st.text_input('Enter your email')
password = st.text_input('Enter your password', type='password')
signup = st.button('signup')
login = st.button('login')
signout = st.button('signout')

if signout:
    res = st_supabase_client.auth.sign_out()
    st.write(res)

if email and password:
    if signup:
        res = st_supabase_client.auth.sign_up(
            dict(
                email=email, 
                password=password, 
                options=dict(data=dict(fname='Siddhant',attribution='I made it :)'))))
        st.write(res)
    elif login:
        res = st_supabase_client.auth.sign_in_with_password(dict(email=email, password=password))
        st.write(res)