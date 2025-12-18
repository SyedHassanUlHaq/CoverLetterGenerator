"""TF-IDF-based example ranking utilities.

Provides a simple function to rank stored example cover letters against a
query (job title + description) using TF-IDF + cosine similarity. Falls back
to a lightweight keyword/tag scoring if scikit-learn is not available.
"""
from typing import List, Tuple


def _keyword_score(query: str, examples: List[dict]) -> List[Tuple[int, float]]:
    """Fallback ranking: score by tag and token overlap (very lightweight)."""
    q = query.lower()
    q_tokens = set([t for t in q.split() if len(t) > 2])
    scores = []
    for i, e in enumerate(examples):
        score = 0.0
        tags = e.get("tags") or []
        for t in tags:
            if t.lower() in q:
                score += 1.5
        # title and description overlap
        text = " ".join([e.get("job_title",""), e.get("job_description","")]).lower()
        text_tokens = set([t for t in text.split() if len(t) > 2])
        overlap = len(q_tokens & text_tokens)
        score += overlap * 0.1
        scores.append((i, float(score)))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def rank_examples_by_tfidf(query: str, examples: List[dict], top_k: int = 3) -> List[Tuple[int, float]]:
    """Return top_k example indices and similarity scores for the query.

    If scikit-learn is not installed, fall back to a simple keyword/tag score.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except Exception:
        return _keyword_score(query, examples)[:top_k]

    corpus = []
    for e in examples:
        parts = [e.get("job_title", ""), e.get("job_description", ""), " ".join(e.get("tags", [])), e.get("cover_letter", "")]
        corpus.append(" \n ".join([p for p in parts if p]))

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)
    X = vectorizer.fit_transform(corpus)
    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, X).flatten()
    ranked_idx = sims.argsort()[::-1][:top_k]
    return [(int(i), float(sims[int(i)])) for i in ranked_idx]


__all__ = ["rank_examples_by_tfidf"]
