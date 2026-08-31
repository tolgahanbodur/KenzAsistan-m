import os
import uuid
import streamlit as st
from supabase import create_client


# ============================================================
# SECRETS
# ============================================================

def get_secret(name):
    value = os.environ.get(name)

    if value:
        return value

    try:
        return st.secrets[name]
    except Exception:
        return None


# ============================================================
# SUPABASE
# ============================================================

@st.cache_resource
def create_supabase():

    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")

    if not url:
        raise ValueError("SUPABASE_URL bulunamadı.")

    if not key:
        raise ValueError("SUPABASE_KEY bulunamadı.")

    return create_client(url, key)


# ============================================================
# SESSION
# ============================================================

def get_session_id():

    if "kenz_session_id" not in st.session_state:
        st.session_state.kenz_session_id = str(uuid.uuid4())

    return st.session_state.kenz_session_id


def get_user_client():

    supabase = create_supabase()
    session_id = get_session_id()

    return supabase, session_id


# ============================================================
# CONVERSATIONS
# ============================================================

def create_conversation(
    supabase,
    session_id,
    title="Yeni sohbet",
):

    response = (
        supabase
        .table("conversations")
        .insert({
            "title": title,
            "user_session_id": session_id,
        })
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Yeni konuşma oluşturulamadı."
        )

    return response.data[0]["id"]


def get_or_create_conversation(
    supabase,
    session_id,
):

    if "kenz_conversation_id" in st.session_state:
        return st.session_state.kenz_conversation_id

    response = (
        supabase
        .table("conversations")
        .select("*")
        .eq(
            "user_session_id",
            session_id,
        )
        .order(
            "updated_at",
            desc=True,
        )
        .limit(1)
        .execute()
    )

    if response.data:
        conversation_id = response.data[0]["id"]

    else:
        conversation_id = create_conversation(
            supabase,
            session_id,
        )

    st.session_state.kenz_conversation_id = (
        conversation_id
    )

    return conversation_id


def new_conversation(
    supabase,
    session_id,
):

    conversation_id = create_conversation(
        supabase,
        session_id,
    )

    st.session_state.kenz_conversation_id = (
        conversation_id
    )

    st.session_state.messages = []

    return conversation_id


# ============================================================
# MESSAGES
# ============================================================

def save_message(
    supabase,
    session_id,
    role,
    content,
    file_name=None,
    file_bytes=None,
    file_type=None,
    provider=None,
):

    conversation_id = get_or_create_conversation(
        supabase,
        session_id,
    )

    # --------------------------------------------------------
    # Dosyayı şimdilik database'e gömmüyoruz.
    # Büyük dosyalar için Supabase Storage kullanacağız.
    # --------------------------------------------------------

    response = (
        supabase
        .table("messages")
        .insert({
            "conversation_id": conversation_id,
            "role": role,
            "content": content or "",
            "file_url": None,
            "file_name": file_name,
            "file_type": file_type,
            "provider": provider,
        })
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Mesaj kaydedilemedi."
        )


def get_messages(
    supabase,
    session_id,
    limit=100,
):

    conversation_id = get_or_create_conversation(
        supabase,
        session_id,
    )

    response = (
        supabase
        .table("messages")
        .select("*")
        .eq(
            "conversation_id",
            conversation_id,
        )
        .order(
            "created_at",
            desc=False,
        )
        .limit(limit)
        .execute()
    )

    return response.data or []


# ============================================================
# MEMORY
# ============================================================

def get_memories(
    supabase,
    session_id,
):

    try:

        response = (
            supabase
            .table("memories")
            .select("*")
            .eq(
                "user_session_id",
                session_id,
            )
            .order(
                "created_at",
                desc=True,
            )
            .execute()
        )

        return response.data or []

    except Exception:

        return []


def save_memory(
    supabase,
    session_id,
    memory,
):

    if not memory:
        return

    try:

        (
            supabase
            .table("memories")
            .insert({
                "user_session_id": session_id,
                "memory": memory,
            })
            .execute()
        )

    except Exception:
        pass


def delete_memory(
    supabase,
    session_id,
    memory_id,
):

    try:

        (
            supabase
            .table("memories")
            .delete()
            .eq(
                "id",
                memory_id,
            )
            .eq(
                "user_session_id",
                session_id,
            )
            .execute()
        )

    except Exception:
        pass


# ============================================================
# WARDROBE
# ============================================================

def get_wardrobe(
    supabase,
    session_id,
):

    try:

        response = (
            supabase
            .table("wardrobe")
            .select("*")
            .eq(
                "user_session_id",
                session_id,
            )
            .order(
                "created_at",
                desc=True,
            )
            .execute()
        )

        return response.data or []

    except Exception:

        return []


def add_wardrobe_item(
    supabase,
    session_id,
    item,
):

    if not item:
        return

    try:

        (
            supabase
            .table("wardrobe")
            .insert({
                "user_session_id": session_id,
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
            })
            .execute()
        )

    except Exception:
        pass
