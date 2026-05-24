import streamlit as st
from components.upload import render_upload
from components.chatUI import render_chat_ui
from components.history_download import render_history_download

st.set_page_config(page_title="Medical PDF Q&A Assistant", layout="wide")
st.title("MedAI Assistant \u2014 Medical PDF Q&A")

render_upload()
render_chat_ui()
render_history_download()
