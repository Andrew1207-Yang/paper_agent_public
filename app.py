from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import parse_args
from src.filters import apply_filters, split_topics
from src.paper_model import ALLOWED_STATUSES, SCORE_VALUES, PaperNote
from src.update_note import update_note_frontmatter
from src.vault_index import index_vault, papers_to_dataframe
from src.visualizations import (
    average_rating_by_topic,
    papers_added_over_time,
    papers_by_status,
    papers_by_topic,
)


st.set_page_config(page_title="Paper Reading Dashboard", layout="wide")


@st.cache_data(show_spinner=False)
def load_papers(base_dir: str, recursive: bool) -> list[PaperNote]:
    return index_vault(Path(base_dir), recursive=recursive)


def main() -> None:
    config = parse_args()

    st.title("Paper Reading Dashboard")
    st.caption("Local markdown-first paper management for an Obsidian vault.")

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

    tabs = st.tabs(["Papers", "Details", "Analytics", "Research Questions"])
    with tabs[0]:
        render_papers_table(filtered)
    with tabs[1]:
        render_detail_view(papers, filtered)
    with tabs[2]:
        render_analytics(filtered)
    with tabs[3]:
        render_research_questions(papers)


def resolve_base_dir(vault_dir: str, paper_subdir: str) -> Path | None:
    if not vault_dir.strip():
        return None
    base_dir = Path(vault_dir).expanduser()
    if paper_subdir.strip():
        base_dir = base_dir / paper_subdir.strip()
    return base_dir


def render_sidebar_filters(dataframe: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.header("Filters")
        statuses = st.multiselect("Status", ALLOWED_STATUSES)
        topics = st.multiselect("Topic", sorted(all_topics(dataframe)))
        sources = st.multiselect("Source", sorted(non_null_values(dataframe, "source")))
        priorities = st.multiselect("Priority", SCORE_VALUES)
        ratings = st.multiselect("Rating", SCORE_VALUES)

    return apply_filters(dataframe, statuses, topics, sources, priorities, ratings)


def render_overview(dataframe: pd.DataFrame) -> None:
    total = len(dataframe)
    read = int((dataframe["status"] == "read").sum())
    candidate = int((dataframe["status"] == "candidate").sum())
    average_rating = dataframe["rating"].dropna().mean()

    columns = st.columns(4)
    columns[0].metric("Total Papers", total)
    columns[1].metric("Read Papers", read)
    columns[2].metric("Candidate Papers", candidate)
    columns[3].metric(
        "Average Rating",
        "N/A" if pd.isna(average_rating) else f"{average_rating:.2f}",
    )
    st.caption(f"Total papers found: {total}")


def render_papers_table(dataframe: pd.DataFrame) -> None:
    st.subheader("Papers")
    if dataframe.empty:
        st.info("No papers match the active filters.")
        return

    columns = ["title", "topics", "status", "priority", "rating", "date_added"]
    control_columns = st.columns([0.45, 0.25, 0.2, 0.1])
    sort_column = control_columns[0].selectbox("Sort by", columns, index=5)
    sort_descending = control_columns[1].checkbox("Descending", value=True)
    sorted_dataframe = dataframe.sort_values(
        by=sort_column, ascending=not sort_descending, na_position="last"
    )
    table_event = st.dataframe(
        sorted_dataframe[columns],
        use_container_width=True,
        hide_index=True,
        key="papers_table",
        selection_mode="single-row",
        on_select="rerun",
    )

    selected_rows = table_event.selection.rows
    if selected_rows:
        selected_paper = sorted_dataframe.iloc[selected_rows[0]]
        control_columns[2].caption(f"Selected: {selected_paper['title']}")
        if control_columns[3].button(
            "↗",
            help="Open selected paper in Details",
            use_container_width=True,
        ):
            st.session_state["selected_paper_path"] = selected_paper["path"]
            st.session_state["paper_detail_search"] = selected_paper["title"]
            st.success("Selected paper is ready in the Details tab.")


def render_detail_view(papers: list[PaperNote], dataframe: pd.DataFrame) -> None:
    st.subheader("Paper Detail")
    if dataframe.empty:
        st.info("No papers match the active filters.")
        return

    visible_paths = set(dataframe["path"])
    visible_papers = [paper for paper in papers if str(paper.path) in visible_paths]
    selected_path = choose_detail_paper(visible_papers)
    if selected_path is None:
        st.info("Search for a title to choose a paper.")
        return

    paper = next(item for item in papers if item.path == selected_path)

    st.markdown(f"### {paper.title}")
    metadata_columns = st.columns(3)
    metadata_columns[0].write(f"**Authors:** {', '.join(paper.authors) or 'N/A'}")
    metadata_columns[1].write(f"**Year:** {paper.year or 'N/A'}")
    metadata_columns[2].write(f"**Venue:** {paper.venue or 'N/A'}")
    if paper.url:
        st.markdown(f"[Open URL]({paper.url})")
    st.code(str(paper.path), language=None)

    with st.form(f"paper_metadata_form_{paper.path}"):
        form_columns = st.columns(3)
        status = form_columns[0].selectbox(
            "Status",
            ALLOWED_STATUSES,
            index=ALLOWED_STATUSES.index(paper.status),
        )
        priority = optional_score_select(form_columns[1], "Priority", paper.priority)
        rating = optional_score_select(form_columns[2], "Rating", paper.rating)

        score_columns = st.columns(5)
        importance = optional_score_select(score_columns[0], "Importance", paper.importance)
        taste_match = optional_score_select(
            score_columns[1], "Taste match", paper.taste_match
        )
        research_idea_potential = optional_score_select(
            score_columns[2],
            "Research idea potential",
            paper.research_idea_potential,
        )
        technical_depth = optional_score_select(
            score_columns[3], "Technical depth", paper.technical_depth
        )
        urgency = optional_score_select(score_columns[4], "Urgency", paper.urgency)

        topics = st.text_input("Topics (comma-separated)", value=", ".join(paper.topics))
        related_notes = st.text_input(
            "Related notes (comma-separated)", value=", ".join(paper.related_notes)
        )
        saved = st.form_submit_button("Save Changes")

    if saved:
        update_note_frontmatter(
            paper.path,
            {
                "status": status,
                "priority": priority,
                "rating": rating,
                "importance": importance,
                "taste_match": taste_match,
                "research_idea_potential": research_idea_potential,
                "technical_depth": technical_depth,
                "urgency": urgency,
                "topics": split_topics(topics),
                "related_notes": split_topics(related_notes),
            },
        )
        load_papers.clear()
        st.success("Saved changes to markdown frontmatter.")
        st.rerun()

    with st.expander("Markdown Body", expanded=True):
        st.markdown(paper.body or "_No body content._")


def choose_detail_paper(papers: list[PaperNote]) -> Path | None:
    apply_pending_detail_search()

    selected_path = st.session_state.get("selected_paper_path")
    if selected_path and all(str(paper.path) != selected_path for paper in papers):
        selected_path = None

    search_columns = st.columns([0.85, 0.15])
    query = search_columns[0].text_input(
        "Search papers by title",
        placeholder="Type part of a paper title...",
        key="paper_detail_search",
    ).strip()
    result_limit = int(
        search_columns[1].number_input(
            "Results",
            min_value=1,
            max_value=100,
            value=10,
            step=1,
            help="Number of search results to show before collapsing the rest.",
        )
    )

    if not query:
        return choose_detail_paper_from_dropdown(papers, selected_path)

    candidates = match_papers_by_title(papers, query)
    with st.container(border=True):
        st.caption(
            f"{len(candidates)} matching paper{'s' if len(candidates) != 1 else ''}"
        )
        render_search_candidate_buttons(candidates[:result_limit], selected_path)
        if len(candidates) > result_limit:
            remaining_count = len(candidates) - result_limit
            with st.expander(f"Show {remaining_count} more result{'s' if remaining_count != 1 else ''}"):
                render_search_candidate_buttons(candidates[result_limit:], selected_path)

    if selected_path:
        return Path(selected_path)
    if len(candidates) == 1:
        st.session_state["selected_paper_path"] = str(candidates[0].path)
        return candidates[0].path
    return None


def render_search_candidate_buttons(
    candidates: list[PaperNote], selected_path: str | None
) -> None:
    for candidate in candidates:
        is_selected = str(candidate.path) == selected_path
        label = f"{'✓ ' if is_selected else ''}{candidate.title} — {candidate.path.name}"
        if st.button(label, key=f"select_{candidate.path}", use_container_width=True):
            st.session_state["selected_paper_path"] = str(candidate.path)
            st.rerun()


def apply_pending_detail_search() -> None:
    pending_search = st.session_state.pop("pending_paper_detail_search", None)
    if pending_search is not None:
        st.session_state["paper_detail_search"] = pending_search


def choose_detail_paper_from_dropdown(
    papers: list[PaperNote], selected_path: str | None
) -> Path:
    labels = [f"{paper.title} — {paper.path.name}" for paper in papers]
    paths = [str(paper.path) for paper in papers]
    selected_index = paths.index(selected_path) if selected_path in paths else 0
    selected_label = st.selectbox(
        "Select a paper",
        labels,
        index=selected_index,
        key="paper_detail_dropdown",
    )
    selected_paper = papers[labels.index(selected_label)]
    st.session_state["selected_paper_path"] = str(selected_paper.path)
    return selected_paper.path


def match_papers_by_title(papers: list[PaperNote], query: str) -> list[PaperNote]:
    if not query:
        return sorted(papers, key=lambda paper: paper.title.lower())

    normalized_query = query.lower()
    matches = [
        paper for paper in papers if normalized_query in paper.title.lower()
    ]
    return sorted(matches, key=lambda paper: paper.title.lower())


def render_analytics(dataframe: pd.DataFrame) -> None:
    st.subheader("Analytics")
    if dataframe.empty:
        st.info("No papers match the active filters.")
        return

    chart_columns = st.columns(2)
    chart_columns[0].plotly_chart(papers_by_status(dataframe), use_container_width=True)
    if all_topics(dataframe):
        chart_columns[1].plotly_chart(papers_by_topic(dataframe), use_container_width=True)

    rating_chart = average_rating_by_topic(dataframe)
    added_chart = papers_added_over_time(dataframe)
    chart_columns = st.columns(2)
    if rating_chart is not None:
        chart_columns[0].plotly_chart(rating_chart, use_container_width=True)
    else:
        chart_columns[0].info("No topic ratings available yet.")
    if added_chart is not None:
        chart_columns[1].plotly_chart(added_chart, use_container_width=True)
    else:
        chart_columns[1].info("No valid `date_added` values available yet.")

    list_columns = st.columns(2)
    unread = dataframe[dataframe["status"] != "read"].sort_values(
        by="priority", ascending=False, na_position="last"
    )
    list_columns[0].markdown("#### High Priority Unread")
    list_columns[0].dataframe(
        unread[["title", "status", "priority"]].head(10),
        use_container_width=True,
        hide_index=True,
    )

    recent = dataframe.sort_values(by="date_added", ascending=False, na_position="last")
    list_columns[1].markdown("#### Recently Added")
    list_columns[1].dataframe(
        recent[["title", "date_added", "status"]].head(10),
        use_container_width=True,
        hide_index=True,
    )


def render_research_questions(papers: list[PaperNote]) -> None:
    st.subheader("Research Questions")
    rows = []
    for paper in papers:
        for heading, snippet in extract_research_sections(paper.body).items():
            rows.append(
                {
                    "Paper Title": paper.title,
                    "Section": heading,
                    "Question Snippet": snippet,
                    "Source Note": str(paper.path),
                }
            )

    if not rows:
        st.info("No Open Questions, Possible Research Directions, or Weaknesses sections found.")
        return

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def extract_research_sections(body: str) -> dict[str, str]:
    target_headings = {"open questions", "possible research directions", "weaknesses"}
    sections: dict[str, str] = {}
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in body.splitlines():
        if line.startswith("#"):
            if current_heading:
                sections[current_heading] = compact_snippet(current_lines)
            heading = line.lstrip("#").strip()
            current_heading = heading if heading.lower() in target_headings else None
            current_lines = []
        elif current_heading:
            current_lines.append(line)

    if current_heading:
        sections[current_heading] = compact_snippet(current_lines)

    return {heading: snippet for heading, snippet in sections.items() if snippet}


def compact_snippet(lines: list[str], limit: int = 240) -> str:
    text = " ".join(line.strip() for line in lines if line.strip())
    return text[:limit] + ("…" if len(text) > limit else "")


def optional_score_select(container, label: str, value: int | None) -> int | None:
    options = [""] + SCORE_VALUES
    index = options.index(value) if value in SCORE_VALUES else 0
    selected = container.selectbox(label, options, index=index)
    return int(selected) if selected != "" else None


def all_topics(dataframe: pd.DataFrame) -> set[str]:
    topics: set[str] = set()
    for value in dataframe["topics"].dropna():
        topics.update(split_topics(value))
    return topics


def non_null_values(dataframe: pd.DataFrame, column: str) -> list[str]:
    return [str(value) for value in dataframe[column].dropna().unique() if str(value)]


if __name__ == "__main__":
    main()
