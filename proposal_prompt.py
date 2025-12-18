# ---------------------------------------------------------------------------
# Mistral prompt helpers — format projects and example letters into a safe
# prompt that the model can use without external retrieval (no RAG).
# ---------------------------------------------------------------------------

GENERATION_PROMPT_SUFFIX = """
Task: You are a professional Upwork bidder writing short, high-conversion cover letters.

Constraints:
- Use only facts from the provided Projects list and Example cover letters; DO NOT fabricate details.
- Choose up to 3 projects that best match the job and reference them by name.
- If necessary facts are missing, return a clarifying question in the 'clarifying_question' field instead of making things up.

Output: JSON object with keys:
- cover_letter: string (the generated letter)
- used_projects: list of project names
- clarifying_question: null or string

Other constraints: 150-220 words (adjustable), 3 short paragraphs + closing line.
"""


def format_projects_list(projects):
    """Format a list of project dicts into a numbered text block for inclusion
    in a prompt.

    Expected project dict keys: name, short_summary, techs (optional), role
    (optional), key_metric (optional).
    """
    lines = []
    for i, p in enumerate(projects, start=1):
        parts = []
        name = p.get("name") or f"Project {i}"
        parts.append(f"{name}: {p.get('short_summary','')}")
        if p.get("role"):
            parts.append(f"Role: {p.get('role')}")
        if p.get("techs"):
            parts.append(f"Techs: {p.get('techs')}")
        if p.get("key_metric"):
            parts.append(f"Result: {p.get('key_metric')}")
        lines.append(f"{i}) " + " | ".join([s for s in parts if s]))
    return "\n".join(lines)


def build_mistral_prompt(job_title, job_description, projects, example_cover_letters=None, tone='confident', min_words=150, max_words=220):
    """Construct the full prompt to send to Mistral.

    - projects: list of dicts (see format_projects_list)
    - example_cover_letters: optional list of strings to use as style examples
    """
    project_block = format_projects_list(projects)
    examples_block = ""
    if example_cover_letters:
        examples_block = "\n\n### Style Examples\n"
        for i, ex in enumerate(example_cover_letters, start=1):
            examples_block += f"Example {i}:\n{ex}\n\n"

    prompt = (
        SYSTEM_PROMPT
        + "\n\n"
        + GENERATION_PROMPT_SUFFIX
        + f"\n\nJob Title: {job_title}\nJob Description:\n{job_description}\n\nProvided Projects:\n{project_block}\n{examples_block}\n\n"
        + f"Instructions: Select up to 3 projects and write a cover letter of {min_words}-{max_words} words. Use only provided facts. Output JSON with keys 'cover_letter','used_projects','clarifying_question'."
    )
    return prompt


def build_mistral_payload(job_title, job_description, projects, example_cover_letters=None, **kwargs):
    """Return a payload dict for a Mistral API call.

    Only recognized prompt parameters are forwarded to `build_mistral_prompt`:
    - tone
    - min_words
    - max_words

    Other kwargs like `temperature` and `max_output_tokens` are used to
    configure the API call and are not passed into the prompt builder.
    """
    tone = kwargs.get("tone", "confident")
    min_words = kwargs.get("min_words", 150)
    max_words = kwargs.get("max_words", 220)

    prompt = build_mistral_prompt(job_title, job_description, projects, example_cover_letters, tone=tone, min_words=min_words, max_words=max_words)
    payload = {
        "input": prompt,
        "temperature": kwargs.get("temperature", 0.2),
        "max_output_tokens": kwargs.get("max_output_tokens", 512),
    }
    return payload


__all__ = [
    "SYSTEM_PROMPT",
    "GENERATION_PROMPT_SUFFIX",
    "format_projects_list",
    "build_mistral_prompt",
    "build_mistral_payload",
]
