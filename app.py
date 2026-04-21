"""Streamlit UI for the Squad Lead Gen Agent — pitch demo edition."""

from __future__ import annotations

import os
from collections import Counter

import streamlit as st

# Propagate Streamlit Cloud secrets into os.environ before importing src
# modules, since config.py reads keys at import time.
try:
    for _key in ("ANTHROPIC_API_KEY", "PERPLEXITY_API_KEY", "DEMO_MODE"):
        if _key in st.secrets:
            os.environ[_key] = str(st.secrets[_key])
except (FileNotFoundError, st.errors.StreamlitAPIException):
    pass

import pandas as pd  # noqa: E402

from src import storage  # noqa: E402
from src.lead_agent import process_lead  # noqa: E402

DEMO_MODE = os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes")

SIGNAL_COLUMNS = [
    ("Creator volume", "creator_volume"),
    ("Attribution", "attribution_pain"),
    ("Contracts / IP", "contract_pain"),
    ("Buyer fit", "buyer_fit"),
    ("Intent / urgency", "intent_urgency"),
]

CUSTOM_CSS = """<style>
.hero{padding:28px 32px;border-radius:18px;color:white;margin-bottom:24px;background:linear-gradient(135deg,#0b2545 0%,#13315c 55%,#1a4d8a 100%);}
.hero h1{margin:0;font-size:40px;letter-spacing:-0.02em;}
.hero p{margin:8px 0 0;opacity:.88;font-size:16px;max-width:720px;}
.kpi{background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:18px 20px;box-shadow:0 1px 2px rgba(0,0,0,0.03);}
.kpi .label{color:#6b7280;font-size:11px;text-transform:uppercase;letter-spacing:.08em;font-weight:600;}
.kpi .value{font-size:34px;font-weight:700;color:#111827;margin-top:6px;line-height:1;}
.score-pill{display:inline-block;padding:6px 16px;border-radius:999px;color:white;font-weight:700;font-size:15px;}
.hook-tag{display:inline-block;padding:4px 12px;border-radius:6px;background:#eef2ff;color:#3730a3;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;}
.brand-name{font-size:22px;font-weight:700;color:#111827;margin:0;}
</style>"""


def _score_color(score: int) -> str:
    if score >= 8:
        return "#059669"
    if score >= 5:
        return "#d97706"
    return "#dc2626"


def _score_int(raw: object) -> int:
    try:
        return int(raw or 0)
    except (TypeError, ValueError):
        return 0


def _render_hero() -> None:
    st.markdown(
        '<div class="hero"><h1>Squad Outbound AI</h1>'
        "<p>Researches, qualifies, and drafts cold outreach to DTC brands running UGC "
        "creator programs. Every lead scored on five signals with real evidence. "
        "~20 seconds per brand, fully personalized.</p></div>",
        unsafe_allow_html=True,
    )


def _render_kpis(leads: list[dict]) -> None:
    scores = [_score_int(l.get("score")) for l in leads]
    high_fit = sum(1 for s in scores if s >= 8)
    avg = sum(scores) / len(scores) if scores else 0.0
    with_email = sum(1 for l in leads if l.get("email_subject"))
    cells = [
        ("Leads qualified", str(len(leads))),
        ("High fit (8+)", str(high_fit)),
        ("Avg score", f"{avg:.1f}"),
        ("Emails drafted", str(with_email)),
    ]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, cells):
        col.markdown(
            f'<div class="kpi"><div class="label">{label}</div>'
            f'<div class="value">{value}</div></div>',
            unsafe_allow_html=True,
        )


def _render_charts(leads: list[dict]) -> None:
    scores = [_score_int(l.get("score")) for l in leads]
    score_df = pd.DataFrame({"score": scores})
    hook_counts = Counter(l.get("hook_pain", "") for l in leads if l.get("hook_pain"))

    left, right = st.columns(2)
    with left:
        st.markdown("##### Score distribution")
        st.bar_chart(score_df["score"].value_counts().sort_index(), height=220)
    with right:
        st.markdown("##### Winning hook")
        st.bar_chart(pd.Series(hook_counts, name="count"), height=220)


def _render_detail(lead: dict) -> None:
    st.markdown(f"**Why they fit:** {lead.get('summary', '')}")
    st.markdown(f"**Evidence for the hook:** {lead.get('hook_evidence', '')}")

    st.markdown("##### Signal breakdown")
    scorecard = pd.DataFrame(
        {
            "signal": [label for label, _ in SIGNAL_COLUMNS],
            "score": [_score_int(lead.get(key)) for _, key in SIGNAL_COLUMNS],
        }
    ).set_index("signal")
    st.bar_chart(scorecard, height=220)

    st.markdown("##### Drafted email")
    subject = lead.get("email_subject") or "(no subject generated)"
    body = lead.get("email_body") or "(no body generated)"
    st.markdown(f"**Subject:** {subject}")
    st.code(body, language=None)

    with st.expander("Full research dump"):
        st.text(lead.get("research_dump", ""))


def _render_lead_card(lead: dict) -> None:
    score = _score_int(lead.get("score"))
    color = _score_color(score)
    with st.container(border=True):
        header = st.columns([4, 1.2, 1.8, 6])
        header[0].markdown(
            f'<p class="brand-name">{lead.get("brand_name", "")}</p>',
            unsafe_allow_html=True,
        )
        header[1].markdown(
            f'<span class="score-pill" style="background:{color}">{score}/10</span>',
            unsafe_allow_html=True,
        )
        hook = lead.get("hook_pain", "")
        header[2].markdown(
            f'<span class="hook-tag">{hook or "n/a"}</span>',
            unsafe_allow_html=True,
        )
        header[3].write(lead.get("summary", ""))
        with st.expander("Open details"):
            _render_detail(lead)


def main() -> None:
    st.set_page_config(page_title="Squad Outbound AI", layout="wide",
                       initial_sidebar_state="expanded")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    storage.init_csv_if_missing()

    with st.sidebar:
        st.header("Add a brand")
        if DEMO_MODE:
            st.caption("Demo mode: Run agent disabled to protect API credits. "
                       "Browse the pre-qualified leads below.")
            brand = ""
            run_clicked = False
            st.text_input("Brand name", placeholder="Disabled in demo mode",
                          disabled=True)
            st.button("Run agent", type="primary", use_container_width=True,
                      disabled=True)
        else:
            brand = st.text_input("Brand name", placeholder="e.g. Alo Yoga")
            run_clicked = st.button("Run agent", type="primary",
                                    use_container_width=True)
        st.markdown("---")
        try:
            with open(storage._csv_path(), "rb") as f:
                st.download_button("Download leads.csv", data=f.read(),
                                   file_name="leads.csv", mime="text/csv",
                                   use_container_width=True)
        except FileNotFoundError:
            st.caption("No leads.csv yet.")
        st.markdown("---")
        st.subheader("Filters")
        min_score = st.slider("Minimum score", 0, 10, 0)
        hooks = st.multiselect("Winning hook", ["attribution", "contracts"],
                               default=["attribution", "contracts"])

    _render_hero()

    if run_clicked and brand.strip():
        with st.spinner(f"Running the agent on {brand.strip()}..."):
            lead = process_lead(brand.strip())
            storage.append_lead(lead)
            if lead.get("error"):
                st.error(f"Partial result saved. {lead['error']}")
            else:
                st.success(f"Added {lead['brand_name']} — score {lead['score']}/10.")

    leads = storage.load_leads()
    if not leads:
        st.info("No leads yet. Add one on the left, or run `python -m scripts.batch_run`.")
        return

    _render_kpis(leads)
    _render_charts(leads)

    filtered = [
        l for l in leads
        if _score_int(l.get("score")) >= min_score
        and (l.get("hook_pain") or "") in hooks
    ]
    filtered.sort(key=lambda r: _score_int(r.get("score")), reverse=True)

    st.markdown(f"## Qualified leads · showing {len(filtered)} of {len(leads)}")
    if not filtered:
        st.info("No leads match the current filters.")
    for lead in filtered:
        _render_lead_card(lead)


if __name__ == "__main__":
    main()
