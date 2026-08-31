import os
from datetime import datetime, timezone

import streamlit as st
from supabase import create_client, Client


# ============================================================
# SUPABASE CONNECTION
# ============================================================

@st.cache_resource
def get_supabase() -> Client:

    url = st.secrets.get(
        "SUPABASE_URL",
        os.environ.get("SUPABASE_URL", "")
    )

    key = st.secrets.get(
        "SUPABASE_KEY",
        os.environ.get("SUPABASE_KEY", "")
    )

    if not url:
        raise RuntimeError(
            "SUPABASE_URL bulunamadı."
        )

    if not key:
        raise RuntimeError(
            "SUPABASE_KEY bulunamadı."
        )

    return create_client(
        url,
        key
    )


# ============================================================
# CONVERSATIONS
# ============================================================

def create_conversation(
    title="Yeni sohbet",
    user_session_id=None
):

    supabase = get_supabase()

    try:

        result = (
            supabase
            .table("conversations")
            .insert(
                {
                    "title": title,
                    "user_session_id": user_session_id
                }
            )
            .execute()
