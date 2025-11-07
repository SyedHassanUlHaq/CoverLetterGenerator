import os
from dotenv import load_dotenv
from mistralai import Mistral
from proposal_prompt import SYSTEM_PROMPT

load_dotenv()

# Load Mistral API Key
mistral_api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=mistral_api_key)

MODEL_NAME = "mistral-large-latest"

def generate_proposal(job_title, job_description):
    """Generate Hassan-style proposal using Mistral API."""
    user_input = f"Job title: {job_title}\nJob description: {job_description}"

    response = client.chat.complete(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
        temperature=0.8,
        top_p=0.9,
        max_tokens=600,
    )

    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    print("=== Hassan Proposal Generator (Mistral) ===")
    job_title = input("Enter job title: ")
    print("Paste job description (end with ENTER + Ctrl+D / Ctrl+Z):")
    job_description = ""
    while True:
        try:
            line = input()
        except EOFError:
            break
        job_description += line + "\n"

    proposal = generate_proposal(job_title, job_description)
    print("\n--- Generated Proposal ---\n")
    print(proposal)
