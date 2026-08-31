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
        )

        rows = (
            getattr(
                result,
                "data",
                []
            )
            or []
        )

        if not rows:
            raise RuntimeError(
                "Sohbet oluşturulamadı."
            )

        return rows[0]

    except Exception as e:

        raise RuntimeError(
            f"Sohbet oluşturulamadı: {e}"
        )


# ============================================================
# GET CONVERSATIONS
# ============================================================

def get_conversations(
    user_session_id=None
):

    supabase = get_supabase()

    try:

        query = (
            supabase
            .table("conversations")
            .select(
                "id,title,created_at,updated_at"
            )
        )

        if user_session_id:
            query = query.eq(
                "user_session_id",
                user_session_id
            )

        result = (
            query
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

    except Exception as e:

        raise RuntimeError(
            f"Sohbetler alınamadı: {e}"
        )


# ============================================================
# GET SINGLE CONVERSATION
# ============================================================

def get_conversation(
    conversation_id
):

    supabase = get_supabase()

    try:

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

    except Exception as e:

        raise RuntimeError(
            f"Sohbet alınamadı: {e}"
        )


# ============================================================
# UPDATE CONVERSATION TITLE
# ============================================================

def update_conversation_title(
    conversation_id,
    title
):

    supabase = get_supabase()

    try:

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

    except Exception as e:

        raise RuntimeError(
            f"Sohbet başlığı güncellenemedi: {e}"
        )


# ============================================================
# DELETE CONVERSATION
# ============================================================

def delete_conversation(
    conversation_id
):

    supabase = get_supabase()

    try:

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

    except Exception as e:

        raise RuntimeError(
            f"Sohbet silinemedi: {e}"
        )


# ============================================================
# MESSAGES
# ============================================================

def get_messages(
    conversation_id
):

    supabase = get_supabase()

    try:

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

    except Exception as e:

        raise RuntimeError(
            f"Mesajlar alınamadı: {e}"
        )


# ============================================================
# ADD MESSAGE
# ============================================================

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

    try:

        result = (
            supabase
            .table("messages")
            .insert(data)
            .execute()
        )

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

    except Exception as e:

        raise RuntimeError(
            f"Mesaj kaydedilemedi: {e}"
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

    try:

        storage_path = file_name

        supabase.storage.from_(
            bucket_name
        ).upload(
            storage_path,
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
                storage_path
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
# IMAGE UPLOAD
# ============================================================

def upload_image(
    file_bytes,
    file_name,
    bucket_name="chat_files"
):

    return upload_file(
        file_bytes,
        file_name,
        "image/jpeg",
        bucket_name
    )


# ============================================================
# GARDIROP
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

    try:

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

    except Exception as e:

        raise RuntimeError(
            f"Kıyafet eklenemedi: {e}"
        )


# ============================================================
# GET WARDROBE
# ============================================================

def get_all_clothes():

    supabase = get_supabase()

    try:

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

    except Exception as e:

        raise RuntimeError(
            f"Gardırop alınamadı: {e}"
        )


# ============================================================
# DELETE CLOTHING
# ============================================================

def delete_clothing_item(
    clothing_id
):

    supabase = get_supabase()

    try:

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

    except Exception as e:

        raise RuntimeError(
            f"Kıyafet silinemedi: {e}"
        )


# ============================================================
# USER MEMORY
# ============================================================

def get_preferences():

    supabase = get_supabase()

    try:

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

    except Exception as e:

        raise RuntimeError(
            f"Hafıza alınamadı: {e}"
        )


# ============================================================
# SAVE MEMORY
# ============================================================

def save_preferences(
    preferences
):

    supabase = get_supabase()

    try:

        existing = get_preferences()

        data = {

            "preferences":
                preferences,

            "updated_at":
                datetime.now(
                    timezone.utc
                ).isoformat()
        }

        if existing:

            result = (
                supabase
                .table("user_preferences")
                .update(data)
                .eq(
                    "id",
                    existing["id"]
                )
                .execute()
            )

        else:

            result = (
                supabase
                .table("user_preferences")
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

    except Exception as e:

        raise RuntimeError(
            f"Hafıza kaydedilemedi: {e}"
        )
