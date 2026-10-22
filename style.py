"""Look and feel: CSS plus small HTML builders. Everything that comes from a model or the web is escaped."""
import html


def esc(x):
    return html.escape("" if x is None else str(x))


def h(s):
    """Collapse indented HTML so Markdown never mistakes it for a code block."""
    return "".join(line.strip() for line in s.splitlines())


def as_list(v):
    if isinstance(v, list):
        return v
    return [v] if v else []


def score_of(o):
    try:
        return max(0, min(100, int(float(o.get("fit_score")))))
    except (TypeError, ValueError):
        return 0


RING = 339.29  # circumference for r=54

CSS = h("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
:root{--canvas:#F5F5F7;--surface:#FFFFFF;--ink:#1D1D1F;--sub:#6E6E73;--hair:#E5E5EA;--blue:#0071E3;--blue-hover:#0077ED;--green:#1D7F3B;--green-bg:#E6F4EA;--amber:#8A5300;--amber-bg:#FDF1DC;--red:#B3261E;--red-bg:#FBE9E7;--font:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","Inter","Segoe UI",Roboto,sans-serif;--lift:0 1px 3px rgba(0,0,0,.04),0 10px 32px rgba(0,0,0,.05);}
html,body,.stApp{background:var(--canvas);color:var(--ink);font-family:var(--font);-webkit-font-smoothing:antialiased;}
.stMarkdown,.stMarkdown *,label,p,button,input,textarea,[data-baseweb="tab"],[data-testid="stWidgetLabel"] *{font-family:var(--font);}
#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none;}
header[data-testid="stHeader"]{background:transparent;}
.block-container,[data-testid="stMainBlockContainer"]{max-width:980px;padding:6rem 1.5rem 4rem;}
.nav{position:fixed;top:0;left:0;right:0;height:52px;z-index:99;display:flex;align-items:center;justify-content:center;background:rgba(245,245,247,.8);backdrop-filter:saturate(180%) blur(20px);-webkit-backdrop-filter:saturate(180%) blur(20px);border-bottom:1px solid rgba(0,0,0,.06);font-size:1.05rem;font-weight:600;letter-spacing:-.01em;color:var(--ink);}
.hero{text-align:center;padding:2.4rem 0 2.6rem;}
.hero-t{font-size:clamp(2.4rem,6vw,4.4rem);font-weight:600;letter-spacing:-.035em;line-height:1.04;max-width:11em;margin:0 auto 1.2rem;color:var(--ink);}
.hero-s{font-size:clamp(1.05rem,2vw,1.35rem);line-height:1.45;color:var(--sub);max-width:30em;margin:0 auto;}
@media (prefers-reduced-motion:no-preference){.hero{animation:rise .9s cubic-bezier(.2,.7,.2,1) both;}@keyframes rise{from{opacity:0;transform:translateY(10px);}}}
.st-key-intake{width:100%;max-width:680px;margin:0 auto;background:var(--surface);border-radius:28px;padding:2.4rem 2.6rem;box-shadow:var(--lift);}
[data-testid="stWidgetLabel"] p{font-size:.9rem;font-weight:500;color:var(--sub);}
[data-testid="stFileUploaderDropzone"]{background:var(--canvas);border:1px dashed #C7C7CC;border-radius:16px;}
[data-testid="stFileUploaderDropzone"] button{border-radius:980px;}
[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="textarea"]{background:var(--canvas) !important;border:none !important;border-radius:12px !important;}
[data-baseweb="input"]:focus-within,[data-baseweb="textarea"]:focus-within{box-shadow:0 0 0 3px rgba(0,113,227,.3);}
[data-baseweb="select"]>div{background:var(--canvas);border:none;border-radius:12px;}
[data-testid="stExpander"] details{border:1px solid var(--hair);border-radius:14px;background:transparent;}
[data-testid="stBaseButton-primary"],button[kind="primary"]{background:var(--blue);border:none;border-radius:980px;min-height:3rem;padding:.6rem 1.8rem;transition:background .2s;}
[data-testid="stBaseButton-primary"]:hover,button[kind="primary"]:hover{background:var(--blue-hover);}
[data-testid="stBaseButton-primary"] p,button[kind="primary"] p{color:#fff;font-size:1.05rem;font-weight:500;}
[data-testid="stBaseButton-secondary"],[data-testid="stDownloadButton"] button,button[kind="secondary"]{background:#E8E8ED;border:none;border-radius:980px;color:var(--ink);padding:.5rem 1.4rem;}
[data-testid="stBaseButton-secondary"] p{font-weight:500;}
[data-testid="stBaseButton-tertiary"] p{color:var(--blue);font-weight:500;font-size:1rem;}
.stTabs [data-baseweb="tab-list"]{justify-content:center;gap:10px;}
.stTabs [data-baseweb="tab"]{font-weight:500;font-size:1rem;color:var(--sub);}
.stTabs [aria-selected="true"]{color:var(--ink);}
.stTabs [data-baseweb="tab-highlight"]{background:var(--ink);height:2px;}
.stTabs [data-baseweb="tab-border"]{background:var(--hair);}
.run{text-align:center;padding:2.6rem 0 1rem;}
.run-t{font-size:clamp(2rem,4.6vw,3.2rem);font-weight:600;letter-spacing:-.03em;line-height:1.1;}
.run-s{color:var(--sub);font-size:1.1rem;margin-top:.9rem;min-height:1.6em;}
.track{display:grid;grid-template-columns:repeat(5,1fr);max-width:780px;margin:3rem auto 1.4rem;}
.stop{position:relative;padding-top:32px;text-align:center;font-size:.92rem;line-height:1.35;}
.stop::before{content:"";position:absolute;left:50%;width:100%;top:7px;height:2px;background:var(--hair);}
.stop:last-child::before{display:none;}
.stop::after{content:"";position:absolute;left:50%;margin-left:-8px;top:0;width:16px;height:16px;border-radius:50%;background:var(--surface);border:2px solid #C7C7CC;box-sizing:border-box;}
.stop b{display:block;font-weight:600;color:var(--ink);}
.stop span{color:var(--sub);font-size:.84rem;}
.stop.done::before{background:var(--blue);}
.stop.done::after{background:var(--blue);border-color:var(--blue);}
.stop.work::after{border-color:var(--blue);box-shadow:0 0 0 5px rgba(0,113,227,.15);}
.stop.ready::after{border-style:dashed;}
@media (prefers-reduced-motion:no-preference){.stop.work::after{animation:breathe 2s ease-in-out infinite;}@keyframes breathe{50%{box-shadow:0 0 0 9px rgba(0,113,227,.08);}}}
.logs{max-width:560px;margin:1.6rem auto 0;text-align:center;}
.logline{font-size:.92rem;color:var(--sub);padding:3px 0;line-height:1.45;}
.logline b{font-weight:600;margin-right:6px;color:var(--sub);}
.logline.now,.logline.now b{color:var(--ink);}
.rh{text-align:center;padding:1.4rem 0 .6rem;}
.rh .hero-t{font-size:clamp(2.1rem,5vw,3.4rem);}
.sec{text-align:center;margin:4rem 0 1.6rem;}
.sec-t{font-size:clamp(1.8rem,4vw,2.6rem);font-weight:600;letter-spacing:-.03em;line-height:1.1;margin-bottom:.6rem;}
.sec-s{color:var(--sub);font-size:1.1rem;}
.card{display:grid;grid-template-columns:1fr 150px;gap:30px;background:var(--surface);border-radius:28px;padding:38px 40px;margin:0 0 20px;box-shadow:var(--lift);}
.c-main{min-width:0;}
.c-top{display:flex;gap:12px;align-items:center;font-size:.95rem;color:var(--sub);margin-bottom:8px;}
.c-best{color:var(--blue);font-weight:600;}
.c-name{font-size:1.9rem;font-weight:600;letter-spacing:-.022em;line-height:1.12;}
.c-prov{font-size:1.05rem;color:var(--sub);margin-top:.35rem;}
.c-reason{font-size:1.06rem;line-height:1.55;margin:1.2rem 0 1.4rem;max-width:50ch;}
.c-facts{display:grid;grid-template-columns:1fr 1fr;gap:24px;border-top:1px solid var(--hair);padding-top:1.1rem;margin-bottom:.9rem;}
.c-facts span{display:block;font-size:.82rem;color:var(--sub);margin-bottom:3px;}
.c-facts div{font-size:1.02rem;font-weight:500;line-height:1.4;}
.c-main details{padding-top:.2rem;}
.c-main summary{cursor:pointer;list-style:none;color:var(--blue);font-size:1rem;font-weight:500;padding:4px 0;}
.c-main summary::-webkit-details-marker{display:none;}
.c-main summary::after{content:"";display:inline-block;width:7px;height:7px;border-right:2px solid var(--blue);border-bottom:2px solid var(--blue);transform:rotate(45deg);margin-left:10px;position:relative;top:-2px;transition:transform .25s;}
.c-main details[open] summary::after{transform:rotate(-135deg);top:1px;}
.c-main summary:focus-visible,.c-more a:focus-visible{outline:2px solid var(--blue);outline-offset:3px;border-radius:4px;}
.c-more{padding:.6rem 0 .2rem;font-size:1rem;line-height:1.6;}
.c-h{font-weight:600;font-size:.95rem;margin:1rem 0 .25rem;}
.c-more ul,.profile ul{margin:0;padding-left:1.2em;}
.c-more p{margin:0;}
.c-more a{color:var(--blue);font-weight:500;text-decoration:none;}
.c-more a:hover{text-decoration:underline;}
.src{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin-top:1rem !important;}
.c-ring{display:flex;flex-direction:column;align-items:center;gap:16px;padding-top:6px;}
.ring{position:relative;width:124px;height:124px;}
.ring svg{width:100%;height:100%;transform:rotate(-90deg);}
.ring circle{fill:none;stroke-width:7;}
.ring .tr{stroke:var(--hair);}
.ring .fg{stroke:var(--blue);stroke-linecap:round;stroke-dasharray:339.29;}
.ring.unlikely .fg{stroke:#AEAEB2;}
@media (prefers-reduced-motion:no-preference){.ring .fg{animation:fill 1.4s cubic-bezier(.22,.8,.3,1) both;}@keyframes fill{from{stroke-dashoffset:339.29;}}}
.ring-n{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:2.2rem;font-weight:600;letter-spacing:-.03em;line-height:1;}
.ring-n small{font-size:.76rem;font-weight:400;color:var(--sub);letter-spacing:0;margin-top:4px;}
.pill,.chip{display:inline-block;font-size:.84rem;font-weight:500;padding:4px 12px;border-radius:99px;line-height:1.4;background:var(--canvas);color:var(--ink);}
.chip{margin:0 6px 8px 0;}
.pill.likely,.chip.ok{background:var(--green-bg);color:var(--green);}
.pill.unclear,.chip.warn{background:var(--amber-bg);color:var(--amber);}
.pill.unlikely{background:var(--red-bg);color:var(--red);}
.profile{background:var(--surface);border-radius:28px;padding:36px 40px;box-shadow:var(--lift);}
.p-name{font-size:1.9rem;font-weight:600;letter-spacing:-.022em;}
.p-sub{color:var(--sub);margin:.3rem 0 1rem;}
.profile p{max-width:56ch;line-height:1.6;}
.note{text-align:center;color:var(--sub);font-size:.9rem;margin:4rem auto 0;max-width:46ch;line-height:1.5;}
@media (max-width:680px){
.st-key-intake{padding:1.6rem 1.3rem;}
.track{grid-template-columns:1fr;margin-top:2rem;}
.stop{text-align:left;padding:0 0 18px 32px;}
.stop::before{left:7px;top:16px;bottom:0;width:2px;height:auto;}
.stop::after{left:0;margin-left:0;top:2px;}
.card{grid-template-columns:1fr;padding:28px 24px;gap:20px;}
.c-ring{flex-direction:row;order:-1;justify-content:flex-start;}
.ring{width:88px;height:88px;}
.ring-n{font-size:1.5rem;}
.c-facts{grid-template-columns:1fr;gap:14px;}
.profile{padding:28px 24px;}
}
</style>
""")

STEPS = [("Profile", "Reads your documents"), ("Research", "Searches the web"),
         ("Eligibility", "Reads official pages"), ("Ranker", "Picks the top five"),
         ("Writer", "Drafts on request")]
TITLES = ["Reading your documents", "Searching the web", "Checking the official pages", "Choosing your best matches"]


def nav():
    return '<div class="nav">Scholarship Finder</div>'


def hero():
    return h("""<div class="hero"><div class="hero-t">Find the scholarships that fit you.</div>
    <div class="hero-s">Upload your resume. Our agents search the web, read the official pages, and show you where you can apply.</div></div>""")


def tracker(states, lines):
    title = next((TITLES[i] for i, s in enumerate(states[:4]) if s == "work"), "All set")
    sub = esc(lines[-1][1]) if lines else ""
    stops = "".join(f'<div class="stop {s}"><b>{n}</b><span>{d}</span></div>' for (n, d), s in zip(STEPS, states))
    recent = lines[-4:]
    log = "".join(f'<div class="logline{" now" if i == len(recent) - 1 else ""}"><b>{esc(a)}</b>{esc(m)}</div>'
                  for i, (a, m) in enumerate(recent))
    return h(f'<div class="run"><div class="run-t">{title}</div><div class="run-s">{sub}</div></div>'
             f'<div class="track">{stops}</div><div class="logs">{log}</div>')


def results_head(state):
    ev = state["evaluated"]
    official = sum(1 for o in ev if o.get("source_checked") == "official page")
    return h(f"""<div class="rh"><div class="hero-t">Your best matches</div>
    <div class="hero-s">{len(ev)} opportunities checked, {official} read from the official page.</div></div>""")


def section_head(title, sub):
    return f'<div class="sec"><div class="sec-t">{esc(title)}</div><div class="sec-s">{esc(sub)}</div></div>'


def card(n, o):
    elig = str(o.get("eligible") or "unclear").lower()
    if elig not in ("likely", "unclear", "unlikely"):
        elig = "unclear"
    label = {"likely": "Likely eligible", "unclear": "Unclear fit", "unlikely": "Unlikely"}[elig]
    score = score_of(o)
    offset = round(RING * (1 - score / 100), 2)
    reqs = "".join(f"<li>{esc(r)}</li>" for r in as_list(o.get("requirements"))) or "<li>Not found on page</li>"
    gaps = "".join(f"<li>{esc(r)}</li>" for r in as_list(o.get("missing_info"))) or "<li>Nothing flagged</li>"
    url = str(o.get("url") or "")
    link = esc(url) if url.startswith(("http://", "https://")) else "#"
    official = o.get("source_checked") == "official page"
    chip = ('<span class="chip ok">Checked official page</span>' if official
            else '<span class="chip warn">Search snippet only</span>')
    best = '<span class="c-best">Best match</span>' if n == 1 else ""
    return h(f"""<article class="card"><div class="c-main">
    <div class="c-top">{best}<span>{esc(o.get("country"))}</span></div>
    <div class="c-name">{esc(o.get("name"))}</div>
    <div class="c-prov">{esc(o.get("provider"))}</div>
    <p class="c-reason">{esc(o.get("reason") or o.get("why"))}</p>
    <div class="c-facts"><div><span>Funding</span>{esc(o.get("funding"))}</div><div><span>Deadline</span>{esc(o.get("deadline"))}</div></div>
    <details><summary>Requirements and how to apply</summary><div class="c-more">
    <div class="c-h">Requirements</div><ul>{reqs}</ul>
    <div class="c-h">Still needed from you</div><ul>{gaps}</ul>
    <div class="c-h">How to apply</div><p>{esc(o.get("how_to_apply"))}</p>
    <p class="src">{chip}<a href="{link}" target="_blank" rel="noopener noreferrer">Open the source page</a></p>
    </div></details></div>
    <div class="c-ring"><div class="ring {elig}"><svg viewBox="0 0 124 124" aria-hidden="true"><circle class="tr" cx="62" cy="62" r="54"/>
    <circle class="fg" cx="62" cy="62" r="54" style="stroke-dashoffset:{offset}"/></svg>
    <div class="ring-n">{score}<small>fit</small></div></div><div class="pill {elig}">{label}</div></div>
    </article>""")


ticket = card


def profile_card(p):
    chips = lambda items, cls="": "".join(f'<span class="chip {cls}">{esc(i)}</span>' for i in as_list(items))
    sub = ", ".join(str(x) for x in (p.get("degree"), p.get("university")) if x)
    if p.get("cgpa"):
        sub += f", CGPA {p.get('cgpa')}"
    projects = "".join(f"<li>{esc(x)}</li>" for x in as_list(p.get("projects")))
    return h(f"""<div class="profile"><div class="p-name">{esc(p.get("name") or "Student")}</div>
    <div class="p-sub">{esc(sub)}</div><p>{esc(p.get("summary"))}</p>
    <div class="c-h">Skills</div><div>{chips(p.get("skills"))}</div>
    <div class="c-h">Projects</div><ul>{projects}</ul>
    <div class="c-h">Scholarships often ask for these, and they are not in your documents</div>
    <div>{chips(p.get("missing_info"), "warn")}</div></div>""")


def log_list(lines):
    return '<div class="logs">' + "".join(
        f'<div class="logline"><b>{esc(a)}</b>{esc(m)}</div>' for a, m in lines) + "</div>"


def footer():
    return h("""<div class="note">Every link comes from a real search result, and each result says whether the official
    page was read. Drafts are never submitted anywhere.</div>""")
