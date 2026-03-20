import streamlit as st
import anthropic
import json
import time
from datetime import datetime
from history import add_to_history, get_history, clear_history

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FakeScope · News Verifier",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0d0d0d;
    color: #e8e0d0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #111111 !important;
    border-right: 1px solid #2a2a2a;
}
[data-testid="stSidebar"] * { color: #e8e0d0 !important; }

/* ── Header ── */
.fakescope-header {
    text-align: center;
    padding: 2.5rem 0 1.5rem;
    border-bottom: 1px solid #2a2a2a;
    margin-bottom: 2rem;
}
.fakescope-title {
    font-family: 'Playfair Display', serif;
    font-size: 3.4rem;
    font-weight: 900;
    letter-spacing: -1px;
    color: #f0e6c8;
    line-height: 1;
}
.fakescope-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.22em;
    color: #666;
    margin-top: 0.5rem;
    text-transform: uppercase;
}

/* ── Verdict cards ── */
.verdict-box {
    border-radius: 6px;
    padding: 1.6rem 2rem;
    margin: 1.5rem 0;
    border-left: 5px solid;
    font-family: 'IBM Plex Mono', monospace;
}
.verdict-fake    { background:#1a0a0a; border-color:#c0392b; }
.verdict-real    { background:#0a1a0a; border-color:#27ae60; }
.verdict-mixed   { background:#1a160a; border-color:#e67e22; }
.verdict-unclear { background:#111; border-color:#555; }

.verdict-label {
    font-size: 1.8rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.verdict-fake    .verdict-label { color:#e74c3c; }
.verdict-real    .verdict-label { color:#2ecc71; }
.verdict-mixed   .verdict-label { color:#f39c12; }
.verdict-unclear .verdict-label { color:#888; }

.verdict-score {
    font-size: 0.8rem;
    color: #888;
    margin-top: 0.3rem;
    letter-spacing: 0.1em;
}

/* ── Section labels ── */
.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #666;
    border-bottom: 1px solid #222;
    padding-bottom: 0.4rem;
    margin: 1.5rem 0 0.8rem;
}

/* ── History item ── */
.hist-item {
    padding: 0.75rem 1rem;
    border-radius: 4px;
    background: #161616;
    border: 1px solid #222;
    margin-bottom: 0.6rem;
    cursor: pointer;
    transition: border-color 0.2s;
}
.hist-item:hover { border-color: #444; }
.hist-verdict-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-right: 0.5rem;
    vertical-align: middle;
}

/* ── Textarea & button ── */
textarea {
    background: #111 !important;
    color: #e8e0d0 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 4px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}
textarea:focus { border-color: #555 !important; }

.stButton > button {
    background: #f0e6c8 !important;
    color: #0d0d0d !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    font-size: 0.82rem !important;
    text-transform: uppercase !important;
    border: none !important;
    border-radius: 3px !important;
    padding: 0.65rem 2rem !important;
    width: 100%;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* ── Metric boxes ── */
.metric-row {
    display: flex;
    gap: 1rem;
    margin: 1rem 0;
}
.metric-box {
    flex: 1;
    background: #131313;
    border: 1px solid #222;
    border-radius: 4px;
    padding: 1rem;
    text-align: center;
}
.metric-val {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.6rem;
    font-weight: 600;
    color: #f0e6c8;
}
.metric-lbl {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #555;
    margin-top: 0.2rem;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #111; }
::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #111 !important;
    border: 1px solid #222 !important;
    border-radius: 4px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="fakescope-header">
    <div class="fakescope-title">🔎 FakeScope</div>
    <div class="fakescope-sub">AI-Powered News Credibility Analyzer</div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar: history ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-label">Analysis History</div>', unsafe_allow_html=True)
    history = get_history()
    if not history:
        st.markdown('<p style="color:#555;font-size:0.85rem;">No analyses yet.</p>', unsafe_allow_html=True)
    else:
        color_map = {"FAKE": "#e74c3c", "REAL": "#2ecc71", "MIXED": "#f39c12", "UNCLEAR": "#888"}
        for item in reversed(history[-20:]):
            dot_color = color_map.get(item["verdict"], "#888")
            snippet = item["text"][:60] + "…" if len(item["text"]) > 60 else item["text"]
            st.markdown(f"""
            <div class="hist-item">
                <span class="hist-verdict-dot" style="background:{dot_color}"></span>
                <span style="font-family:'IBM Plex Mono',monospace;font-size:0.72rem;color:{dot_color};font-weight:600">{item["verdict"]}</span>
                <span style="font-family:'IBM Plex Mono',monospace;font-size:0.65rem;color:#555;float:right">{item["confidence"]}%</span>
                <div style="font-size:0.78rem;color:#888;margin-top:0.35rem">{snippet}</div>
                <div style="font-size:0.65rem;color:#444;margin-top:0.2rem">{item["timestamp"]}</div>
            </div>""", unsafe_allow_html=True)

        if st.button("🗑 Clear History"):
            clear_history()
            st.rerun()

    st.markdown("---")
    st.markdown('<div class="section-label">Stats</div>', unsafe_allow_html=True)
    if history:
        total   = len(history)
        fakes   = sum(1 for h in history if h["verdict"] == "FAKE")
        reals   = sum(1 for h in history if h["verdict"] == "REAL")
        avg_conf = round(sum(h["confidence"] for h in history) / total)
        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-box"><div class="metric-val">{total}</div><div class="metric-lbl">Total</div></div>
            <div class="metric-box"><div class="metric-val" style="color:#e74c3c">{fakes}</div><div class="metric-lbl">Fake</div></div>
            <div class="metric-box"><div class="metric-val" style="color:#2ecc71">{reals}</div><div class="metric-lbl">Real</div></div>
        </div>
        <div class="metric-box" style="text-align:center;margin-top:0.5rem">
            <div class="metric-val">{avg_conf}%</div><div class="metric-lbl">Avg Confidence</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#555;font-size:0.82rem;">Run some analyses to see stats.</p>', unsafe_allow_html=True)

# ── Main layout ───────────────────────────────────────────────────────────────
col_input, col_result = st.columns([1, 1], gap="large")

with col_input:
    st.markdown('<div class="section-label">Article / Claim to Analyze</div>', unsafe_allow_html=True)
    article_text = st.text_area(
        label="",
        placeholder="Paste a news article, headline, or any claim here…\n\nExample:\n\"Scientists discover that drinking coffee cures all diseases, government hiding the truth.\"",
        height=300,
        key="article_input",
        label_visibility="collapsed",
    )

    col_a, col_b = st.columns(2)
    with col_a:
        analyze_btn = st.button("⚡ Analyze", use_container_width=True)
    with col_b:
        if st.button("✕ Clear", use_container_width=True):
            st.session_state["article_input"] = ""
            st.session_state.pop("result", None)
            st.rerun()

    st.markdown('<div class="section-label">What FakeScope checks</div>', unsafe_allow_html=True)
    st.markdown("""
    <ul style="color:#888;font-size:0.82rem;line-height:1.9;padding-left:1.2rem">
        <li>Sensational or emotionally charged language</li>
        <li>Logical fallacies & unsupported claims</li>
        <li>Factual plausibility & source credibility cues</li>
        <li>Conspiracy theory patterns</li>
        <li>Scientific or statistical misrepresentation</li>
        <li>Overall credibility assessment</li>
    </ul>
    """, unsafe_allow_html=True)

# ── Analysis logic ────────────────────────────────────────────────────────────
def analyze_article(text: str):
    client = anthropic.Anthropic()
    prompt = f"""You are an expert fact-checker and media literacy analyst. Analyze the following news article or claim for credibility.

Respond ONLY with a valid JSON object (no markdown, no extra text) with exactly these fields:
{{
  "verdict": "FAKE" | "REAL" | "MIXED" | "UNCLEAR",
  "confidence": <integer 0-100>,
  "summary": "<2-3 sentence overall assessment>",
  "red_flags": ["<flag1>", "<flag2>", ...],
  "credibility_factors": ["<factor1>", "<factor2>", ...],
  "language_analysis": "<assessment of tone, bias, sensationalism>",
  "recommendation": "<what the reader should do>"
}}

Verdict guide:
- FAKE: Clear misinformation, fabricated facts, conspiracy content
- REAL: Credible, factual, well-sourced
- MIXED: Some true, some false or misleading elements
- UNCLEAR: Cannot determine without more information

Article/Claim:
\"\"\"
{text}
\"\"\"
"""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ── Run analysis ──────────────────────────────────────────────────────────────
if analyze_btn:
    if not article_text.strip():
        st.warning("Please paste some text to analyze.")
    elif len(article_text.strip()) < 20:
        st.warning("Please provide more text (at least 20 characters).")
    else:
        with col_result:
            with st.spinner("Analyzing credibility…"):
                try:
                    result = analyze_article(article_text)
                    st.session_state["result"] = result
                    st.session_state["analyzed_text"] = article_text
                    add_to_history(article_text, result)
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

# ── Display result ────────────────────────────────────────────────────────────
with col_result:
    if "result" in st.session_state:
        r = st.session_state["result"]
        verdict = r.get("verdict", "UNCLEAR")
        confidence = r.get("confidence", 0)

        verdict_class = {
            "FAKE": "verdict-fake",
            "REAL": "verdict-real",
            "MIXED": "verdict-mixed",
            "UNCLEAR": "verdict-unclear",
        }.get(verdict, "verdict-unclear")

        verdict_emoji = {"FAKE": "🚨", "REAL": "✅", "MIXED": "⚠️", "UNCLEAR": "❓"}.get(verdict, "❓")

        st.markdown(f"""
        <div class="verdict-box {verdict_class}">
            <div class="verdict-label">{verdict_emoji} {verdict}</div>
            <div class="verdict-score">CONFIDENCE · {confidence}%</div>
        </div>
        """, unsafe_allow_html=True)

        # Confidence bar
        bar_color = {"FAKE": "#e74c3c", "REAL": "#2ecc71", "MIXED": "#f39c12", "UNCLEAR": "#666"}.get(verdict, "#666")
        st.markdown(f"""
        <div style="background:#1a1a1a;border-radius:3px;height:6px;margin-bottom:1.2rem">
            <div style="background:{bar_color};width:{confidence}%;height:100%;border-radius:3px;transition:width 0.5s"></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-label">Summary</div>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#ccc;font-size:0.88rem;line-height:1.7">{r.get("summary","")}</p>', unsafe_allow_html=True)

        if r.get("red_flags"):
            st.markdown('<div class="section-label">🚩 Red Flags</div>', unsafe_allow_html=True)
            for flag in r["red_flags"]:
                st.markdown(f'<div style="padding:0.4rem 0;color:#e74c3c;font-size:0.84rem">· {flag}</div>', unsafe_allow_html=True)

        if r.get("credibility_factors"):
            st.markdown('<div class="section-label">✅ Credibility Factors</div>', unsafe_allow_html=True)
            for factor in r["credibility_factors"]:
                st.markdown(f'<div style="padding:0.4rem 0;color:#2ecc71;font-size:0.84rem">· {factor}</div>', unsafe_allow_html=True)

        with st.expander("Language & Tone Analysis"):
            st.markdown(f'<p style="color:#aaa;font-size:0.85rem">{r.get("language_analysis","")}</p>', unsafe_allow_html=True)

        st.markdown('<div class="section-label">📌 Recommendation</div>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#f0e6c8;font-size:0.86rem;font-style:italic">{r.get("recommendation","")}</p>', unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style="height:300px;display:flex;align-items:center;justify-content:center;flex-direction:column;border:1px dashed #222;border-radius:6px;color:#333">
            <div style="font-size:3rem">🔎</div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:0.75rem;letter-spacing:0.15em;text-transform:uppercase;margin-top:0.8rem">Awaiting analysis</div>
        </div>
        """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;margin-top:3rem;padding-top:1.5rem;border-top:1px solid #1a1a1a">
    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.65rem;color:#333;letter-spacing:0.15em">
        FAKESCOPE · POWERED BY CLAUDE AI · FOR EDUCATIONAL USE ONLY
    </span>
</div>
""", unsafe_allow_html=True)
