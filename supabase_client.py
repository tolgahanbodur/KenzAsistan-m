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
    title="Yeni sohbet"
):

    supabase = get_supabase()

    result = (
        supabase
        .table("conversations")
        .insert(
            {
                "title": title
            }
        )
        .execute()
    )

    rows = (
        getattr(
            result,
            "data",
            []
        )
        or []
    )

    return (
        rows[0]
        if rows
        else None
    )


def get_conversations():

    supabase = get_supabase()

    result = (
        supabase
        .table("conversations")
        .select(
            "id,title,created_at,updated_at"
        )
        .order(
            "updated_at",
            desc=True
        )
        .execute()
    )

    return (
        getattr(
            result,
            "data",
            []
        )
        or []
    )


def get_conversation(
    conversation_id
):

    supabase = get_supabase()

    result = (
        supabase
        .table("conversations")
        .select("*")
        .eq(
            "id",
            conversation_id
        )
        .limit(1)
        .execute()
    )

    rows = (
        getattr(
            result,
            "data",
            []
        )
        or []
    )

    return (
        rows[0]
        if rows
        else None
    )


def update_conversation_title(
    conversation_id,
    title
):

    supabase = get_supabase()

    result = (
        supabase
        .table("conversations")
        .update(
            {
                "title": title,
                "updated_at":
                    datetime.now(
                        timezone.utc
                    ).isoformat()
            }
        )
        .eq(
            "id",
            conversation_id
        )
        .execute()
    )

    return (
        getattr(
            result,
            "data",
            []
        )
        or []
    )


def delete_conversation(
    conversation_id
):

    supabase = get_supabase()

    (
        supabase
        .table("conversations")
        .delete()
        .eq(
            "id",
            conversation_id
        )
        .execute()
    )

    return True


# ============================================================
# MESSAGES
# ============================================================

def get_messages(
    conversation_id
):

    supabase = get_supabase()

    result = (
        supabase
        .table("messages")
        .select("*")
        .eq(
            "conversation_id",
            conversation_id
        )
        .order(
            "created_at",
            desc=False
        )
        .execute()
    )

    return (
        getattr(
            result,
            "data",
            []
        )
        or []
    )


def add_message(
    conversation_id,
    role,
    content=None,
    file_url=None,
    file_name=None,
    file_type=None,
    provider=None
):

    supabase = get_supabase()

    data = {

        "conversation_id":
            conversation_id,

        "role":
            role,

        "content":
            content,

        "file_url":
            file_url,

        "file_name":
            file_name,

        "file_type":
            file_type,

        "provider":
            provider,
    }

    result = (
        supabase
        .table("messages")
        .insert(data)
        .execute()
    )

    # --------------------------------------------------------
    # SOHBET GÜNCELLEME ZAMANI
    # --------------------------------------------------------

    (
        supabase
        .table("conversations")
        .update(
            {
                "updated_at":
                    datetime.now(
                        timezone.utc
                    ).isoformat()
            }
        )
        .eq(
            "id",
            conversation_id
        )
        .execute()
    )

    return (
        getattr(
            result,
            "data",
            []
        )
        or []
    )


# ============================================================
# STORAGE
# ============================================================

def upload_file(
    file_bytes,
    file_name,
    content_type,
    bucket_name="chat_files"
):

    supabase = get_supabase()

    if not file_bytes:
        return None

    try:

        supabase.storage.from_(
            bucket_name
        ).upload(
            file_name,
            file_bytes,
            {
                "content-type":
                    content_type,

                "upsert":
                    "true"
            }
        )

        public_url = (
            supabase
            .storage
            .from_(
                bucket_name
            )
            .get_public_url(
                file_name
            )
        )

        return public_url

    except Exception as e:

        print(
            "STORAGE ERROR:",
            repr(e)
        )

        return None


# ============================================================
# WARDROBE
# ============================================================

def add_clothing_item(
    image_url,
    category=None,
    name=None,
    color=None,
    style=None,
    season=None,
    description=None
):

    supabase = get_supabase()

    data = {

        "image_url":
            image_url,

        "category":
            category,

        "name":
            name,

        "color":
            color,

        "style":
            style,

        "season":
            season,

        "description":
            description,
    }

    result = (
        supabase
        .table("clothes")
        .insert(data)
        .execute()
    )

    return (
        getattr(
            result,
            "data",
            []
        )
        or []
    )


def get_all_clothes():

    supabase = get_supabase()

    result = (
        supabase
        .table("clothes")
        .select("*")
        .order(
            "added_date",
            desc=True
        )
        .execute()
    )

    return (
        getattr(
            result,
            "data",
            []
        )
        or []
    )


def delete_clothing_item(
    clothing_id
):

    supabase = get_supabase()

    (
        supabase
        .table("clothes")
        .delete()
        .eq(
            "id",
            clothing_id
        )
        .execute()
    )

    return True


# ============================================================
# MEMORY
# ============================================================

def get_preferences():

    supabase = get_supabase()

    result = (
        supabase
        .table("user_preferences")
        .select("*")
        .limit(1)
        .execute()
    )

    rows = (
        getattr(
            result,
            "data",
            []
        )
        or []
    )

    return (
        rows[0]
        if rows
        else None
    )


def save_preferences(
    preferences
):

    supabase = get_supabase()

    existing = get_preferences()

    updated_at = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    # --------------------------------------------------------
    # VARSA GÜNCELLE
    # --------------------------------------------------------

    if existing:

        result = (
            supabase
            .table("user_preferences")
            .update(
                {
                    "preferences":
                        preferences,

                    "updated_at":
                        updated_at
                }
            )
            .eq(
                "id",
                existing["id"]
            )
            .execute()
        )

    # --------------------------------------------------------
    # YOKSA OLUŞTUR
    # --------------------------------------------------------

    else:

        result = (
            supabase
            .table("user_preferences")
            .insert(
                {
                    "preferences":
                        preferences,

                    "updated_at":
                        updated_at
                }
            )
            .execute()
        )

    return (
        getattr(
            result,
            "data",
            []
        )
        or []
    )


# ============================================================
# AUTOMATIC MEMORY UPDATE
# ============================================================

def append_memory(
    new_memory
):

    if not new_memory:
        return False

    new_memory = str(
        new_memory
    ).strip()

    if not new_memory:
        return False

    existing = get_preferences()

    current = ""

    if existing:

        current = (
            existing.get(
                "preferences"
            )
            or ""
        )

    # Aynı bilgi zaten varsa tekrar ekleme
    if new_memory.lower() in current.lower():

        return True

    if current.strip():

        combined = (
            current.strip()
            + "\n"
            + new_memory
        )

    else:

        combined = new_memory

    save_preferences(
        combined
    )

    return True
