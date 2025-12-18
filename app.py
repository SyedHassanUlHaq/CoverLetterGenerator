import streamlit as st
import json
from main import generate_proposal

st.set_page_config(page_title="Hassan Proposal Generator", layout="centered")

st.title("📄 Hassan Proposal Generator (Mistral)")

job_title = st.text_input("Job Title", key="job_title")
job_description = st.text_area("Job Description", height=250, key="job_description")


col1, col2, col3 = st.columns(3)
with col1:
    min_words = st.number_input("Min words", min_value=50, max_value=1000, value=150)
with col2:
    max_words = st.number_input("Max words", min_value=50, max_value=2000, value=220)
with col3:
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.2)

if st.button("Generate Proposal"):
    if not job_title.strip() or not job_description.strip():
        st.warning("Please fill out both fields.")
    else:
        # Use selected examples stored in session state
        example_letters = st.session_state.get('selected_examples', [])
        projects = None

        with st.spinner("Generating proposal..."):
            result = generate_proposal(
                job_title,
                job_description,
                projects=projects,
                example_cover_letters=example_letters,
                min_words=min_words,
                max_words=max_words,
                temperature=temperature,
            )

        st.subheader("✅ Generated Proposal:")

        # result is expected to be a dict (see main.generate_proposal)
        if isinstance(result, dict):
            cover = result.get("cover_letter")
            used = result.get("used_projects")
            clar = result.get("clarifying_question")
            if clar:
                st.warning("Model asked a clarifying question. Please answer it before sending the proposal:")
                st.info(clar)
            if used:
                st.markdown("**Projects used:** " + ", ".join(used))
            st.write(cover)
            st.download_button(label="📥 Download as .txt", data=cover or "", file_name="proposal.txt", mime="text/plain")
        else:
            st.write(result)
            st.download_button(label="📥 Download as .txt", data=str(result), file_name="proposal.txt", mime="text/plain")
