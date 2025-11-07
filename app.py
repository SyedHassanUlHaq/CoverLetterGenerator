import streamlit as st
from main import generate_proposal

st.set_page_config(page_title="Hassan Proposal Generator", layout="centered")

st.title("📄 Hassan Proposal Generator (Mistral)")

job_title = st.text_input("Job Title")
job_description = st.text_area("Job Description", height=250)

if st.button("Generate Proposal"):
    if not job_title.strip() or not job_description.strip():
        st.warning("Please fill out both fields.")
    else:
        with st.spinner("Generating proposal..."):
            proposal = generate_proposal(job_title, job_description)
        st.subheader("✅ Generated Proposal:")
        st.write(proposal)

        st.download_button(
            label="📥 Download as .txt",
            data=proposal,
            file_name="proposal.txt",
            mime="text/plain"
        )
