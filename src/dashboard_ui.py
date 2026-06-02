from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.filters import apply_filters, split_topics
from src.paper_model import ALLOWED_STATUSES, SCORE_VALUES, PaperNote
from src.resource_validation import missing_required_resources
from src.update_note import update_note_frontmatter
from src.visualizations import (
    average_rating_by_topic,
    papers_added_over_time,
    papers_by_status,
    papers_by_topic,
)


def render_resource_warnings() -> None:
    missing = missing_required_resources()
    if missing:
        with st.sidebar:
            st.warning(
                "Missing resources: "
                + ", ".join(str(path) for path in missing)
                + ". The dashboard will continue."
            )


def render_sidebar_filters(dataframe: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.header("Filters")
        statuses = st.multiselect("Status", ALLOWED_STATUSES)
        topics = st.multiselect("Topic", sorted(all_topics(dataframe)))
        sources = st.multiselect("Source", sorted(non_null_values(dataframe, "source")))
        priorities = st.multiselect("Priority", SCORE_VALUES)
        ratings = st.multiselect("Rating", SCORE_VALUES)
        min_ranking_score = st.number_input(
            "Minimum ranking score",
            min_value=0,
            value=0,
            step=1,
        )
        recent_only = st.checkbox("Recent papers only")
        recent_days = st.number_input(
            "Recent window days",
            min_value=1,
            value=30,
            step=1,
            disabled=not recent_only,
        )
        triage_decisions = st.multiselect(
            "Triage decision",
            ["read_now", "skim", "read_later", "skip"],
        )
        min_semantic_fit = st.number_input(
            "Minimum semantic fit",
            min_value=0,
            max_value=5,
            value=0,
            step=1,
        )
        min_research_potential = st.number_input(
            "Minimum research potential",
            min_value=0,
            max_value=5,
            value=0,
            step=1,
        )
        min_conceptual_depth = st.number_input(
            "Minimum conceptual depth",
            min_value=0,
            max_value=5,
            value=0,
            step=1,
        )
        matched_interests = st.multiselect(
            "Matched interest",
            sorted(non_null_values(dataframe, "matched_interest")),
        )
        min_semantic_score = st.number_input(
            "Minimum semantic score",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.05,
        )

    return apply_filters(
        dataframe,
        statuses,
        topics,
        sources,
        priorities,
        ratings,
        min_ranking_score=int(min_ranking_score) if min_ranking_score else None,
        recent_only=recent_only,
        recent_days=int(recent_days),
        triage_decisions=triage_decisions,
        min_semantic_fit=int(min_semantic_fit) if min_semantic_fit else None,
        min_research_potential=(
            int(min_research_potential) if min_research_potential else None
        ),
        min_conceptual_depth=int(min_conceptual_depth) if min_conceptual_depth else None,
        matched_interests=matched_interests,
        min_semantic_score=float(min_semantic_score) if min_semantic_score else None,
    )


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

    columns = [
        "title",
        "topics",
        "status",
        "source",
        "priority",
        "rating",
        "ranking_score",
        "final_priority_score",
        "triage_decision",
        "semantic_score",
        "matched_interest",
        "published_date",
        "date_added",
    ]
    visible_columns = [column for column in columns if column in dataframe.columns]
    control_columns = st.columns([0.45, 0.25, 0.2, 0.1])
    sort_column = control_columns[0].selectbox(
        "Sort by", visible_columns, index=visible_columns.index("date_added")
    )
    sort_descending = control_columns[1].checkbox("Descending", value=True)
    sorted_dataframe = dataframe.sort_values(
        by=sort_column, ascending=not sort_descending, na_position="last"
    )
    table_event = st.dataframe(
        sorted_dataframe[visible_columns],
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
            st.session_state["pending_paper_detail_search"] = selected_paper["title"]
            st.success("Selected paper is ready in the Details tab.")


def render_openable_table(
    dataframe: pd.DataFrame,
    columns: list[str],
    key: str,
    empty_message: str,
) -> None:
    if dataframe.empty:
        st.info(empty_message)
        return

    display_columns = [column for column in columns if column in dataframe.columns]
    control_columns = st.columns([0.88, 0.12])
    table_event = st.dataframe(
        dataframe[display_columns],
        use_container_width=True,
        hide_index=True,
        key=key,
        selection_mode="single-row",
        on_select="rerun",
    )
    selected_rows = table_event.selection.rows
    if not selected_rows:
        return

    selected_paper = dataframe.iloc[selected_rows[0]]
    control_columns[0].caption(f"Selected: {selected_paper['title']}")
    if control_columns[1].button(
        "↗",
        help="Open selected paper in Details",
        key=f"{key}_open_details",
        use_container_width=True,
    ):
        st.session_state["selected_paper_path"] = selected_paper["path"]
        st.session_state["pending_paper_detail_search"] = selected_paper["title"]
        st.success("Selected paper is ready in the Details tab.")


def render_detail_view(
    papers: list[PaperNote],
    dataframe: pd.DataFrame,
    on_save,
) -> None:
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
    metadata_columns = st.columns(4)
    metadata_columns[0].write(f"**Authors:** {', '.join(paper.authors) or 'N/A'}")
    metadata_columns[1].write(f"**Year:** {paper.year or 'N/A'}")
    metadata_columns[2].write(f"**Venue:** {paper.venue or 'N/A'}")
    score = paper.ranking_score if paper.ranking_score is not None else "N/A"
    metadata_columns[3].write(f"**Score:** {score}")
    if paper.url:
        st.markdown(f"[Open URL]({paper.url})")
    if paper.pdf_url:
        st.markdown(f"[Open PDF]({paper.pdf_url})")
    if paper.ranking_reason:
        with st.expander("Ranking Reasons"):
            for reason in paper.ranking_reason:
                st.write(f"- {reason}")
    if paper.triage_decision:
        st.write(
            f"**Triage:** {paper.triage_decision} "
            f"(confidence {paper.triage_confidence or 'N/A'})"
        )
    if paper.semantic_score is not None:
        st.write(
            f"**Retrieval:** {paper.matched_interest or 'N/A'} "
            f"(semantic {paper.semantic_score:.3f}, retrieval {paper.retrieval_score or 0:.3f})"
        )
    if paper.retrieval_reason:
        with st.expander("Retrieval Reasons"):
            for reason in paper.retrieval_reason:
                st.write(f"- {reason}")
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
        importance = optional_score_select(
            score_columns[0], "Importance", paper.importance
        )
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
        taste_columns = st.columns(4)
        read_status = taste_columns[0].selectbox(
            "Read status",
            ["", "unread", "reading", "read"],
            index=["", "unread", "reading", "read"].index(paper.read_status or ""),
        )
        user_rating = optional_score_select(
            taste_columns[1], "User rating", paper.user_rating
        )
        starred = taste_columns[2].checkbox("Starred", value=paper.starred)
        clipped = taste_columns[3].checkbox("Clipped", value=paper.clipped)
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
                "read_status": read_status or None,
                "user_rating": user_rating,
                "starred": starred,
                "clipped": clipped,
            },
        )
        on_save()
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
            with st.expander(
                f"Show {remaining_count} more result"
                f"{'s' if remaining_count != 1 else ''}"
            ):
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
    return sorted(
        [paper for paper in papers if normalized_query in paper.title.lower()],
        key=lambda paper: paper.title.lower(),
    )


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


def render_candidate_feed(dataframe: pd.DataFrame) -> None:
    st.subheader("Candidate Feed")
    candidates = dataframe[dataframe["status"] == "candidate"].copy()
    if candidates.empty:
        st.info("No candidate papers found.")
        return
    candidates["decision_order"] = candidates["triage_decision"].map(
        {"read_now": 0, "skim": 1, "read_later": 2, "skip": 3}
    ).fillna(4)
    candidates["source_order"] = candidates["source"].map({"clipping": 0}).fillna(1)
    candidates = candidates.sort_values(
        by=["decision_order", "source_order", "final_priority_score", "ranking_score"],
        ascending=[True, True, False, False],
        na_position="last",
    )
    columns = [
        "title",
        "source",
        "origin",
        "ranking_score",
        "final_priority_score",
        "triage_decision",
        "semantic_fit",
        "research_potential",
        "conceptual_depth",
        "semantic_score",
        "matched_interest",
        "ranking_reason",
        "published_date",
        "date_added",
    ]
    render_openable_table(
        candidates,
        columns,
        key="candidate_feed_table",
        empty_message="No candidate papers found.",
    )


def render_semantic_retrieval_results(dataframe: pd.DataFrame) -> None:
    st.subheader("Semantic Retrieval Results")
    retrieved = dataframe.dropna(subset=["semantic_score"]).copy()
    if retrieved.empty:
        st.info("No semantic retrieval results found yet.")
        return
    retrieved = retrieved.sort_values(
        by="retrieval_score", ascending=False, na_position="last"
    )
    columns = [
        "title",
        "source",
        "semantic_score",
        "retrieval_score",
        "matched_interest",
        "selected_for_triage",
        "retrieval_reason",
        "nearest_positive_papers",
        "retrieval_model",
        "retrieval_date",
    ]
    render_openable_table(
        retrieved,
        columns,
        key="semantic_retrieval_table",
        empty_message="No semantic retrieval results found yet.",
    )


def render_triage_queue(dataframe: pd.DataFrame) -> None:
    st.subheader("Triage Queue")
    queue = dataframe[dataframe["status"] == "candidate"].copy()
    if queue.empty:
        st.info("No candidate papers found.")
        return
    queue["decision_order"] = queue["triage_decision"].map(
        {"read_now": 0, "skim": 1, "read_later": 2, "skip": 3}
    ).fillna(4)
    queue["source_order"] = queue["source"].map({"clipping": 0}).fillna(1)
    queue = queue.sort_values(
        by=["decision_order", "source_order", "final_priority_score", "ranking_score"],
        ascending=[True, True, False, False],
        na_position="last",
    )
    columns = [
        "title",
        "source",
        "triage_decision",
        "final_priority_score",
        "semantic_fit",
        "research_potential",
        "conceptual_depth",
        "triage_confidence",
        "published_date",
    ]
    render_openable_table(
        queue,
        columns,
        key="triage_queue_table",
        empty_message="No candidate papers found.",
    )


def render_high_confidence_reads(dataframe: pd.DataFrame) -> None:
    st.subheader("High Confidence Reads")
    reads = dataframe[
        (dataframe["triage_decision"] == "read_now")
        & (dataframe["triage_confidence"].fillna(0) >= 4)
    ].copy()
    if reads.empty:
        st.info("No high-confidence read-now papers yet.")
        return
    reads = reads.sort_values(
        by="final_priority_score", ascending=False, na_position="last"
    )
    columns = [
        "title",
        "source",
        "final_priority_score",
        "semantic_fit",
        "research_potential",
        "conceptual_depth",
        "triage_confidence",
        "published_date",
    ]
    render_openable_table(
        reads,
        columns,
        key="high_confidence_reads_table",
        empty_message="No high-confidence read-now papers yet.",
    )


def render_daily_queue(vault_dir: Path | None) -> None:
    st.subheader("Daily Queue")
    if vault_dir is None:
        st.info("Provide a vault directory to view daily queues.")
        return
    queue_dir = vault_dir / "Daily Queues"
    if not queue_dir.exists():
        st.info("No Daily Queues directory found yet.")
        return
    queue_files = sorted(queue_dir.glob("*.md"), reverse=True)
    if not queue_files:
        st.info("No daily queue notes found yet.")
        return
    selected = st.selectbox("Queue note", queue_files, format_func=lambda path: path.name)
    st.markdown(selected.read_text(encoding="utf-8"))


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
