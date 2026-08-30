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
        os.environ.get(
            "SUPABASE_URL",
            ""
        )
    )

    key = st.secrets.get(
        "SUPABASE_KEY",
        os.environ.get(
            "SUPABASE_KEY",
            ""
        )
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
# AUTH
# ============================================================

def get_current_user():

    supabase = get_supabase()

    try:

        response = supabase.auth.get_user()

        if response and response.user:

            return response.user

    except Exception:

        pass

    return None


def get_user_id():

    user = get_current_user()

    if not user:
        return None

    return str(
        user.id
    )


def is_authenticated():

    return (
        get_current_user()
        is not None
    )


# ============================================================
# SIGN UP
# ============================================================

def sign_up(
    email,
    password,
    name=""
):

    supabase = get_supabase()

    result = (
        supabase
        .auth
        .sign_up(
            {
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "name": name
                    }
                }
            }
        )
    )

    return result


# ============================================================
# LOGIN
# ============================================================

def sign_in(
    email,
    password
):

    supabase = get_supabase()

    result = (
        supabase
        .auth
        .sign_in_with_password(
            {
                "email": email,
                "password": password
            }
        )
    )

    return result


# ============================================================
# LOGOUT
# ============================================================

def sign_out():

    supabase = get_supabase()

    try:

        supabase.auth.sign_out()

    except Exception:

        pass

    # Session temizliği

    keys_to_remove = [
        "conversation_id",
        "messages",
        "initialized",
        "last_provider",
        "selected_file",
        "selected_file_name",
        "selected_file_type",
        "show_wardrobe",
    ]

    for key in keys_to_remove:

        if key in st.session_state:

            del st.session_state[key]


# ============================================================
# PROFILE
# ============================================================

def get_profile():

    supabase = get_supabase()

    user_id = get_user_id()

    if not user_id:
        return None

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

    return (
        rows[0]
        if rows
        else None
    )


def update_profile(
    name=None,
    avatar_url=None
):

    supabase = get_supabase()

    user_id = get_user_id()

    if not user_id:
        return []

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

    if not user_id:

        raise RuntimeError(
            "Önce giriş yapmalısınız."
        )

    result = (
        supabase
        .table("conversations")
        .insert(
            {
                "user_id":
                    user_id,

                "title":
                    title
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

    user_id = get_user_id()

    if not user_id:
        return []

    result = (
        supabase
        .table("conversations")
        .select(
            """
            id,
            user_id,
            title,
            created_at,
            updated_at
            """
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


def get_conversation(
    conversation_id
):

    supabase = get_supabase()

    user_id = get_user_id()

    if not user_id:
        return None

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


def update_conversation_title(
    conversation_id,
    title
):

    supabase = get_supabase()

    user_id = get_user_id()

    if not user_id:
        return []

    result = (
        supabase
        .table("conversations")
        .update(
            {
                "title":
                    title,

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


def delete_conversation(
    conversation_id
):

    supabase = get_supabase()

    user_id = get_user_id()

    if not user_id:
        return False

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

    if not user_id:
        return []

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

    if not user_id:

        raise RuntimeError(
            "Önce giriş yapmalısınız."
        )

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

    if not user_id:

        raise RuntimeError(
            "Önce giriş yapmalısınız."
        )

    # Her kullanıcının kendi klasörü

    storage_path = (
        str(user_id)
        + "/"
        + file_name
    )

    supabase.storage.from_(
        bucket_name
    ).upload(
        storage_path,
        file_bytes,
        {
            "content-type":
                content_type,

            "upsert":
                True
        }
    )

    return (
        supabase
        .storage
        .from_(
            bucket_name
        )
        .get_public_url(
            storage_path
        )
    )


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

    if not user_id:

        raise RuntimeError(
            "Önce giriş yapmalısınız."
        )

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


def get_all_clothes():

    supabase = get_supabase()

    user_id = get_user_id()

    if not user_id:
        return []

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


def delete_clothing_item(
    clothing_id
):

    supabase = get_supabase()

    user_id = get_user_id()

    if not user_id:
        return False

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
# USER PREFERENCES
# ============================================================

def get_user_preferences():

    supabase = get_supabase()

    user_id = get_user_id()

    if not user_id:
        return None

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


def save_user_preferences(
    preferences
):

    supabase = get_supabase()

    user_id = get_user_id()

    if not user_id:

        raise RuntimeError(
            "Önce giriş yapmalısınız."
        )

    existing = get_user_preferences()

    data = {

        "user_id":
            user_id,

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
            .table(
                "user_preferences"
            )
            .update(
                {
                    "preferences":
                        preferences,

                    "updated_at":
                        data[
                            "updated_at"
                        ]
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
                data
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
