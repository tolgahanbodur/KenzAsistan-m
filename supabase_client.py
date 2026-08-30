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
# LOCAL USER
# ============================================================

# Login sistemi kaldırıldığı için artık Supabase Auth
# kullanıcı ID'sine bağlı çalışmıyoruz.
#
# Kenz ilk açıldığında cihaz için kalıcı bir UUID oluşturulur.
# Bu UUID Supabase'deki verilerin sahibini belirler.

def get_user_id():

    if "kenz_user_id" not in st.session_state:

        st.session_state.kenz_user_id = str(
            uuid.uuid4()
        )

    return st.session_state.kenz_user_id


# ============================================================
# USER INFORMATION
# ============================================================

def get_current_user():

    return {
        "id": get_user_id(),
        "email": None,
        "name": "Kullanıcı"
    }


def get_profile():

    return {
        "id": get_user_id(),
        "email": None,
        "name": "Kullanıcı",
        "avatar_url": None
    }


def update_profile(
    name=None,
    avatar_url=None
):

    return {
        "id": get_user_id(),
        "name": name or "Kullanıcı",
        "avatar_url": avatar_url
    }


# ============================================================
# CONVERSATIONS
# ============================================================

def create_conversation(
    title="Yeni sohbet"
):

    supabase = get_supabase()

    user_id = get_user_id()

    data = {
        "user_id": user_id,
        "title": title
    }

    try:

        result = (
            supabase
            .table("conversations")
            .insert(data)
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
            f"Sohbet oluşturulamadı: {e}"
        )


# ============================================================
# GET CONVERSATIONS
# ============================================================

def get_conversations():

    supabase = get_supabase()

    user_id = get_user_id()

    try:

        result = (
            supabase
            .table("conversations")
            .select(
                "id,user_id,title,created_at,updated_at"
            )
            .eq(
                "user_id",
                user_id
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

    user_id = get_user_id()

    try:

        result = (
            supabase
            .table("conversations")
            .select("*")
            .eq(
                "id",
                conversation_id
            )
            .eq(
                "user_id",
                user_id
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

    except Exception:

        return None


# ============================================================
# UPDATE CONVERSATION TITLE
# ============================================================

def update_conversation_title(
    conversation_id,
    title
):

    supabase = get_supabase()

    user_id = get_user_id()

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
            .eq(
                "user_id",
                user_id
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
            f"Sohbet güncellenemedi: {e}"
        )


# ============================================================
# DELETE CONVERSATION
# ============================================================

def delete_conversation(
    conversation_id
):

    supabase = get_supabase()

    user_id = get_user_id()

    try:

        (
            supabase
            .table("conversations")
            .delete()
            .eq(
                "id",
                conversation_id
            )
            .eq(
                "user_id",
                user_id
            )
            .execute()
        )

        return True

    except Exception:

        return False


# ============================================================
# MESSAGES
# ============================================================

def get_messages(
    conversation_id
):

    supabase = get_supabase()

    user_id = get_user_id()

    try:

        result = (
            supabase
            .table("messages")
            .select("*")
            .eq(
                "conversation_id",
                conversation_id
            )
            .eq(
                "user_id",
                user_id
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

    user_id = get_user_id()

    data = {

        "conversation_id":
            conversation_id,

        "user_id":
            user_id,

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

        # ----------------------------------------------------
        # SOHBET ZAMANINI GÜNCELLE
        # ----------------------------------------------------

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
            .eq(
                "user_id",
                user_id
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

    user_id = get_user_id()

    # Her kullanıcı için ayrı klasör
    storage_path = (
        str(user_id)
        + "/"
        + file_name
    )

    try:

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

    user_id = get_user_id()

    data = {

        "user_id":
            user_id,

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
            f"Kıyafet kaydedilemedi: {e}"
        )


# ============================================================
# GET WARDROBE
# ============================================================

def get_all_clothes():

    supabase = get_supabase()

    user_id = get_user_id()

    try:

        result = (
            supabase
            .table("clothes")
            .select("*")
            .eq(
                "user_id",
                user_id
            )
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

    user_id = get_user_id()

    try:

        (
            supabase
            .table("clothes")
            .delete()
            .eq(
                "id",
                clothing_id
            )
            .eq(
                "user_id",
                user_id
            )
            .execute()
        )

        return True

    except Exception:

        return False


# ============================================================
# USER MEMORY
# ============================================================

def get_preferences():

    supabase = get_supabase()

    user_id = get_user_id()

    try:

        result = (
            supabase
            .table("user_preferences")
            .select("*")
            .eq(
                "user_id",
                user_id
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

    except Exception:

        return None


# ============================================================
# SAVE MEMORY
# ============================================================

def save_preferences(
    preferences
):

    supabase = get_supabase()

    user_id = get_user_id()

    now = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    existing = get_preferences()

    try:

        if existing:

            result = (
                supabase
                .table(
                    "user_preferences"
                )
                .update(
                    {
                        "preferences":
                            preferences,

                        "updated_at":
                            now
                    }
                )
                .eq(
                    "user_id",
                    user_id
                )
                .execute()
            )

        else:

            result = (
                supabase
                .table(
                    "user_preferences"
                )
                .insert(
                    {
                        "user_id":
                            user_id,

                        "preferences":
                            preferences,

                        "updated_at":
                            now
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

    except Exception as e:

        raise RuntimeError(
            f"Hafıza kaydedilemedi: {e}"
        )


# ============================================================
# AUTOMATIC MEMORY
# ============================================================

def append_memory(
    memory_text
):

    if not memory_text:
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

    memory_text = str(
        memory_text
    ).strip()

    if not memory_text:
        return False

    # Aynı bilgiyi tekrar tekrar ekleme
    if memory_text.lower() in current.lower():

        return True

    if current.strip():

        new_memory = (
            current.rstrip()
            + "\n"
            + memory_text
        )

    else:

        new_memory = memory_text

    save_preferences(
        new_memory
    )

    return True


# ============================================================
# GET ALL MEMORY
# ============================================================

def get_memory():

    preferences = get_preferences()

    if not preferences:

        return ""

    return (
        preferences.get(
            "preferences"
        )
        or ""
    )


# ============================================================
# CLEAR MEMORY
# ============================================================

def clear_memory():

    supabase = get_supabase()

    user_id = get_user_id()

    try:

        (
            supabase
            .table(
                "user_preferences"
            )
            .delete()
            .eq(
                "user_id",
                user_id
            )
            .execute()
        )

        return True

    except Exception:

        return False
