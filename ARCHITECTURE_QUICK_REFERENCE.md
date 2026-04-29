# CoverLetterGenerator - Quick Reference Guide

## Architecture at a Glance

```
┌────────────────────────────────────────────────────────────────┐
│                     USER (Web Browser)                         │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│         STREAMLIT UI (app.py)                                 │
│  • Input: Job Title, Description                              │
│  • Controls: Min/Max Words, Temperature                        │
│  • Output: Generated Proposal, Download Button                │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│      PROPOSAL GENERATOR (main.py)                              │
│  • Orchestrates the generation pipeline                        │
│  • Calls prompt builder & example ranker                       │
│  • Handles Mistral API communication                           │
│  • Parses JSON responses (4 fallback strategies)               │
└────────────────────────┬─────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
    ┌────────┐      ┌──────────┐    ┌──────────┐
    │ Prompt │      │ Example  │    │   .env   │
    │Builder │      │ Ranker   │    │ Config   │
    └────────┘      └──────────┘    └──────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                         ▼
    ┌──────────────────────────────────┐
    │    Mistral API Integration        │
    │  • Authenticate with API key      │
    │  • Send complete prompt           │
    │  • Receive JSON response          │
    │  • Parse & validate response      │
    └──────────────────────────────────┘
```

---

## Module Responsibilities

### 1. **app.py** - Streamlit Interface
**Input**: User interactions (text inputs, buttons, sliders)
**Output**: Rendered UI with results
**Key Functions**:
- `st.text_input()` - Job title input
- `st.text_area()` - Job description input
- `st.button()` - Generate button
- `st.spinner()` - Loading indicator
- `st.download_button()` - Download proposal

---

### 2. **main.py** - Proposal Generator Engine
**Input**: Job details, projects, examples, generation parameters
**Output**: Dictionary with cover_letter, used_projects, clarifying_question

**Key Functions**:
```python
generate_proposal(
    job_title: str,
    job_description: str,
    projects: Optional[List[dict]],
    example_cover_letters: Optional[List[dict]],
    min_words: int = 150,
    max_words: int = 220,
    temperature: float = 0.2,
    max_output_tokens: int = 512
) -> Dict[str, Any]

_try_parse_json(text: str) -> Optional[Dict]
```

---

### 3. **proposal_prompt.py** - Prompt Construction
**Input**: Job info, projects, examples, parameters
**Output**: Formatted prompt payload for Mistral

**Key Functions**:
```python
build_mistral_payload(
    job_title: str,
    job_description: str,
    projects: List[dict],
    example_cover_letters: Optional[List[dict]],
    min_words: int,
    max_words: int,
    temperature: float,
    max_output_tokens: int
) -> Dict[str, Any]

format_projects_list(projects: List[dict]) -> str
```

---

### 4. **ranker.py** - Example Ranking
**Input**: Query (job title + description), examples list
**Output**: Top-K ranked examples with similarity scores

**Key Functions**:
```python
rank_examples_by_tfidf(
    query: str,
    examples: List[dict],
    top_k: int = 3
) -> List[Tuple[int, float]]

_keyword_score(
    query: str,
    examples: List[dict]
) -> List[Tuple[int, float]]
```

---

## Data Flow Summary

```
User Input (Job Title + Description)
    ↓
[Parallel: Build Prompt + Rank Examples]
    ├─ Prompt Builder:
    │  • Format projects
    │  • Add system prompt
    │  • Add job context
    │
    └─ Example Ranker:
       • Compute TF-IDF vectors
       • Calculate similarity scores
       • Return top-3 examples
    ↓
[Combine payload + ranked examples]
    ↓
[Load API key from .env]
    ↓
[Call Mistral API]
    ↓
[Parse JSON response (4 strategies)]
    ├─ Strategy 1: json.loads()
    ├─ Strategy 2: Regex extraction
    ├─ Strategy 3: Quote replacement
    └─ Strategy 4: Field regex fallback
    ↓
[Return structured result]
    ↓
[Display in Streamlit UI]
```

---

## Integration Points

### Mistral AI API
- **Endpoint**: `mistral-large-latest` model
- **Authentication**: API key in `.env`
- **Request Format**: JSON with messages array
- **Response Format**: JSON with model-generated cover letter

### python-dotenv
- **Purpose**: Load `MISTRAL_API_KEY` from `.env` file
- **Method**: `load_dotenv()` called at module import

### scikit-learn
- **Purpose**: TF-IDF vectorization for example ranking
- **Fallback**: Keyword-based scoring if not available

### Streamlit
- **Purpose**: Web UI framework
- **Communication**: Callbacks from UI → functions → results → display

---

## Configuration

### `.env` File
```
MISTRAL_API_KEY=your_api_key_here
```

### Generation Parameters (adjustable via UI)
- **Min Words**: 50-1000 (default 150)
- **Max Words**: 50-2000 (default 220)
- **Temperature**: 0.0-1.0 (default 0.2)
  - 0.0 = deterministic, focused
  - 1.0 = creative, varied

---

## Error Handling & Resilience

### JSON Parsing Fallbacks
1. **Direct Parse**: Try standard `json.loads()`
2. **Regex Extraction**: Find `{...}` patterns in text
3. **Quote Replacement**: Fix single/double quote mismatches
4. **Field Extraction**: Extract via regex if full JSON fails

### API Key Protection
- Never commit `.env` to git
- Use `.env.example` as template
- Load via `python-dotenv` at runtime

---

## Performance Optimizations

### Implemented
- TF-IDF vectorization for efficient ranking
- Parallel prompt building & example ranking
- JSON parsing with early exit strategies

### Recommended Future
- Cache Mistral client initialization
- Cache ranked examples for same queries
- Implement response caching layer
- Add request batching

---

## Testing the System

### Manual Test
```bash
cd /home/wara/Downloads/CoverLetterGenerator
source venv/bin/activate
streamlit run app.py
```

### API Test
```bash
python3 -c "
from main import generate_proposal
result = generate_proposal(
    'AI Developer',
    'Looking for someone to build AI agents...',
    min_words=100,
    max_words=150
)
print(result['cover_letter'])
"
```

---

## Deployment Checklist

- [ ] Set `MISTRAL_API_KEY` environment variable
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Verify Mistral API access
- [ ] Test proposal generation locally
- [ ] Configure output directory for downloads
- [ ] Set up error logging
- [ ] Test with various job descriptions
- [ ] Monitor API usage and costs

---

## Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `app.py` | Streamlit UI | ~60 |
| `main.py` | Proposal generation | ~100 |
| `proposal_prompt.py` | Prompt building | ~200+ |
| `ranker.py` | Example ranking | ~50 |
| `requirements.txt` | Dependencies | 60+ packages |
| `data/projects.json` | Portfolio data | Variable |
| `data/cover_letters.json` | Example proposals | Variable |
| `.env` | API keys | 1 line |

---

## Key Metrics

- **Average Generation Time**: 2-5 seconds (depends on API latency)
- **Typical Output Length**: 150-220 words
- **Example Pool Size**: As many as in `cover_letters.json`
- **API Cost**: Per Mistral pricing tier
