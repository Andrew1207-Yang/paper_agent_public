from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.config import parse_args
from src.dashboard_ui import (
    render_analytics,
    render_candidate_feed,
    render_daily_queue,
    render_detail_view,
    render_high_confidence_reads,
    render_overview,
    render_papers_table,
    render_research_questions,
    render_resource_warnings,
    render_semantic_retrieval_results,
    render_sidebar_filters,
    render_triage_queue,
)
from src.paper_model import PaperNote
from src.vault_index import index_vault, papers_to_dataframe


st.set_page_config(page_title="Paper Reading Dashboard", layout="wide")


@st.cache_data(show_spinner=False)
def load_papers(base_dir: str, recursive: bool) -> list[PaperNote]:
    return index_vault(Path(base_dir), recursive=recursive)


def main() -> None:
    config = parse_args()

    st.title("Paper Reading Dashboard")
    st.caption("Local markdown-first paper management for an Obsidian vault.")
    render_resource_warnings()

    with st.sidebar:
        st.header("Vault")
        vault_dir = st.text_input(
            "Vault directory",
            value=str(config.vault_dir) if config.vault_dir else "",
            placeholder="/path/to/obsidian/vault",
        )
        paper_subdir = st.text_input(
            "Paper subdirectory",
            value=config.paper_subdir or "",
            placeholder="Optional, e.g. Paper Notes",
        )
        recursive = st.checkbox("Search recursively", value=config.recursive)
        if st.button("Refresh Index", use_container_width=True):
            load_papers.clear()

    base_dir = resolve_base_dir(vault_dir, paper_subdir)
    if base_dir is None:
        st.info("Provide a vault directory in the sidebar or via `--vault_dir`.")
        st.stop()
    if not base_dir.exists():
        st.error(f"Directory does not exist: `{base_dir}`")
        st.stop()

    papers = load_papers(str(base_dir), recursive)
    dataframe = papers_to_dataframe(papers)

    if dataframe.empty:
        st.metric("Total papers found", 0)
        st.warning("No markdown files found in the selected directory.")
        st.stop()

    filtered = render_sidebar_filters(dataframe)
    render_overview(filtered)

    tabs = st.tabs([
        "Papers",
        "Details",
        "Candidate Feed",
        "Semantic Retrieval",
        "Triage Queue",
        "High Confidence Reads",
        "Daily Queue",
        "Analytics",
        "Research Questions",
    ])
    with tabs[0]:
        render_papers_table(filtered)
    with tabs[1]:
        render_detail_view(papers, filtered, on_save=load_papers.clear)
    with tabs[2]:
        render_candidate_feed(filtered)
    with tabs[3]:
        render_semantic_retrieval_results(filtered)
    with tabs[4]:
        render_triage_queue(filtered)
    with tabs[5]:
        render_high_confidence_reads(filtered)
    with tabs[6]:
        render_daily_queue(Path(vault_dir).expanduser() if vault_dir.strip() else None)
    with tabs[7]:
        render_analytics(filtered)
    with tabs[8]:
        render_research_questions(papers)


def resolve_base_dir(vault_dir: str, paper_subdir: str) -> Path | None:
    if not vault_dir.strip():
        return None
    base_dir = Path(vault_dir).expanduser()
    if paper_subdir.strip():
        base_dir = base_dir / paper_subdir.strip()
    return base_dir


if __name__ == "__main__":
    main()
