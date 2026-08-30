import os
import uuid
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
# CLIENT ID
# ============================================================

def get_client_id():

    if "client_id" not in st.session_state:

        st.session_state.client_id = str(
            uuid.uuid4()
        )

    return st.session_state.client_id


# ============================================================
# CONVERSATIONS
# ============================================================

def create_conversation(
    client_id=None,
    title="Yeni sohbet"
):

    supabase = get_supabase()

    if client_id is None:
        client_id = get_client_id()

    data = {
        "client_id": str(client_id),
        "title": title,
    }

    result = (
        supabase
        .table("conversations")
        .insert(data)
        .execute()
    )

    rows = getattr(
        result,
        "data",
        None
    )

    if not rows:
        return None

    return rows[0]


def get_conversations(
    client_id=None
):

    supabase = get_supabase()

    if client_id is None:
        client_id = get_client_id()

    result = (
        supabase
        .table("conversations")
        .select(
            "id,client_id,title,created_at,updated_at"
        )
        .eq(
            "client_id",
            str(client_id)
        )
        .order(
            "updated_at",
            desc=True
        )
        .execute()
    )

    return getattr(
        result,
        "data",
        []
    ) or []


def get_conversation(
    conversation_id,
    client_id=None
):

    supabase = get_supabase()

    if client_id is None:
        client_id = get_client_id()

    result = (
        supabase
        .table("conversations")
        .select("*")
        .eq(
            "id",
            conversation_id
        )
        .eq(
            "client_id",
            str(client_id)
        )
        .limit(1)
        .execute()
    )

    rows = getattr(
        result,
        "data",
        []
    ) or []

    if rows:
        return rows[0]

    return None


# ============================================================
# UPDATE CONVERSATION TITLE
# ============================================================

def update_conversation_title(
    conversation_id,
    client_id,
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
        .eq(
            "client_id",
            str(client_id)
        )
        .execute()
    )

    return getattr(
        result,
        "data",
        []
    ) or []


# ============================================================
# DELETE CONVERSATION
# ============================================================

def delete_conversation(
    conversation_id,
    client_id=None
):

    supabase = get_supabase()

    if client_id is None:
        client_id = get_client_id()

    (
        supabase
        .table("conversations")
        .delete()
        .eq(
            "id",
            conversation_id
        )
        .eq(
            "client_id",
            str(client_id)
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

    return getattr(
        result,
        "data",
        []
    ) or []


def add_message(
    conversation_id,
    role,
    content,
    image_url=None,
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

        "image_url":
            image_url,

        "provider":
            provider,
    }

    result = (
        supabase
        .table("messages")
        .insert(data)
        .execute()
    )


    # Sohbetin son kullanım zamanını güncelle
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


    return getattr(
        result,
        "data",
        []
    ) or []


# ============================================================
# STORAGE
# ============================================================

def upload_image(
    file_bytes,
    file_name,
    bucket_name="chat_images"
):

    supabase = get_supabase()

    try:

        supabase.storage.from_(
            bucket_name
        ).upload(
            file_name,
            file_bytes,
            {
                "content-type":
                    "image/jpeg",

                "upsert":
                    "true"
            }
        )

        return (
            supabase
            .storage
            .from_(bucket_name)
            .get_public_url(
                file_name
            )
        )

    except Exception as e:

        print(
            "IMAGE UPLOAD ERROR:",
            repr(e)
        )

        return None


# ============================================================
# GARDIROP
# ============================================================

def add_clothing_item(
    image_url,
    category,
    color,
    description
):

    supabase = get_supabase()

    result = (
        supabase
        .table("clothes")
        .insert(
            {
                "image_url":
                    image_url,

                "category":
                    category,

                "color":
                    color,

                "description":
                    description,
            }
        )
        .execute()
    )

    return getattr(
        result,
        "data",
        []
    ) or []


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

    return getattr(
        result,
        "data",
        []
    ) or []
