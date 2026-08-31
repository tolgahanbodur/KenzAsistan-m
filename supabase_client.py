import base64
import os
from datetime import datetime

import streamlit as st
from supabase import (
    create_client,
    Client,
)


# ============================================================
# CONFIG
# ============================================================

def get_secret(
    name,
):

    value = os.environ.get(
        name
    )

    if value:
        return value

    try:
        return st.secrets[
            name
        ]
    except Exception:
        return None


# ============================================================
# CREATE CLIENT
# ============================================================

def create_supabase() -> Client:

    url = get_secret(
        "SUPABASE_URL"
    )

    key = get_secret(
        "SUPABASE_KEY"
    )

    if not url:
        raise ValueError(
            "SUPABASE_URL bulunamadı."
        )

    if not key:
        raise ValueError(
            "SUPABASE_KEY bulunamadı."
        )

    return create_client(
        url,
        key,
    )


# ============================================================
# USER / ANONYMOUS SESSION
# ============================================================

def get_user_client():

    if (
        "supabase_access_token"
        not in st.session_state
    ):

        st.session_state.supabase_access_token = None

    if (
        "supabase_refresh_token"
        not in st.session_state
    ):

        st.session_state.supabase_refresh_token = None

    supabase = create_supabase()


    # --------------------------------------------------------
    # RESTORE SESSION
    # --------------------------------------------------------

    access_token = (
        st.session_state.supabase_access_token
    )

    refresh_token = (
        st.session_state.supabase_refresh_token
    )

    if (
        access_token
        and refresh_token
    ):

        try:

            supabase.auth.set_session(
                access_token,
                refresh_token,
            )

            response = (
                supabase.auth.get_user()
            )

            if response.user:

                return (
                    supabase,
                    str(
                        response.user.id
                    ),
                )

        except Exception:

            st.session_state.supabase_access_token = None
            st.session_state.supabase_refresh_token = None


    # --------------------------------------------------------
    # NEW ANONYMOUS USER
    # --------------------------------------------------------

    try:

        response = (
            supabase.auth.sign_in_anonymously()
        )

    except Exception as e:

        raise RuntimeError(
            "Supabase anonymous sign-in "
            "başarısız. Supabase Dashboard → "
            "Authentication → Sign In / Providers "
            "bölümünden Anonymous Sign-Ins'i aç.\n\n"
            + str(e)
        )


    session = response.session
    user = response.user

    if not session or not user:

        raise RuntimeError(
            "Supabase anonymous kullanıcı "
            "oluşturulamadı."
        )


    st.session_state.supabase_access_token = (
        session.access_token
    )

    st.session_state.supabase_refresh_token = (
        session.refresh_token
    )

    user_id = str(
        user.id
    )


    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

    try:

        supabase.table(
            "profiles"
        ).upsert(
            {
                "id": user_id,
                "display_name": "Kenz Kullanıcısı",
            },
            on_conflict="id",
        ).execute()

    except Exception:
        pass


    return (
        supabase,
        user_id,
    )


# ============================================================
# MESSAGES
# ============================================================

def save_message(
    supabase,
    user_id,
    role,
    content,
    file_name=None,
    file_bytes=None,
):

    encoded_file = None

    if file_bytes:

        encoded_file = base64.b64encode(
            file_bytes
        ).decode("utf-8")


    data = {

        "user_id": user_id,

        "role": role,

        "content": content or "",

        "file_name": file_name,

        "file_data": encoded_file,

    }

    supabase.table(
        "messages"
    ).insert(
        data
    ).execute()


def get_messages(
    supabase,
    user_id,
    limit=100,
):

    response = (
        supabase.table(
            "messages"
        )
        .select(
            "*"
        )
        .eq(
            "user_id",
            user_id,
        )
        .order(
            "created_at",
            desc=False,
        )
        .limit(
            limit
        )
        .execute()
    )

    return response.data or []


# ============================================================
# MEMORY
# ============================================================

def get_memories(
    supabase,
    user_id,
):

    response = (
        supabase.table(
            "memories"
        )
        .select(
            "*"
        )
        .eq(
            "user_id",
            user_id,
        )
        .order(
            "created_at",
            desc=True,
        )
        .execute()
    )

    return response.data or []


def save_memory(
    supabase,
    user_id,
    memory,
):

    if not memory:
        return

    supabase.table(
        "memories"
    ).insert(
        {
            "user_id": user_id,
            "memory": memory,
        }
    ).execute()


def delete_memory(
    supabase,
    user_id,
    memory_id,
):

    supabase.table(
        "memories"
    ).delete().eq(
        "id",
        memory_id,
    ).eq(
        "user_id",
        user_id,
    ).execute()


# ============================================================
# WARDROBE
# ============================================================

def get_wardrobe(
    supabase,
    user_id,
):

    response = (
        supabase.table(
            "wardrobe"
        )
        .select(
            "*"
        )
        .eq(
            "user_id",
            user_id,
        )
        .order(
            "created_at",
            desc=True,
        )
        .execute()
    )

    return response.data or []


def add_wardrobe_item(
    supabase,
    user_id,
    item,
):

    if not item:
        return

    supabase.table(
        "wardrobe"
    ).insert(
        {
            "user_id": user_id,
            "name": item.get(
                "name",
                "Kıyafet",
            ),
            "category": item.get(
                "category",
                "diğer",
            ),
            "color": item.get(
                "color",
                "belirsiz",
            ),
            "description": item.get(
                "description",
                "",
            ),
            "metadata": item,
        }
    ).execute()
