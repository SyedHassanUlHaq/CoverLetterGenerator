import os
import json
import re
from dotenv import load_dotenv
from mistralai import Mistral
from proposal_prompt import build_mistral_payload

load_dotenv()

# Load Mistral API Key
mistral_api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=mistral_api_key)

MODEL_NAME = "mistral-large-latest"

def _try_parse_json(text: str):
    """Try parsing model output as JSON, with several fallbacks.

    - Try full json.loads
    - Search for any JSON-like {...} substrings and attempt to parse them
      (useful when model wraps JSON in explanations/code fences).
    - Try a loose replacement of single quotes -> double quotes as a last resort.
    - Return the first parsed object that contains expected keys (e.g., 'cover_letter')
    """
    if not text or not isinstance(text, str):
        return None

    # 1) direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) try to find JSON-like objects in the text
    matches = re.finditer(r"\{[\s\S]*?\}", text)
    for m in matches:
        candidate = m.group(0)
        try:
            obj = json.loads(candidate)
            # return the first object we can parse
            return obj
        except Exception:
            continue

    # 3) try a naive single-quote -> double-quote swap (may help in some outputs)
    try:
        fixed = text.replace("\'", '"')
        return json.loads(fixed)
    except Exception:
        pass

    return None


def _remove_hyphens(text):
    """Remove all em-dashes and hyphens used as dashes from text.
    
    Removes em-dashes (—) but preserves hyphens in hyphenated words.
    """
    if not text or not isinstance(text, str):
        return text
    # Remove em-dashes (—)
    text = text.replace('—', '')
    # Remove hyphens that appear as sentence-level dashes (surrounded by spaces)
    # This regex finds " - " or " - " patterns and replaces with just a space
    text = re.sub(r'\s+–\s+|\s+—\s+|\s+-\s+(?=[A-Z])', ' ', text)
    return text


def generate_proposal(job_title, job_description, projects=None, example_cover_letters=None, min_words=150, max_words=220, temperature=0.2, max_output_tokens=512):
    """Generate a proposal using the prompt builder and Mistral.

    Returns a dict with keys: 'cover_letter', 'used_projects', 'clarifying_question'.
    """
    payload = build_mistral_payload(
        job_title=job_title,
        job_description=job_description,
        projects=projects or [],
        example_cover_letters=example_cover_letters,
        min_words=min_words,
        max_words=max_words,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )

    response = client.chat.complete(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": payload["input"]}],
        temperature=payload.get("temperature", 0.2),
        max_tokens=payload.get("max_output_tokens", 512),
    )

    text = response.choices[0].message.content.strip()
    parsed = _try_parse_json(text)
    if parsed and isinstance(parsed, dict) and "cover_letter" in parsed:
        # cover_letter itself may be a nested JSON string; try to extract nested JSON
        cl = parsed.get("cover_letter")
        if isinstance(cl, str):
            nested = _try_parse_json(cl)
            if nested and isinstance(nested, dict) and "cover_letter" in nested:
                # prefer the inner cover_letter text and merge other fields if present
                parsed["cover_letter"] = _remove_hyphens(nested.get("cover_letter"))
                if nested.get("used_projects"):
                    parsed.setdefault("used_projects", []).extend(nested.get("used_projects"))
                if nested.get("clarifying_question") and not parsed.get("clarifying_question"):
                    parsed["clarifying_question"] = nested.get("clarifying_question")
            else:
                parsed["cover_letter"] = _remove_hyphens(cl)
        else:
            parsed["cover_letter"] = _remove_hyphens(cl)
        return parsed

    # If the model returned a JSON-like string embedded in text, attempt to extract it
    # and pull out the cover_letter field using a regex as a last resort.
    # This handles cases where parsing failed but the response contains a 'cover_letter' key.
    m = re.search(r'"cover_letter"\s*:\s*"([\s\S]*?)"\s*(,|\})', text)
    if m:
        val = m.group(1)
        # unescape common sequences
        val = val.replace('\\n', '\n').replace('\\"', '"')
        val = _remove_hyphens(val)
        return {"cover_letter": val, "used_projects": [], "clarifying_question": None}

    # Final fallback: return raw text as cover_letter
    text = _remove_hyphens(text)
    return {"cover_letter": text, "used_projects": [], "clarifying_question": None}
