import os
import uuid
import streamlit as st

from supabase import create_client, Client


@st.cache_resource
def get_supabase() -> Client:

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url:
        url = st.secrets.get(
            "SUPABASE_URL",
            ""
        )

    if not key:
        key = st.secrets.get(
            "SUPABASE_KEY",
            ""
        )

    if not url or not key:
        return None

    return create_client(
        url,
        key
    )


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

    if not supabase:
        return None

    res = supabase.table(
        "clothes"
    ).insert({

        "image_url": image_url,
        "category": category,
        "color": color,
        "description": description

    }).execute()

    return getattr(
        res,
        "data",
        res
    )


def get_all_clothes():

    supabase = get_supabase()

    if not supabase:
        return []

    res = supabase.table(
        "clothes"
    ).select(
        "*"
    ).order(
        "added_date",
        desc=True
    ).execute()

    return getattr(
        res,
        "data",
        []
    )


def upload_image(
    file_bytes,
    file_name
):

    supabase = get_supabase()

    if not supabase:
        return None

    bucket_name = "wardrobe_images"

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

        public_url = (
            supabase
            .storage
            .from_(bucket_name)
            .get_public_url(
                file_name
            )
        )

        return public_url

    except Exception as e:

        print(
            f"Yükleme hatası: {e}"
        )

        return None


# ============================================================
# CHAT CLIENT ID
# ============================================================

def get_client_id():

    if "client_id" not in st.session_state:

        st.session_state.client_id = str(
            uuid.uuid4()
        )

    return st.session_state.client_id


# ============================================================
# SOHBET OLUŞTUR
# ============================================================

def create_conversation(
    title="Yeni sohbet"
):

    supabase = get_supabase()

    if not supabase:
        return None

    client_id = get_client_id()

    result = supabase.table(
        "conversations"
    ).insert({

        "client_id":
            client_id,

        "title":
            title

    }).execute()

    data = getattr(
        result,
        "data",
        []
    )

    if not data:
        return None

    return data[0]


# ============================================================
# SOHBETLERİ GETİR
# ============================================================

def get_conversations():

    supabase = get_supabase()

    if not supabase:
        return []

    client_id = get_client_id()

    result = (
        supabase
        .table("conversations")
        .select("*")
        .eq(
            "client_id",
            client_id
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
    )


# ============================================================
# TEK SOHBET
# ============================================================

def get_conversation(
    conversation_id
):

    supabase = get_supabase()

    if not supabase:
        return None

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
            client_id
        )
        .maybe_single()
        .execute()
    )

    return getattr(
        result,
        "data",
        None
    )


# ============================================================
# MESAJLARI GETİR
# ============================================================

def get_messages(
    conversation_id
):

    supabase = get_supabase()

    if not supabase:
        return []

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
    )


# ============================================================
# MESAJ EKLE
# ============================================================

def add_message(
    conversation_id,
    role,
    content,
    image_url=None,
    provider=None
):

    supabase = get_supabase()

    if not supabase:
        return None

    result = supabase.table(
        "messages"
    ).insert({

        "conversation_id":
            conversation_id,

        "role":
            role,

        "content":
            content,

        "image_url":
            image_url,

        "provider":
            provider

    }).execute()

    # Sohbetin updated_at değerini güncelle
    try:

        supabase.table(
            "conversations"
        ).update({

            "updated_at":
                "now()"

        }).eq(
            "id",
            conversation_id
        ).execute()

    except Exception:
        pass

    return getattr(
        result,
        "data",
        result
    )


# ============================================================
# SOHBET SİL
# ============================================================

def delete_conversation(
    conversation_id
):

    supabase = get_supabase()

    if not supabase:
        return False

    client_id = get_client_id()

    result = (
        supabase
        .table("conversations")
        .delete()
        .eq(
            "id",
            conversation_id
        )
        .eq(
            "client_id",
            client_id
        )
        .execute()
    )

    return True


# ============================================================
# SOHBET BAŞLIĞINI GÜNCELLE
# ============================================================

def update_conversation_title(
    conversation_id,
    title
):

    supabase = get_supabase()

    if not supabase:
        return False

    client_id = get_client_id()

    (
        supabase
        .table("conversations")
        .update({
            "title": title
        })
        .eq(
            "id",
            conversation_id
        )
        .eq(
            "client_id",
            client_id
        )
        .execute()
    )

    return True
