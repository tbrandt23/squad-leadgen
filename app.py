"""Streamlit UI for the Squad Lead Gen Agent.

Sidebar: brand input, run button, CSV download.
Main: color-coded leads table with an expandable detail view per row.
"""

from __future__ import annotations

import streamlit as st

from src import storage
from src.lead_agent import process_lead


def _score_color(score: int) -> str:
    if score >= 8:
        return "#1f883d"
    if score >= 5:
        return "#bf8700"
    return "#cf222e"


def _score_badge(score_raw: str) -> str:
    try:
        score = int(score_raw)
    except (TypeError, ValueError):
        score = 0
    color = _score_color(score)
    return (
        f"<span style='background:{color};color:white;padding:2px 8px;"
        f"border-radius:10px;font-weight:600'>{score}</span>"
    )


def _render_detail(lead: dict[str, str]) -> None:
    st.markdown(f"### {lead['brand_name']}")
    st.markdown(f"**Summary:** {lead.get('summary', '')}")
    st.markdown(f"**Winning hook:** `{lead.get('hook_pain', '')}`")
    st.markdown(f"**Evidence:** {lead.get('hook_evidence', '')}")

    st.markdown("#### Scorecard")
    cols = st.columns(5)
    signals = [
        ("Creator volume", lead.get("creator_volume", "0")),
        ("Attribution", lead.get("attribution_pain", "0")),
        ("Contracts/IP", lead.get("contract_pain", "0")),
        ("Buyer fit", lead.get("buyer_fit", "0")),
        ("Intent/urgency", lead.get("intent_urgency", "0")),
    ]
    for col, (label, value) in zip(cols, signals):
        col.metric(label, f"{value}/3")

    st.markdown("#### Email")
    st.markdown(f"**Subject:** {lead.get('email_subject', '')}")
    st.text(lead.get("email_body", ""))

    st.markdown("#### Research dump")
    st.text(lead.get("research_dump", ""))


def main() -> None:
    st.set_page_config(page_title="Squad Lead Gen Agent", layout="wide")
    st.title("Squad Lead Gen Agent")
    st.caption("Research, qualify, and draft outreach for DTC brands in ~20s.")

    storage.init_csv_if_missing()

    with st.sidebar:
        st.header("Add a brand")
        brand_input = st.text_input("Brand name", key="brand_input")
        run_clicked = st.button("Run agent", type="primary", use_container_width=True)

        st.markdown("---")
        try:
            with open(storage._csv_path(), "rb") as f:
                st.download_button(
                    "Download leads.csv",
                    data=f.read(),
                    file_name="leads.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        except FileNotFoundError:
            st.caption("No leads.csv yet.")

    if run_clicked and brand_input.strip():
        with st.spinner(f"Processing {brand_input.strip()}..."):
            lead = process_lead(brand_input.strip())
            storage.append_lead(lead)
            if lead.get("error"):
                st.error(f"Partial result. {lead['error']}")
            else:
                st.success(f"Added {lead['brand_name']} (score {lead['score']}).")

    leads = storage.load_leads()
    if not leads:
        st.info("No leads yet. Add a brand on the left or run scripts/batch_run.py.")
        return

    leads_sorted = sorted(
        leads,
        key=lambda r: int(r.get("score") or 0),
        reverse=True,
    )

    header_cols = st.columns([2, 1, 2, 5])
    for col, label in zip(header_cols, ("Brand", "Score", "Hook", "Summary")):
        col.markdown(f"**{label}**")

    for lead in leads_sorted:
        cols = st.columns([2, 1, 2, 5])
        cols[0].write(lead.get("brand_name", ""))
        cols[1].markdown(_score_badge(lead.get("score", "0")), unsafe_allow_html=True)
        cols[2].write(lead.get("hook_pain", ""))
        cols[3].write(lead.get("summary", ""))
        with st.expander(f"Details: {lead.get('brand_name', '')}"):
            _render_detail(lead)


if __name__ == "__main__":
    main()
