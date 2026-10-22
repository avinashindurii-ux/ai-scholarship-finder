"""Shared helpers: LLM calls with recovery, web search with fallback, page fetching, GitHub, PDF."""
import io
import json
import re
import time
from collections import Counter

import requests
from bs4 import BeautifulSoup
from groq import Groq
from pypdf import PdfReader


def extract_json(text):
    """Pull the first valid JSON object or array out of a model reply."""
    text = re.sub(r"```(?:json)?", "", text or "").strip()
    for opener, closer in (("{", "}"), ("[", "]")):
        start, end = text.find(opener), text.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                continue
    return None


class LLM:
    """Groq wrapper. Retries on errors, then switches to a fallback model."""

    def __init__(self, api_key, model="openai/gpt-oss-120b", fallback="openai/gpt-oss-20b"):
        self.client = Groq(api_key=api_key)
        self.models = [m for m in (model, fallback) if m]

    def chat(self, system, user, temperature=0.2, max_tokens=3000):
        last = None
        for model in self.models:
            for attempt in range(3):
                try:
                    r = self.client.chat.completions.create(
                        model=model,
                        temperature=temperature,
                        max_completion_tokens=max_tokens,
                        messages=[{"role": "system", "content": system},
                                  {"role": "user", "content": user}],
                    )
                    return r.choices[0].message.content or ""
                except Exception as e:
                    last = e
                    if "401" in str(e) or "invalid_api_key" in str(e):
                        raise RuntimeError("Groq API key was rejected. Check GROQ_API_KEY.")
                    time.sleep(5 * (attempt + 1))
        raise RuntimeError(f"LLM call failed after retries: {last}")

    def json(self, system, user, **kw):
        system += "\nReturn only valid JSON. No markdown fences, no commentary."
        for _ in range(3):
            data = extract_json(self.chat(system, user, **kw))
            if isinstance(data, dict):
                return data
            user += "\n\nYour last reply was not a valid JSON object. Reply with the JSON object only."
        raise ValueError("Model did not return valid JSON")


def web_search(query, tavily_key=None, n=5):
    """Tavily first. If it fails or returns nothing, fall back to DuckDuckGo."""
    if tavily_key:
        try:
            from tavily import TavilyClient
            res = TavilyClient(api_key=tavily_key).search(query, max_results=n)
            hits = [{"title": r["title"], "url": r["url"], "snippet": r.get("content", "")}
                    for r in res.get("results", [])]
            if hits:
                return hits, "tavily"
        except Exception:
            pass
    try:
        from ddgs import DDGS
        res = DDGS().text(query, max_results=n)
        return [{"title": r["title"], "url": r["href"], "snippet": r["body"]} for r in res], "duckduckgo"
    except Exception:
        return [], "none"


def fetch_page(url, limit=2500):
    """Return readable text of an HTML page, or None if it cannot be read."""
    try:
        r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0 (scholarship-finder demo)"})
        r.raise_for_status()
        if "html" not in r.headers.get("content-type", ""):
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        text = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
        return text[:limit] if len(text) > 300 else None
    except Exception:
        return None


def github_profile(username):
    """Public GitHub data: languages and non-fork repos. Returns None on any failure."""
    try:
        user = requests.get(f"https://api.github.com/users/{username}", timeout=10).json()
        repos = requests.get(f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated",
                             timeout=10).json()
        if not isinstance(repos, list):
            return None
        repos = [r for r in repos if not r.get("fork")]
        langs = Counter(r["language"] for r in repos if r.get("language"))
        return {
            "bio": user.get("bio"),
            "top_languages": [name for name, _ in langs.most_common(5)],
            "repos": [{"name": r["name"], "description": r.get("description"), "language": r.get("language")}
                      for r in repos[:8]],
        }
    except Exception:
        return None


def pdf_text(file):
    try:
        return "\n".join((p.extract_text() or "") for p in PdfReader(file).pages)
    except Exception:
        return ""
