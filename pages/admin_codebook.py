"""Admin page: Manage codebook questions (add/edit/remove)."""

import logging
import streamlit as st
import pandas as pd

from core.codebook_admin import (
    load_codebook, save_codebook, get_sections,
    get_items_by_section, add_item, remove_item, update_item,
)
from core.ui_theme import page_header, section_header

logger = logging.getLogger("sehra.admin_codebook")

page_header("Manage Questions", "Add, edit, or remove questions in the SEHRA codebook.")

# Section selector
sections = get_sections()
SECTION_LABELS = {
    "context": "Context (O-series)",
    "policy": "Policy & Strategy (S-series)",
    "service_delivery": "Service Delivery (I-series)",
    "human_resources": "Human Resources (H-series)",
    "supply_chain": "Supply Chain (C-series)",
    "barriers": "Barriers (B-series)",
    "summary": "Summary (M-series)",
}

selected_section = st.selectbox(
    "Section",
    options=sections,
    format_func=lambda s: SECTION_LABELS.get(s, s),
)

items = get_items_by_section(selected_section)

st.caption(f"{len(items)} items in this section")

# Display items as editable dataframe
if items:
    df = pd.DataFrame(items)
    display_cols = ["id", "question", "type", "has_scoring", "is_reverse"]
    df_display = df[display_cols].copy()
    df_display.columns = ["ID", "Question", "Type", "Scored", "Reverse"]

    edited_df = st.data_editor(
        df_display,
        use_container_width=True,
        hide_index=True,
        disabled=["ID"],
        column_config={
            "Type": st.column_config.SelectboxColumn(
                options=["numeric", "text", "categorical", "categorical_text"],
            ),
            "Scored": st.column_config.CheckboxColumn(),
            "Reverse": st.column_config.CheckboxColumn(),
        },
        num_rows="fixed",
    )

    # Detect changes and save
    if st.button("Save Changes", type="primary"):
        changed = False
        for idx, row in edited_df.iterrows():
            original = items[idx]
            if (row["Question"] != original["question"] or
                row["Type"] != original["type"] or
                row["Scored"] != original["has_scoring"] or
                row["Reverse"] != original["is_reverse"]):
                update_item(
                    original["id"],
                    question=row["Question"],
                    type=row["Type"],
                    has_scoring=bool(row["Scored"]),
                    is_reverse=bool(row["Reverse"]),
                )
                changed = True
        if changed:
            st.success("Changes saved to codebook.json")
            st.rerun()
        else:
            st.info("No changes detected.")

st.divider()

# Add new question
section_header("Add New Question")

with st.form("add_question"):
    col1, col2 = st.columns([3, 1])
    with col1:
        new_question = st.text_area("Question text", height=80)
    with col2:
        new_type = st.selectbox(
            "Type",
            options=["categorical_text", "numeric", "text", "categorical"],
        )
        new_scored = st.checkbox("Has scoring", value=True)
        new_reverse = st.checkbox("Reverse scored")

    new_id = st.text_input("Custom ID (leave blank for auto)", value="")

    if st.form_submit_button("Add Question", type="primary"):
        if not new_question.strip():
            st.error("Question text is required.")
        else:
            new_item = add_item(
                section=selected_section,
                question=new_question.strip(),
                item_type=new_type,
                has_scoring=new_scored,
                is_reverse=new_reverse,
                item_id=new_id.strip(),
            )
            st.success(f"Added item **{new_item['id']}**: {new_item['question'][:60]}...")
            st.rerun()

st.divider()

# Delete question
section_header("Delete Question")
if items:
    delete_options = {f"{item['id']}: {item['question'][:60]}": item["id"] for item in items}
    delete_label = st.selectbox("Select question to delete", options=list(delete_options.keys()))
    delete_id = delete_options[delete_label]

    if st.button("Delete Selected", type="secondary"):
        if remove_item(delete_id):
            st.success(f"Deleted item {delete_id}")
            st.rerun()
        else:
            st.error("Item not found.")
else:
    st.info("No items in this section.")
