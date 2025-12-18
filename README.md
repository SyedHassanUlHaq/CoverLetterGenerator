# CoverLetterGenerator

## Setup & Usage

- Copy `.env.example` to `.env` and add your Mistral API key:

```
MISTRAL_API_KEY=sk-...your-key...
```

- Run the Streamlit UI locally:

```
pip install -r requirements.txt
streamlit run app.py
```

Open the UI, paste the job title and description, optionally paste a Projects JSON and example cover letters, then click "Generate Proposal". The app will call Mistral and present the generated letter (and any clarifying questions the model asks).

Do not commit your real `.env` file to git. Use the `.env.example` as a template.
