"""Five agents that pass a shared state dict along: profile -> research -> eligibility -> ranker -> writer."""
import json

from tools import fetch_page, github_profile, web_search


def compact(profile):
    keys = ["degree", "cgpa", "skills", "projects", "achievements", "interests", "preferred_countries", "goal"]
    return json.dumps({k: profile.get(k) for k in keys})[:1500]


def to_score(value):
    try:
        return max(0, min(100, int(float(value))))
    except (TypeError, ValueError):
        return 0


# 1. Profile Agent ---------------------------------------------------------------------------

PROFILE_SYS = """You build a student profile from the documents given.
Use only facts that appear in the input. Never invent grades, projects or achievements.
Return JSON with these keys: name, degree, university, cgpa, graduation_year, skills (list),
projects (list of short strings), achievements (list), interests (list),
preferred_countries (list, only if the student's notes say so), summary (two sentences),
missing_info (list of things scholarships often ask for that are absent, such as an English test score
or recommendation letters)."""


def profile_agent(llm, state, log):
    log("Profile Agent", "Reading resume and marksheet")
    gh = None
    if state["github"]:
        log("Profile Agent", f"Looking up GitHub user {state['github']}")
        gh = github_profile(state["github"])
        log("Profile Agent", "GitHub data found" if gh else "GitHub lookup failed, continuing with documents only")
    prompt = (f"RESUME:\n{state['resume'][:6000]}\n\nMARKSHEET:\n{state['marksheet'][:2000]}\n\n"
              f"GITHUB:\n{json.dumps(gh)[:2500]}\n\nSTUDENT NOTES:\n{state['goal']}")
    profile = llm.json(PROFILE_SYS, prompt)
    profile["goal"] = state["goal"]
    state["profile"] = profile
    log("Profile Agent", f"Profile ready: {len(profile.get('skills') or [])} skills, "
                         f"{len(profile.get('projects') or [])} projects")


# 2. Research Agent --------------------------------------------------------------------------

def pick_candidates(llm, profile, results):
    listing = "\n".join(f"[{i}] {r['title'][:90]} | {r['url'][:80]} | {r['snippet'][:200]}"
                        for i, r in enumerate(results[:40]))
    data = llm.json(
        "From these search results pick up to 12 that are a specific, real scholarship, fellowship or "
        "university program this student could apply to. Skip blog posts, listicles and news. "
        "Prefer official sites. Return JSON: "
        '{"picks": [{"id": <result number>, "name": "...", "provider": "...", "country": "..."}]}. '
        "Use only result numbers from the list.",
        f"STUDENT: {compact(profile)}\n\nRESULTS:\n{listing}")
    out, used = [], set()
    for p in data.get("picks", []):
        try:
            i = int(p.get("id"))
        except (TypeError, ValueError):
            continue
        if 0 <= i < len(results) and i not in used:
            used.add(i)
            # The URL always comes from the search results, never from the model.
            out.append({**p, "url": results[i]["url"], "snippet": results[i]["snippet"]})
    return out


def research_agent(llm, state, log, tavily_key):
    profile = state["profile"]
    queries = llm.json(
        "You plan web searches to find real scholarships and university programs for a student. "
        'Return JSON: {"queries": [five short search queries]}. Mix funding-focused and program-focused '
        "queries and use the student's preferred countries if there are any.",
        compact(profile)).get("queries", [])[:5]

    results, seen = [], set()

    def collect(qs):
        for q in qs:
            hits, engine = web_search(q, tavily_key)
            log("Research Agent", f'Searched "{q}" via {engine}: {len(hits)} results')
            for h in hits:
                if h["url"] not in seen:
                    seen.add(h["url"])
                    results.append(h)

    collect(queries)
    candidates = pick_candidates(llm, profile, results) if results else []

    if len(candidates) < 10:
        log("Research Agent", f"Only {len(candidates)} candidates, running broader searches")
        field = (profile.get("degree") or "computer science")
        countries = profile.get("preferred_countries") or ["Europe", "Canada", "Asia"]
        collect([f"fully funded masters scholarships international students {field} {c}" for c in countries[:3]])
        candidates = pick_candidates(llm, profile, results) if results else []

    state["results"], state["candidates"] = results, candidates
    log("Research Agent", f"{len(candidates)} candidate opportunities from {len(results)} search results")


# 3. Eligibility Agent -----------------------------------------------------------------------

ELIG_SYS = """You check whether a student fits a scholarship or program, using ONLY the page text provided.
If the page does not say something, write "not found on page". Do not guess deadlines or amounts.
Return JSON with keys: requirements (list of short strings), deadline, funding, how_to_apply,
eligible ("likely", "unclear" or "unlikely"), fit_score (0 to 100), why (one sentence),
missing_info (list of things the student must provide or confirm)."""


def eligibility_agent(llm, state, log):
    evaluated = []
    for c in state["candidates"][:12]:
        page = fetch_page(c["url"])
        checked = "official page" if page else "search snippet only"
        log("Eligibility Agent", f"{c['name']}: read {checked}")
        try:
            r = llm.json(ELIG_SYS, f"STUDENT: {compact(state['profile'])}\n\nOPPORTUNITY: {c['name']} "
                                   f"({c['url']})\n\nPAGE TEXT:\n{page or c['snippet']}")
        except Exception as e:
            log("Eligibility Agent", f"{c['name']}: skipped after error ({str(e)[:80]})")
            continue
        r["fit_score"] = to_score(r.get("fit_score"))
        evaluated.append({**c, **r, "source_checked": checked})
    state["evaluated"] = evaluated
    log("Eligibility Agent", f"Checked {len(evaluated)} opportunities")


# 4. Ranker Agent ----------------------------------------------------------------------------

def ranker_agent(llm, state, log):
    ev = state["evaluated"]
    brief = "\n".join(
        f"[{i}] {x['name']} | {x.get('country')} | funding: {str(x.get('funding'))[:80]} | "
        f"deadline: {x.get('deadline')} | {x.get('eligible')} | score {x['fit_score']}"
        for i, x in enumerate(ev))
    top, used = [], set()
    try:
        data = llm.json(
            "You rank opportunities for a student who cannot afford tuition, so strong funding matters as "
            "much as fit. Pick the best 5 and skip any marked unlikely. "
            'Return JSON: {"top": [{"id": <number>, "reason": "one sentence"}]}.',
            f"STUDENT: {compact(state['profile'])}\n\n{brief}")
        for t in data.get("top", []):
            try:
                i = int(t.get("id"))
            except (TypeError, ValueError):
                continue
            if 0 <= i < len(ev) and i not in used:
                used.add(i)
                top.append({**ev[i], "reason": t.get("reason") or ev[i].get("why")})
    except Exception as e:
        log("Ranker Agent", f"Ranking call failed ({str(e)[:80]}), using fit score order")

    if len(top) < 5:  # recovery: fill from the best fit scores
        for i in sorted(range(len(ev)), key=lambda k: -ev[k]["fit_score"]):
            if len(top) >= 5:
                break
            if i not in used:
                used.add(i)
                top.append({**ev[i], "reason": ev[i].get("why")})
    state["top5"] = top[:5]
    log("Ranker Agent", "Top 5 ready")


# 5. Application Writer Agent ----------------------------------------------------------------

def writer_agent(llm, state, opp):
    return llm.chat(
        "You write a first draft of a statement of purpose for a student. Use only facts from the profile. "
        "Do not invent grades, projects, awards or experiences. Where something is missing, write a "
        "[PLACEHOLDER: what to add]. First person, about 350 words, plain and specific, no cliches. "
        "Avoid em dashes.",
        f"PROFILE: {json.dumps(state['profile'])[:2500]}\n\nOPPORTUNITY: {opp['name']} at {opp.get('provider')}, "
        f"{opp.get('country')}\nREQUIREMENTS: {opp.get('requirements')}\nFUNDING: {opp.get('funding')}",
        temperature=0.5, max_tokens=1500)


def run_swarm(llm, state, log, tavily_key=None):
    profile_agent(llm, state, log)
    research_agent(llm, state, log, tavily_key)
    eligibility_agent(llm, state, log)
    ranker_agent(llm, state, log)
    return state
