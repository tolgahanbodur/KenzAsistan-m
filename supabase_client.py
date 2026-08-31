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
# USER SESSION
# ============================================================

def get_session_id():

    if "kenz_user_id" not in st.session_state:

        st.session_state.kenz_user_id = str(
            uuid.uuid4()
        )

    return st.session_state.kenz_user_id


def get_user_client():

    supabase = create_supabase()

    user_id = get_session_id()

    return (
        supabase,
        user_id,
    )


# ============================================================
# CONVERSATIONS
# ============================================================

def create_conversation(
    supabase,
    user_id,
    title="Yeni sohbet",
):

    response = (
        supabase
        .table("conversations")
        .insert({
            "title": title,
            "user_session_id": user_id,
        })
        .execute()
    )

    if not response.data:

        raise RuntimeError(
            "Yeni sohbet oluşturulamadı."
        )

    return response.data[0]["id"]


def get_conversations(
    supabase,
    user_id,
):

    response = (
        supabase
        .table("conversations")
        .select(
            "id,title,created_at,updated_at,user_session_id"
        )
        .eq(
            "user_session_id",
            user_id,
        )
        .order(
            "updated_at",
            desc=True,
        )
        .execute()
    )

    return response.data or []


def get_or_create_conversation(
    supabase,
    user_id,
):

    # --------------------------------------------------------
    # Zaten seçili sohbet varsa
    # --------------------------------------------------------

    current_id = st.session_state.get(
        "kenz_conversation_id"
    )

    if current_id:

        return current_id


    # --------------------------------------------------------
    # Kullanıcının eski sohbetleri
    # --------------------------------------------------------

    conversations = get_conversations(
        supabase,
        user_id,
    )


    if conversations:

        conversation_id = conversations[0]["id"]

    else:

        conversation_id = create_conversation(
            supabase,
            user_id,
            "Yeni sohbet",
        )


    st.session_state[
        "kenz_conversation_id"
    ] = conversation_id


    return conversation_id


def switch_conversation(
    supabase,
    user_id,
    conversation_id,
):

    # --------------------------------------------------------
    # Bu sohbet gerçekten bu kullanıcıya mı ait?
    # --------------------------------------------------------

    conversations = get_conversations(
        supabase,
        user_id,
    )


    valid = False


    for conversation in conversations:

        if str(
            conversation["id"]
        ) == str(
            conversation_id
        ):

            valid = True

            break


    if not valid:

        return False


    # --------------------------------------------------------
    # Sohbeti değiştir
    # --------------------------------------------------------

    st.session_state[
        "kenz_conversation_id"
    ] = conversation_id


    # --------------------------------------------------------
    # Seçilen sohbetin mesajlarını yükle
    # --------------------------------------------------------

    st.session_state.messages = (
        get_messages_by_conversation(
            supabase,
            conversation_id,
            100,
        )
    )


    return True


def new_conversation(
    supabase,
    user_id,
):

    conversation_id = create_conversation(
        supabase,
        user_id,
        "Yeni sohbet",
    )


    st.session_state[
        "kenz_conversation_id"
    ] = conversation_id


    st.session_state.messages = []


    return conversation_id


def update_conversation_title(
    supabase,
    conversation_id,
    title,
):

    if not title:

        return


    (
        supabase
        .table("conversations")
        .update({
            "title": title[:80],
        })
        .eq(
            "id",
            conversation_id,
        )
        .execute()
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
    file_type=None,
    provider=None,
):

    conversation_id = (
        get_or_create_conversation(
            supabase,
            user_id,
        )
    )


    response = (
        supabase
        .table("messages")
        .insert({
            "conversation_id":
                conversation_id,

            "role":
                role,

            "content":
                content or "",

            "file_url":
                None,

            "file_name":
                file_name,

            "file_type":
                file_type,

            "provider":
                provider,
        })
        .execute()
    )


    # --------------------------------------------------------
    # Sohbetin son kullanım zamanını güncelle
    # --------------------------------------------------------

    (
        supabase
        .table("conversations")
        .update({
            "updated_at":
                "now()",
        })
        .eq(
            "id",
            conversation_id,
        )
        .execute()
    )


    return response.data


def get_messages_by_conversation(
    supabase,
    conversation_id,
    limit=100,
):

    if not conversation_id:

        return []


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


def get_messages(
    supabase,
    user_id,
    limit=100,
):

    conversation_id = (
        get_or_create_conversation(
            supabase,
            user_id,
        )
    )


    return get_messages_by_conversation(
        supabase,
        conversation_id,
        limit,
    )


# ============================================================
# MEMORY
# ============================================================

def get_memories(
    supabase,
    user_id,
):

    response = (
        supabase
        .table("memories")
        .select("*")
        .eq(
            "user_session_id",
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


    (
        supabase
        .table("memories")
        .insert({
            "user_session_id":
                user_id,

            "memory":
                memory,
        })
        .execute()
    )


def delete_memory(
    supabase,
    user_id,
    memory_id,
):

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
            user_id,
        )
        .execute()
    )


# ============================================================
# WARDROBE
# ============================================================

def get_wardrobe(
    supabase,
    user_id,
):

    response = (
        supabase
        .table("wardrobe")
        .select("*")
        .eq(
            "user_session_id",
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


    (
        supabase
        .table("wardrobe")
        .insert({
            "user_session_id":
                user_id,

            "name":
                item.get(
                    "name",
                    "Kıyafet",
                ),

            "category":
                item.get(
                    "category",
                    "diğer",
                ),

            "color":
                item.get(
                    "color",
                    "belirsiz",
                ),

            "description":
                item.get(
                    "description",
                    "",
                ),

            "metadata":
                item,
        })
        .execute()
    )
