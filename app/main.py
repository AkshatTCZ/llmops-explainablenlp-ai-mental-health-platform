from contextlib import asynccontextmanager

import os
import re
from pathlib import Path
from typing import Any

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from model.llm_client import generate_support_response, suggest_single_book
from model.predict import load_model, predict_emotion
from model.shap_explainer import (
    ensure_shap_explainer,
    generate_deterministic_explanation,
    get_top_words,
)

# Load environment variables from .env (if present) once on startup.
# Use an explicit path so it works regardless of the server's working directory.
_APP_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _APP_DIR.parent
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv(_APP_DIR / ".env")

# Google Books API key (server-side only; never sent to frontend).
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
print("Using Google Books API key:", bool(GOOGLE_BOOKS_API_KEY))


class ChatHistoryItem(BaseModel):
    role: str
    content: str


class TextInput(BaseModel):
    text: str = Field(..., min_length=1, description="Text to classify")
    advice_given: bool = False
    history: list[ChatHistoryItem] = Field(default_factory=list)


class PredictResponse(BaseModel):
    emotion: str
    confidence: float
    important_words: list[str]
    response: str


class ExplainResponse(BaseModel):
    explanation: str
    important_words: list[str]


class RecommendBookRequest(BaseModel):
    emotion: str = Field(..., min_length=1)
    important_words: list[str] = Field(default_factory=list)
    session_id: str = "default"
    seen_titles: list[str] = Field(default_factory=list)


class RecommendBookResponse(BaseModel):
    title: str
    author: str
    description: str
    image: str
    tags: list[str]
    rating: int
    reason: str


def _build_book_query(emotion: str, important_words: list[str]) -> tuple[str, list[str]]:
    safe_emotion = (emotion or "").strip().lower() or "mental health"
    keywords = [w.strip().lower() for w in (important_words or []) if isinstance(w, str) and w.strip()]
    top2 = keywords[:2]
    # Keep concise and meaningful.
    query = f"self help book for {' '.join(top2)} {safe_emotion}".strip()
    return query, top2


def _score_volume_info(info: dict[str, Any]) -> int:
    if not info.get("title"):
        return -10
    desc = info.get("description")
    has_description = isinstance(desc, str) and len(desc.strip()) > 40
    image_links = info.get("imageLinks") or {}
    thumb = image_links.get("thumbnail") or image_links.get("smallThumbnail")
    has_thumb = isinstance(thumb, str) and bool(thumb.strip())
    cats = info.get("categories")
    has_categories = isinstance(cats, list) and len(cats) > 0
    return (2 if has_description else 0) + (2 if has_thumb else 0) + (1 if has_categories else 0)


def _normalize_thumbnail(url: Any) -> str:
    if not isinstance(url, str) or not url.strip():
        return ""
    u = url.strip()
    return u.replace("http://", "https://", 1) if u.startswith("http://") else u


# Track recommended titles per chat session to reduce repeats.
_recommended_titles_by_session: dict[str, list[str]] = {}


def _normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (title or "").strip().lower())


def _is_seen_title(title: str, seen_titles: list[str]) -> bool:
    norm = _normalize_title(title)
    if not norm:
        return False
    return any(_normalize_title(t) == norm for t in seen_titles)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    ensure_shap_explainer()
    yield


app = FastAPI(
    title="Emotion Detection API",
    lifespan=lifespan,
)


@app.get("/")
def home():
    return {"message": "Emotion Detection API is running"}


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/predict", response_model=PredictResponse)
def predict_emotion_endpoint(body: TextInput) -> PredictResponse:
    label_id, label_name, probability = predict_emotion(body.text)
    important_words = get_top_words(body.text, top_k=3, label_id=label_id)
    user_response = generate_support_response(
        body.text,
        label_name,
        body.advice_given,
        body.history,
    )
    return PredictResponse(
        emotion=label_name,
        confidence=round(float(probability), 4),
        important_words=important_words,
        response=user_response,
    )


@app.post("/explain", response_model=ExplainResponse)
def explain_emotion_endpoint(body: TextInput) -> ExplainResponse:
    label_id, label_name, _probability = predict_emotion(body.text)
    important_words = get_top_words(body.text, top_k=3, label_id=label_id)
    explanation = generate_deterministic_explanation(label_name, important_words)
    return ExplainResponse(
        explanation=explanation,
        important_words=important_words,
    )


@app.post("/recommend-book", response_model=RecommendBookResponse)
def recommend_book(body: RecommendBookRequest) -> RecommendBookResponse:
    # Re-read env var as a fallback (e.g., differing cwd/reloader processes).
    api_key = GOOGLE_BOOKS_API_KEY or os.getenv("GOOGLE_BOOKS_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_BOOKS_API_KEY not set",
        )

    query, top2 = _build_book_query(body.emotion, body.important_words)
    session_id = (body.session_id or "default").strip() or "default"
    memory_seen_titles = _recommended_titles_by_session.get(session_id, [])
    payload_seen_titles = [t for t in body.seen_titles if isinstance(t, str) and t.strip()]
    seen_titles = []
    for t in memory_seen_titles + payload_seen_titles:
        if not _is_seen_title(t, seen_titles):
            seen_titles.append(t)

    # 1) Ask LLM for a semantically relevant REAL book title + short description.
    llm_title = ""
    llm_description = ""
    excluded_titles = list(seen_titles)
    for _ in range(3):
        llm_pick = suggest_single_book(body.emotion, body.important_words, excluded_titles)
        if not llm_pick:
            break
        candidate_title, candidate_desc = llm_pick
        if candidate_title and not _is_seen_title(candidate_title, seen_titles):
            llm_title = candidate_title
            llm_description = candidate_desc
            break
        if candidate_title:
            excluded_titles.append(candidate_title)

    # If LLM only returns already-seen titles, force query-based fallback.
    if llm_title and _is_seen_title(llm_title, seen_titles):
        llm_title = ""
        llm_description = ""

    # 2) Use Google Books for metadata lookup (prefer searching by title if LLM succeeded).
    url = "https://www.googleapis.com/books/v1/volumes"
    google_query = llm_title if llm_title else query
    try:
        resp = requests.get(
            url,
            params={"q": google_query, "maxResults": 5, "key": api_key} if api_key else {"q": google_query, "maxResults": 5},
            timeout=15,
        )
    except requests.RequestException as e:
        # Fallback: if LLM worked, return its title/description with safe defaults.
        if llm_title:
            result = RecommendBookResponse(
                title=llm_title,
                author="Unknown author",
                description=llm_description or "No description available",
                image="",
                tags=["Mental Health", "Self-Help"],
                rating=4,
                reason="Recommended based on your emotional context",
            )
            return result
        raise HTTPException(status_code=502, detail=f"Failed to reach Google Books API: {e}") from e

    if resp.status_code != 200:
        # Try to surface Google error message (quota, bad key, etc.)
        detail = f"Google Books API error: HTTP {resp.status_code}"
        try:
            err = resp.json()
            msg = err.get("error", {}).get("message")
            if isinstance(msg, str) and msg.strip():
                detail = f"{detail} - {msg.strip()}"
        except ValueError:
            pass
        # Fallback: if LLM worked, return its title/description with safe defaults.
        if llm_title:
            result = RecommendBookResponse(
                title=llm_title,
                author="Unknown author",
                description=llm_description or "No description available",
                image="",
                tags=["Mental Health", "Self-Help"],
                rating=4,
                reason="Recommended based on your emotional context",
            )
            return result
        raise HTTPException(status_code=502, detail=detail)

    data = resp.json()
    items = data.get("items") or []
    if not isinstance(items, list) or not items:
        # Fallback: if LLM worked, return its title/description with safe defaults.
        if llm_title:
            result = RecommendBookResponse(
                title=llm_title,
                author="Unknown author",
                description=llm_description or "No description available",
                image="",
                tags=["Mental Health", "Self-Help"],
                rating=4,
                reason="Recommended based on your emotional context",
            )
            return result
        raise HTTPException(status_code=404, detail="No book results found.")

    # Pick best valid result, preferring titles not already seen in this session.
    best_info: dict[str, Any] | None = None
    best_score = -999
    for item in items:
        info = item.get("volumeInfo") if isinstance(item, dict) else None
        if not isinstance(info, dict):
            continue
        score = _score_volume_info(info)
        candidate_title = str(info.get("title") or "")
        if candidate_title and not _is_seen_title(candidate_title, seen_titles):
            score += 3
        if score > best_score:
            best_score = score
            best_info = info

    if not best_info or not best_info.get("title"):
        raise HTTPException(status_code=404, detail="No valid book results found.")

    title = str(best_info.get("title"))
    authors = best_info.get("authors")
    author = ", ".join(authors) if isinstance(authors, list) and authors else "Unknown author"
    # Prefer LLM-generated concise description; ignore Google Books description when LLM succeeded.
    if llm_title:
        description_text = llm_description or "No description available"
    else:
        description = best_info.get("description")
        description_text = description.strip() if isinstance(description, str) and description.strip() else "No description available"

    image_links = best_info.get("imageLinks") if isinstance(best_info.get("imageLinks"), dict) else {}
    image = _normalize_thumbnail(image_links.get("thumbnail") or image_links.get("smallThumbnail"))

    categories = best_info.get("categories")
    tags = categories[:3] if isinstance(categories, list) and categories else ["Mental Health", "Self-Help"]

    avg = best_info.get("averageRating")
    try:
        rating_val = int(round(float(avg))) if avg is not None else 4
    except (TypeError, ValueError):
        rating_val = 4
    rating = max(1, min(5, rating_val))

    reason = "Recommended based on your emotional context" if llm_title else (
        f"Picked based on: {body.emotion.strip()}" + (f" + {', '.join(top2)}" if top2 else "")
    )

    result = RecommendBookResponse(
        title=llm_title or title,
        author=author,
        description=description_text,
        image=image,
        tags=[str(t) for t in tags if isinstance(t, (str, int, float))],
        rating=rating,
        reason=reason,
    )

    final_title = result.title.strip()
    if final_title:
        existing = _recommended_titles_by_session.get(session_id, [])
        if not any(final_title.lower() == t.lower() for t in existing):
            existing.append(final_title)
        # Keep memory bounded.
        _recommended_titles_by_session[session_id] = existing[-20:]
    return result
