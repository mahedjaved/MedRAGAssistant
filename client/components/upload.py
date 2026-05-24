import streamlit as st
from utils.api import upload_pdfs_api


def render_upload():
    st.sidebar.subheader("📁 Upload Medical Documents (.pdf)")
    uploaded_files = st.sidebar.file_uploader(
        "Upload multiple PDF files", type="pdf", accept_multiple_files=True
    )
    if st.sidebar.button("Upload DB") and uploaded_files:
        response = upload_pdfs_api(uploaded_files)
        if response.status_code == 200:
            st.sidebar.success("Files uploaded successfully!")
        else:
            st.sidebar.error(f"Upload failed: {response.text}")