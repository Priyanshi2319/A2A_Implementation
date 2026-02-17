
import streamlit as st
from host_client import send_to_host_agent

st.set_page_config(page_title="A2A Multi Agent", layout="wide")

st.title("🤖 Host Agent UI")

# chat memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# show history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# user input
if prompt := st.chat_input("Ask Host Agent..."):

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Host Agent routing..."):

            response = send_to_host_agent(prompt)

            st.markdown(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })
