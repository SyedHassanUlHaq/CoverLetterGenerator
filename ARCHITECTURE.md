# CoverLetterGenerator - Complete Architecture Documentation

## System Overview
CoverLetterGenerator is an AI-powered proposal/cover letter generation system that leverages the Mistral AI API to create personalized cover letters for job applications. It uses example-based learning through TF-IDF ranking to find contextually relevant proposals.

---

## Architecture Layers

### 1. **UI Layer** - Streamlit Frontend (`app.py`)
**Purpose**: User-facing web interface for proposal generation

**Responsibilities**:
- Display input fields for job title and description
- Provide configuration controls (min/max words, temperature slider)
- Handle user button clicks to trigger generation
- Display results (cover letter, used projects, clarifying questions)
- Provide download functionality for generated proposals

**Key Interactions**:
```
User Input → Streamlit UI → generate_proposal() → Streamlit Display
```

**UI Components**:
- Title: "📄 Hassan Proposal Generator (Mistral)"
- Inputs: Job Title, Job Description
- Parameters: Min words, Max words, Temperature
- Output: Generated proposal with download button

---

### 2. **Core Generation Engine**

#### A. **Proposal Generator** (`main.py`)
**Purpose**: Orchestrates the entire proposal generation pipeline

**Key Functions**:

1. **`generate_proposal()`** - Main entry point
   - Inputs: job_title, job_description, projects, example_cover_letters, min_words, max_words, temperature
   - Process:
     1. Builds prompt via `build_mistral_payload()`
     2. Calls Mistral AI API
     3. Parses JSON response with multiple fallbacks
     4. Returns structured dict: `{cover_letter, used_projects, clarifying_question}`

2. **`_try_parse_json()`** - Robust JSON parsing with 3 fallback strategies
   - Strategy 1: Direct `json.loads()` parsing
   - Strategy 2: Extract JSON-like `{...}` patterns using regex
   - Strategy 3: Replace single quotes with double quotes and retry
   - Fallback: Extract cover_letter from regex pattern
   - Ultimate fallback: Return raw text as cover_letter

**Data Flow**:
```
Job Title + Description
    ↓
build_mistral_payload()
    ↓
[Format with projects & examples & system prompt]
    ↓
Mistral API Call
    ↓
_try_parse_json() [with 3 strategies]
    ↓
Structured Result Dict
    ↓
Streamlit UI
```

**API Integration**:
- Uses `Mistral` client from `mistralai` SDK
- Model: `mistral-large-latest`
- Auth: `MISTRAL_API_KEY` from `.env`

---

#### B. **Prompt Builder** (`proposal_prompt.py`)
**Purpose**: Constructs optimized prompts for Mistral with system context

**Key Components**:

1. **`SYSTEM_PROMPT`** - System message containing:
   - Role definition (Hassan Ul Haq's proposal writer)
   - Style rules (confident, conversational, 150-220 words)
   - Structure template (greeting, opening, approach, closing)
   - 3 detailed example proposals (AI/Automation, Proposal Automation, AI Agent & Automation)

2. **`build_mistral_payload()`** - Constructs the complete prompt payload
   - Inputs: job_title, job_description, projects, example_cover_letters, min_words, max_words, temperature, max_output_tokens
   - Returns: Dict with:
     - `input`: Complete prompt text
     - `temperature`: Model creativity parameter
     - `max_output_tokens`: Response length limit

3. **`format_projects_list()`** - Formats portfolio projects
   - Structures: name, short_summary, role, techs, key_metric
   - Output: Numbered, readable project descriptions for prompt

**Prompt Structure**:
```
SYSTEM_PROMPT (role, style, examples)
    ↓
Projects List (formatted)
    ↓
Example Cover Letters (ranked)
    ↓
Job Title + Description
    ↓
GENERATION_PROMPT_SUFFIX (task instructions, output format)
```

**Output Format Specification**:
```json
{
  "cover_letter": "string (150-220 words)",
  "used_projects": ["project1", "project2"],
  "clarifying_question": "string or null"
}
```

---

#### C. **Example Ranker** (`ranker.py`)
**Purpose**: Intelligently rank stored cover letter examples by relevance

**Key Functions**:

1. **`rank_examples_by_tfidf(query, examples, top_k=3)`** - Primary ranking
   - Algorithm: TF-IDF (Term Frequency-Inverse Document Frequency)
   - Process:
     1. Vectorize corpus: [job_title, job_description, tags, cover_letter]
     2. Compute TF-IDF vectors with scikit-learn
     3. Calculate cosine similarity between query and corpus
     4. Return top-k ranked examples
   - Fallback: If scikit-learn unavailable, use keyword matching

2. **`_keyword_score(query, examples)`** - Lightweight fallback ranking
   - Algorithm: Keyword overlap scoring
   - Scoring: Tags (1.5 points), Token overlap (0.1 points each)
   - Returns: Sorted indices and scores

**Ranking Data**:
- Input: Query = "job_title + job_description"
- Corpus: Cover letters from `data/cover_letters.json`
- Output: Top-K ranked examples with similarity scores

---

### 3. **Data Layer**

#### A. **Project Portfolio** (`data/projects.json`)
**Structure**:
```json
{
  "projects": [
    {
      "name": "Project Name",
      "short_summary": "Brief description",
      "role": "Developer/Architect",
      "techs": "Python, FastAPI, PostgreSQL",
      "key_metric": "Improved performance by X%"
    }
  ]
}
```

**Usage**: Included in prompt to provide context about Hassan's past work

#### B. **Example Cover Letters** (`data/cover_letters.json`)
**Structure**:
```json
{
  "examples": [
    {
      "job_title": "AI Developer",
      "job_description": "...",
      "tags": ["AI", "ML", "LLM"],
      "cover_letter": "..."
    }
  ]
}
```

**Usage**: 
- Ranked by `ranker.py` for relevance
- Top-3 examples included in prompt for few-shot learning

#### C. **Environment Configuration** (`.env`)
**Content**:
```
MISTRAL_API_KEY=<api_key_from_console.mistral.ai>
```

**Usage**: Loaded by `python-dotenv` in `main.py` for API authentication

---

### 4. **External Services Integration**

#### **Mistral AI API**
**Service**: https://console.mistral.ai

**Integration Points**:
- **Client**: `Mistral(api_key=mistral_api_key)` from `mistralai` SDK
- **Model**: `mistral-large-latest`
- **Parameters**:
  - `messages`: List with user message containing prompt
  - `temperature`: 0.0-1.0 (0=deterministic, 1=creative)
  - `max_tokens`: Response length limit (default 512)

**Request/Response Flow**:
```
Request:
{
  "model": "mistral-large-latest",
  "messages": [{"role": "user", "content": "<full_prompt>"}],
  "temperature": 0.2,
  "max_tokens": 512
}

Response:
{
  "choices": [
    {
      "message": {
        "content": "{\"cover_letter\": \"...\", \"used_projects\": [...], \"clarifying_question\": null}"
      }
    }
  ]
}
```

---

## Data Flow Diagram

### Generation Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    User Input                               │
│  • Job Title                                                │
│  • Job Description                                          │
│  • Generation Parameters (min/max words, temperature)       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            app.py - Streamlit UI                            │
│  • Collects user inputs                                     │
│  • Validates fields                                         │
│  • Calls generate_proposal()                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│       main.py - generate_proposal()                         │
│  • Orchestrates generation pipeline                         │
│  • Calls prompt builder                                     │
│  • Initializes Mistral client                               │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
    ┌─────────────┐         ┌──────────────┐
    │ Prompt      │         │   Example    │
    │ Builder     │         │   Ranker     │
    │             │         │              │
    │ • Format    │         │ • Query job  │
    │   projects  │         │   info       │
    │ • Format    │         │ • TF-IDF     │
    │   examples  │         │   ranking    │
    │ • Add sys   │         │ • Return     │
    │   prompt    │         │   top-K      │
    └──────┬──────┘         └──────┬───────┘
           │                       │
           └───────────┬───────────┘
                       │
                       ▼
       ┌──────────────────────────────────┐
       │  Build Mistral Payload           │
       │  • System prompt                 │
       │  • Projects (formatted)          │
       │  • Top-K examples (ranked)       │
       │  • Job title + description       │
       │  • Generation constraints        │
       └──────────────┬───────────────────┘
                      │
                      ▼
       ┌──────────────────────────────────┐
       │  Load .env Configuration         │
       │  • MISTRAL_API_KEY               │
       └──────────────┬───────────────────┘
                      │
                      ▼
       ┌──────────────────────────────────┐
       │  Mistral AI API Call             │
       │  • Authenticate with API key     │
       │  • Send complete prompt          │
       │  • Set temperature & max_tokens  │
       └──────────────┬───────────────────┘
                      │
          ┌───────────┴───────────┐
          │   Mistral Response    │
          │   • JSON format       │
          │   • cover_letter      │
          │   • used_projects     │
          │   • clarifying_q      │
          └───────────┬───────────┘
                      │
                      ▼
       ┌──────────────────────────────────┐
       │  Parse Response                  │
       │  • _try_parse_json()             │
       │  • Strategy 1: Direct parse      │
       │  • Strategy 2: Regex extraction  │
       │  • Strategy 3: Quote replacement │
       │  • Strategy 4: Regex fallback    │
       └──────────────┬───────────────────┘
                      │
                      ▼
       ┌──────────────────────────────────┐
       │  Return Structured Result        │
       │  {                               │
       │    cover_letter: str,            │
       │    used_projects: list,          │
       │    clarifying_question: str|null │
       │  }                               │
       └──────────────┬───────────────────┘
                      │
                      ▼
       ┌──────────────────────────────────┐
       │  Display in Streamlit            │
       │  • Show cover letter             │
       │  • List used projects            │
       │  • Show clarifying question      │
       │  • Provide download button       │
       └──────────────────────────────────┘
```

---

## Dependencies & Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| `streamlit` | 1.51.0 | Web UI framework |
| `mistralai` | 1.9.11 | Mistral API SDK |
| `python-dotenv` | 1.2.1 | Environment variable loading |
| `scikit-learn` | 1.8.0 | TF-IDF vectorization, cosine similarity |
| `pandas` | 2.3.3 | Data manipulation (if needed) |
| `numpy` | 2.3.4 | Numerical computing |
| `Jinja2` | 3.1.6 | Template rendering (optional) |
| `requests` | 2.32.5 | HTTP requests (optional) |

---

## Key Design Decisions

### 1. **Multiple JSON Parsing Strategies**
- **Why**: LLMs sometimes return JSON wrapped in text or with formatting issues
- **Benefit**: Robust error handling, maximizes success rate

### 2. **TF-IDF Ranking with Keyword Fallback**
- **Why**: TF-IDF finds semantically similar examples; keyword fallback works without sklearn
- **Benefit**: Better example selection, graceful degradation

### 3. **Few-Shot Learning via Examples**
- **Why**: Mistral model learns from provided examples in-context
- **Benefit**: Improved output quality without retraining

### 4. **Prompt Templating**
- **Why**: System prompt + examples + task instructions ensure consistent output format
- **Benefit**: Reliable JSON parsing, predictable behavior

### 5. **Environment Variables for Secrets**
- **Why**: Never commit API keys to repository
- **Benefit**: Security, easy credential rotation

---

## Extension Points

### 1. **Add Database Backend**
```python
# Replace JSON files with database
# Modify: data loading in prompt_builder.py, ranker.py
```

### 2. **Support Multiple LLM Providers**
```python
# Add abstract LLM interface
# Support: OpenAI, Anthropic, Hugging Face
```

### 3. **Add Example Evaluation**
```python
# Track which examples produced best results
# Use feedback to improve ranking
```

### 4. **Implement Caching**
```python
# Cache generated proposals by job description hash
# Reduce API calls and costs
```

### 5. **Add User Authentication**
```python
# Track user history, saved proposals
# Implement rate limiting
```

---

## File Structure

```
CoverLetterGenerator/
├── app.py                      # Streamlit UI
├── main.py                     # Core generation logic
├── proposal_prompt.py          # Prompt building
├── ranker.py                   # Example ranking
├── requirements.txt            # Python dependencies
├── .env                        # API keys (git-ignored)
├── .env.example                # Template for .env
├── .gitignore                  # Exclude .env, venv, etc.
├── README.md                   # Documentation
├── data/
│   ├── projects.json          # Portfolio data
│   └── cover_letters.json      # Example proposals
└── scripts/
    └── generate_demo.py       # Deprecated demo script
```

---

## Deployment Considerations

### Local Development
- Run: `streamlit run app.py`
- Port: `http://localhost:8501`

### Cloud Deployment
- **Platforms**: Streamlit Cloud, Heroku, AWS, GCP
- **Requirements**: Python 3.12+, `requirements.txt`
- **Secrets**: Set `MISTRAL_API_KEY` as environment variable

### Performance Optimization
- Cache Mistral client initialization
- Cache ranked examples for similar queries
- Implement request batching for multiple generations
- Add response caching layer

---

## Conclusion

The CoverLetterGenerator follows a modular, layered architecture:
- **UI Layer**: Streamlit handles user interaction
- **Core Engine**: Proposal generator orchestrates the pipeline
- **Support Modules**: Prompt builder and ranker provide specialized functions
- **Data Layer**: JSON files store projects and examples
- **External Service**: Mistral AI provides language model capabilities

This design enables easy maintenance, testing, and extension while maintaining clear separation of concerns.
