import os
import time

import streamlit as st

from agents import run_swarm, writer_agent
from style import (CSS, card, footer, hero, log_list, nav, profile_card, results_head,
                   section_head, tracker)
from tools import LLM, pdf_text

SAMPLE_RESUME = """Rahul (fictional sample profile)
Final-year B.Tech Computer Science and Engineering, Jalandhar. CGPA 8.2 / 10.
Skills: Python, scikit-learn, PyTorch basics, SQL, Streamlit, Git.
Projects:
- Crime Incidents Analysis and Prediction: data cleaning, feature engineering and a classifier on public city records.
- Multi-agent debate system: three LLM agents (for, against, moderator) built in Python.
- Expense tracker mobile app built with Flutter.
Interests: machine learning, NLP, applied AI.
Wants to study abroad (Canada, Germany or Singapore). Family cannot afford high tuition fees."""

st.set_page_config(page_title="Scholarship Finder", page_icon="🎓", layout="wide",
                   initial_sidebar_state="collapsed" if os.getenv("GROQ_API_KEY") else "expanded")
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(nav(), unsafe_allow_html=True)

with st.sidebar:
    st.subheader("Keys and model")
    groq_key = st.text_input("Groq API key", value=os.getenv("GROQ_API_KEY", ""), type="password")
    tavily_key = st.text_input("Tavily API key (optional)", value=os.getenv("TAVILY_API_KEY", ""), type="password")
    model = st.text_input("Model", "openai/gpt-oss-120b")
    fallback = st.text_input("Fallback model", "openai/gpt-oss-20b")
    st.caption("Without a Tavily key the search agent uses DuckDuckGo.")

AGENT_INDEX = {"Profile Agent": 0, "Research Agent": 1, "Eligibility Agent": 2, "Ranker Agent": 3}
state = st.session_state.get("state")

if not state:
    hero_box = st.empty()
    hero_box.markdown(hero(), unsafe_allow_html=True)
    form_box = st.empty()
    with form_box.container(key="intake"):
        resume_file = st.file_uploader("Resume (PDF)", type="pdf")
        marks_file = st.file_uploader("Marksheet (PDF, optional)", type="pdf")
        github = st.text_input("GitHub username (optional)")
        goal = st.text_area("What are you hoping to find?",
                            "Masters abroad with a scholarship or funding. Family cannot afford full fees.",
                            height=100)
        with st.expander("No PDF? Paste your resume or try the sample"):
            st.text_area("Resume text", key="resume_paste", height=160)
            st.button("Use the sample profile",
                      on_click=lambda: st.session_state.update(resume_paste=SAMPLE_RESUME))
        _, mid, _ = st.columns([1, 2, 1])
        run = mid.button("Find my matches", type="primary", width="stretch")

    if run:
        resume = (pdf_text(resume_file) if resume_file else "") or st.session_state.get("resume_paste", "")
        if not groq_key:
            st.error("Add your Groq API key in the sidebar, then try again.")
            st.stop()
        if not resume.strip():
            st.error("Upload a resume PDF or paste the text, then try again.")
            st.stop()

        hero_box.empty()
        form_box.empty()
        work = {"resume": resume, "marksheet": pdf_text(marks_file) if marks_file else "",
                "github": github.strip(), "goal": goal, "trace": []}
        box = st.empty()

        def log(agent, msg):
            work["trace"].append((agent, msg))
            active = AGENT_INDEX.get(agent, 0)
            states = ["done" if i < active else "work" if i == active else "wait" for i in range(4)] + ["ready"]
            box.markdown(tracker(states, work["trace"]), unsafe_allow_html=True)

        box.markdown(tracker(["work", "wait", "wait", "wait", "ready"], [("Profile Agent", "Starting")]),
                     unsafe_allow_html=True)
        try:
            run_swarm(LLM(groq_key, model, fallback), work, log, tavily_key)
        except Exception as e:
            st.error(f"The run stopped: {e}")
            st.button("Try again")
            st.stop()
        box.markdown(tracker(["done"] * 4 + ["ready"], work["trace"]), unsafe_allow_html=True)
        time.sleep(1.2)
        st.session_state.state = work
        st.session_state.sop = None
        st.rerun()
else:
    st.markdown(results_head(state), unsafe_allow_html=True)
    _, mid, _ = st.columns([2, 1, 2])
    if mid.button("Start over", type="tertiary", width="stretch"):
        st.session_state.pop("state", None)
        st.session_state.pop("sop", None)
        st.rerun()

    top_tab, all_tab, profile_tab, log_tab = st.tabs(["Best matches", "Everything checked", "Your profile", "Agent log"])

    with top_tab:
        for n, o in enumerate(state["top5"], 1):
            st.markdown(card(n, o), unsafe_allow_html=True)

        st.markdown(section_head("Draft an application", "Pick a match and the Writer agent prepares a first draft."),
                    unsafe_allow_html=True)
        _, mid, _ = st.columns([1, 2, 1])
        names = [o["name"] for o in state["top5"]]
        choice = mid.selectbox("Which opportunity?", names)
        if mid.button("Write the draft", width="stretch"):
            with st.spinner("The Writer agent is drafting"):
                opp = state["top5"][names.index(choice)]
                st.session_state.sop = writer_agent(LLM(groq_key, model, fallback), state, opp)
        if st.session_state.get("sop"):
            st.text_area("Draft statement of purpose", st.session_state.sop, height=380)
            st.caption("This is a draft. Fill in the placeholders and check every fact before you use it. "
                       "Nothing is submitted anywhere.")
            st.download_button("Download the draft", st.session_state.sop, file_name="sop_draft.txt")

    with all_tab:
        st.dataframe([{"Name": o["name"], "Country": o.get("country"), "Fit": o["fit_score"],
                       "Eligible": o.get("eligible"), "Deadline": o.get("deadline"),
                       "Source checked": o["source_checked"], "URL": o["url"]} for o in state["evaluated"]],
                     width="stretch")

    with profile_tab:
        st.markdown(profile_card(state["profile"]), unsafe_allow_html=True)

    with log_tab:
        st.markdown(log_list(state["trace"]), unsafe_allow_html=True)

st.markdown(footer(), unsafe_allow_html=True)
