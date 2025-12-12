"""
Streamlit CRUD app using SQLite3.

Run: streamlit run studentsApp/app.py

This single-file app creates/connects to an SQLite database (data.db),
creates the table if missing, and provides Create/Read/Update/Delete
operations via a clean Streamlit UI.
"""

import streamlit as st
import sqlite3
import pandas as pd
import os
from typing import List, Tuple, Optional


# Database file path (placed next to this app file)
DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")


def safe_rerun() -> None:
    """Safely rerun the Streamlit script.

    Uses `st.experimental_rerun()` when available; otherwise toggles
    a session-state flag to force Streamlit to rerun the script.
    This avoids errors on Streamlit versions where `experimental_rerun`
    may not be present or accessible.
    """
    try:
        # Preferred method when available
        st.experimental_rerun()
    except Exception:
        # Fallback: toggling session state causes a rerun
        key = "_rerun_toggle"
        st.session_state[key] = not st.session_state.get(key, False)


def get_conn():
    """Return a sqlite3 connection to the database file."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn


def create_table() -> None:
    """Create the entries table if it doesn't exist."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def insert_entry(name: str, age: Optional[int], email: str) -> int:
    """Insert a new entry and return the new row id."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO entries (name, age, email) VALUES (?, ?, ?)",
            (name, age, email),
        )
        conn.commit()
        return cur.lastrowid


def view_all() -> pd.DataFrame:
    """Return all records as a pandas DataFrame."""
    with get_conn() as conn:
        df = pd.read_sql_query("SELECT * FROM entries ORDER BY id DESC", conn)
    return df


def get_entry_by_id(entry_id: int) -> Optional[Tuple]:
    """Return a single entry tuple or None if not found."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        row = cur.fetchone()
    return row


def update_entry(entry_id: int, name: str, age: Optional[int], email: str) -> None:
    """Update an existing entry."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE entries SET name = ?, age = ?, email = ? WHERE id = ?",
            (name, age, email, entry_id),
        )
        conn.commit()


def delete_entry(entry_id: int) -> None:
    """Delete an entry by id."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        conn.commit()


def main():
    st.set_page_config(page_title="Streamlit SQLite CRUD", layout="centered")
    st.title("Welcome to My App")

    # Ensure table exists on startup
    create_table()

    # --- Create: Add new record ---
    st.header("Add New Entry")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=0, max_value=150, step=1, value=0)
        email = st.text_input("Email")
        submitted = st.form_submit_button("Add")
        if submitted:
            if not name.strip():
                st.error("Name is required.")
            else:
                new_id = insert_entry(name.strip(), int(age) if age else None, email.strip())
                st.success(f"Added entry (id={new_id}).")

    st.markdown("---")

    # --- Read: Show all records ---
    st.header("All Records")
    df = view_all()
    if df.empty:
        st.info("No records found. Add one above.")
    else:
        # Show dataframe
        st.dataframe(df)

    st.markdown("---")

    # Helper: build options mapping for select widgets
    def build_options(dataframe: pd.DataFrame) -> List[tuple]:
        """Return list of (display_text, id) tuples for select widgets."""
        opts = []
        for _, row in dataframe.iterrows():
            opts.append((f"{int(row['id'])} — {row['name']}", int(row['id'])))
        return opts

    if not df.empty:
        options = build_options(df)

        # --- Update: select and edit a record ---
        st.header("Update Record")
        option_display = [o[0] for o in options]
        selected = st.selectbox("Pick a record to edit", option_display)
        selected_id = next((o[1] for o in options if o[0] == selected), None)

        if selected_id is not None:
            row = get_entry_by_id(selected_id)
            if row:
                # row structure: (id, name, age, email, created_at)
                with st.form("update_form"):
                    u_name = st.text_input("Name", value=row[1])
                    u_age = st.number_input(
                        "Age", min_value=0, max_value=150, step=1, value=int(row[2]) if row[2] is not None else 0
                    )
                    u_email = st.text_input("Email", value=row[3] or "")
                    updated = st.form_submit_button("Save changes")
                    if updated:
                        if not u_name.strip():
                            st.error("Name cannot be empty")
                        else:
                            update_entry(selected_id, u_name.strip(), int(u_age) if u_age else None, u_email.strip())
                            st.success("Record updated.")
                            safe_rerun()

        st.markdown("---")

        # --- Delete: choose and delete a record ---
        st.header("Delete Record")
        del_option = st.selectbox("Pick a record to delete", option_display, key="del_select")
        del_id = next((o[1] for o in options if o[0] == del_option), None)
        with st.form("delete_form"):
            confirm = st.checkbox("I confirm deletion of the selected record")
            do_delete = st.form_submit_button("Delete")
            if do_delete:
                if not confirm:
                    st.error("Please confirm deletion by checking the box.")
                else:
                    delete_entry(del_id)
                    st.success("Record deleted.")
                    safe_rerun()


if __name__ == "__main__":
    main()

