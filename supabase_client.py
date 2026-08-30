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
# ANONYMOUS USER ID
# ============================================================

def get_user_id():

    if "kenz_user_id" not in st.session_state:

        st.session_state.kenz_user_id = str(
            uuid.uuid4()
        )

    return st.session_state.kenz_user_id


# ============================================================
# CURRENT USER
# ============================================================

def get_current_user():

    return {
        "id": get_user_id()
    }


# ============================================================
# SESSION
# ============================================================

def get_session():

    return {
        "user_id": get_user_id()
    }


# ============================================================
# PROFILE
# ============================================================

def get_profile():

    supabase = get_supabase()
    user_id = get_user_id()

    try:

        result = (
            supabase
            .table("profiles")
            .select("*")
            .eq(
                "id",
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

        if rows:
            return rows[0]

        # Profil yoksa otomatik oluştur
        data = {
            "id": user_id,
            "name": "Kullanıcı",
            "avatar_url": None,
        }

        result = (
            supabase
            .table("profiles")
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
            else data
        )

    except Exception:
        return {
            "id": user_id,
            "name": "Kullanıcı",
            "avatar_url": None,
        }


# ============================================================
# UPDATE PROFILE
# ============================================================

def update_profile(
    name=None,
    avatar_url=None
):

    supabase = get_supabase()
    user_id = get_user_id()

    data = {
        "updated_at":
            datetime.now(
                timezone.utc
            ).isoformat()
    }

    if name is not None:
        data["name"] = name

    if avatar_url is not None:
        data["avatar_url"] = avatar_url

    result = (
        supabase
        .table("profiles")
        .update(data)
        .eq(
            "id",
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


# ============================================================
# CONVERSATIONS
# ============================================================

def create_conversation(
    title="Yeni sohbet"
):

    supabase = get_supabase()
    user_id = get_user_id()

    result = (
        supabase
        .table("conversations")
        .insert(
            {
                "user_id": user_id,
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


# ============================================================
# GET CONVERSATIONS
# ============================================================

def get_conversations():

    supabase = get_supabase()
    user_id = get_user_id()

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


# ============================================================
# GET SINGLE CONVERSATION
# ============================================================

def get_conversation(
    conversation_id
):

    supabase = get_supabase()
    user_id = get_user_id()

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


# ============================================================
# UPDATE CONVERSATION TITLE
# ============================================================

def update_conversation_title(
    conversation_id,
    title
):

    supabase = get_supabase()
    user_id = get_user_id()

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


# ============================================================
# DELETE CONVERSATION
# ============================================================

def delete_conversation(
    conversation_id
):

    supabase = get_supabase()
    user_id = get_user_id()

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


# ============================================================
# MESSAGES
# ============================================================

def get_messages(
    conversation_id
):

    supabase = get_supabase()
    user_id = get_user_id()

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

    # Kullanıcıya özel klasör
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


# ============================================================
# GET WARDROBE
# ============================================================

def get_all_clothes():

    supabase = get_supabase()
    user_id = get_user_id()

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


# ============================================================
# DELETE CLOTHING
# ============================================================

def delete_clothing_item(
    clothing_id
):

    supabase = get_supabase()
    user_id = get_user_id()

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


# ============================================================
# USER PREFERENCES / MEMORY
# ============================================================

def get_preferences():

    supabase = get_supabase()
    user_id = get_user_id()

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


# ============================================================
# SAVE PREFERENCES
# ============================================================

def save_preferences(
    preferences
):

    supabase = get_supabase()
    user_id = get_user_id()

    existing = get_preferences()

    updated_at = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )


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
                        updated_at
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
