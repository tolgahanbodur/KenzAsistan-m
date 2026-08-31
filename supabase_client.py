import os
import uuid
import base64
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

        st.session_state.kenz_session_id = str(
            uuid.uuid4()
        )

    return st.session_state.kenz_session_id


# ============================================================
# USER / CLIENT
# ============================================================

def get_user_client():

    supabase = create_supabase()

    session_id = get_session_id()

    return supabase, session_id


# ============================================================
# CONVERSATION
# ============================================================

def get_or_create_conversation(
    supabase,
    session_id,
):

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

    conversations = response.data or []

    if conversations:

        return conversations[0]["id"]


    response = (
        supabase
        .table("conversations")
        .insert(
            {
                "title": "Yeni sohbet",
                "user_session_id": session_id,
            }
        )
        .execute()
    )

    if not response.data:

        raise RuntimeError(
            "Yeni konuşma oluşturulamadı."
        )

    return response.data[0]["id"]


# ============================================================
# NEW CONVERSATION
# ============================================================

def create_new_conversation(
    supabase,
    session_id,
    title="Yeni sohbet",
):

    response = (
        supabase
        .table("conversations")
        .insert(
            {
                "title": title,
                "user_session_id": session_id,
            }
        )
        .execute()
    )

    if not response.data:

        raise RuntimeError(
            "Yeni konuşma oluşturulamadı."
        )

    return response.data[0]["id"]


# ============================================================
# CURRENT CONVERSATION
# ============================================================

def get_current_conversation(
    supabase,
    session_id,
):

    if "kenz_conversation_id" not in st.session_state:

        st.session_state.kenz_conversation_id = (
            get_or_create_conversation(
                supabase,
                session_id,
            )
        )

    return st.session_state.kenz_conversation_id


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

    conversation_id = get_current_conversation(
        supabase,
        session_id,
    )

    file_url = None

    # --------------------------------------------------------
    # FILE STORAGE
    # --------------------------------------------------------

    # Dosya yükleme daha sonra Supabase Storage'a bağlanabilir.
    # Şimdilik mesaj tablosunda URL boş bırakılıyor.
    #
    # Böylece büyük dosyaları database içine base64 olarak
    # doldurup sistemi şişirmiyoruz.

    response = (
        supabase
        .table("messages")
        .insert(
            {
                "conversation_id": conversation_id,
                "role": role,
                "content": content or "",
                "file_url": file_url,
                "file_name": file_name,
                "file_type": file_type,
                "provider": provider,
            }
        )
        .execute()
    )

    if not response.data:

        raise RuntimeError(
            "Mesaj kaydedilemedi."
        )

    # Conversation updated_at
    try:

        (
            supabase
            .table("conversations")
            .update(
                {
                    "updated_at": "now()"
                }
            )
            .eq(
                "id",
                conversation_id,
            )
            .execute()
        )

    except Exception:
        pass


# ============================================================
# GET MESSAGES
# ============================================================

def get_messages(
    supabase,
    session_id,
    limit=100,
):

    conversation_id = get_current_conversation(
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
    session_id,
):

    # Hafıza tablosu mevcut değilse boş döndür.
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


# ============================================================
# SAVE MEMORY
# ============================================================

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
            .insert(
                {
                    "user_session_id": session_id,
                    "memory": memory,
                }
            )
            .execute()
        )

    except Exception:

        # Hafıza tablosu henüz oluşturulmamışsa
        # sohbetin çalışmasını engelleme.
        pass


# ============================================================
# DELETE MEMORY
# ============================================================

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


# ============================================================
# ADD WARDROBE
# ============================================================

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
            .insert(
                {
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
                }
            )
            .execute()
        )

    except Exception:

        pass
