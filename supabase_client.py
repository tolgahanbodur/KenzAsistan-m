import os
import uuid
from datetime import datetime, timezone

import streamlit as st
from supabase import create_client, Client


# ============================================================
# SUPABASE CLIENT
# ============================================================

@st.cache_resource
def get_supabase() -> Client:

    url = os.environ.get(
        "SUPABASE_URL"
    )

    key = os.environ.get(
        "SUPABASE_KEY"
    )


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

    if supabase is None:
        return None


    result = (
        supabase
        .table("clothes")
        .insert(
            {
                "image_url": image_url,
                "category": category,
                "color": color,
                "description": description,
            }
        )
        .execute()
    )


    return getattr(
        result,
        "data",
        []
    )


def get_all_clothes():

    supabase = get_supabase()

    if supabase is None:
        return []


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
    )


# ============================================================
# STORAGE
# ============================================================

def upload_image(
    file_bytes,
    file_name,
    bucket_name="wardrobe_images"
):

    supabase = get_supabase()

    if supabase is None:
        return None


    try:

        # Aynı dosya varsa üzerine yaz
        supabase.storage.from_(
            bucket_name
        ).upload(
            file_name,
            file_bytes,
            {
                "content-type": "image/jpeg",
                "upsert": "true",
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
            "Storage upload error:",
            repr(e)
        )

        return None


# ============================================================
# CHAT CLIENT ID
# ============================================================

def get_client_id():

    if "client_id" in st.query_params:

        return st.query_params["client_id"]


    if "client_id" not in st.session_state:

        st.session_state.client_id = str(
            uuid.uuid4()
        )


    return st.session_state.client_id


# ============================================================
# SOHBET OLUŞTUR
# ============================================================

def create_conversation(
    client_id=None,
    title="Yeni sohbet"
):

    supabase = get_supabase()

    if supabase is None:
        return None


    if client_id is None:

        client_id = get_client_id()


    result = (
        supabase
        .table("conversations")
        .insert(
            {
                "client_id": client_id,
                "title": title,
            }
        )
        .execute()
    )


    data = getattr(
        result,
        "data",
        []
    )


    if not data:
        return None


    return data[0]


# ============================================================
# SOHBETLER
# ============================================================

def get_conversations(
    client_id=None
):

    supabase = get_supabase()

    if supabase is None:
        return []


    if client_id is None:

        client_id = get_client_id()


    try:

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
        ) or []


    except Exception as e:

        print(
            "GET CONVERSATIONS ERROR:",
            repr(e)
        )

        return []


# ============================================================
# TEK SOHBET
# ============================================================

def get_conversation(
    conversation_id,
    client_id=None
):

    supabase = get_supabase()

    if supabase is None:
        return None


    if client_id is None:

        client_id = get_client_id()


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
                "client_id",
                client_id
            )
            .execute()
        )


        data = getattr(
            result,
            "data",
            []
        )


        if data:

            return data[0]


        return None


    except Exception as e:

        print(
            "GET CONVERSATION ERROR:",
            repr(e)
        )

        return None


# ============================================================
# MESAJLAR
# ============================================================

def get_messages(
    conversation_id
):

    supabase = get_supabase()

    if supabase is None:
        return []


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


        return getattr(
            result,
            "data",
            []
        ) or []


    except Exception as e:

        print(
            "GET MESSAGES ERROR:",
            repr(e)
        )

        return []


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

    if supabase is None:
        return None


    try:

        result = (
            supabase
            .table("messages")
            .insert(
                {
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
            )
            .execute()
        )


        # Sohbet tarihini güncelle
        supabase.table(
            "conversations"
        ).update(
            {
                "updated_at":
                    datetime.now(
                        timezone.utc
                    ).isoformat()
            }
        ).eq(
            "id",
            conversation_id
        ).execute()


        return getattr(
            result,
            "data",
            []
        )


    except Exception as e:

        print(
            "ADD MESSAGE ERROR:",
            repr(e)
        )

        return None


# ============================================================
# SOHBET SİL
# ============================================================

def delete_conversation(
    conversation_id,
    client_id=None
):

    supabase = get_supabase()

    if supabase is None:
        return False


    if client_id is None:

        client_id = get_client_id()


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
                "client_id",
                client_id
            )
            .execute()
        )


        return True


    except Exception as e:

        print(
            "DELETE CONVERSATION ERROR:",
            repr(e)
        )

        return False


# ============================================================
# BAŞLIK GÜNCELLE
# ============================================================

def update_conversation_title(
    conversation_id,
    client_id,
    title
):

    supabase = get_supabase()

    if supabase is None:
        return False


    try:

        (
            supabase
            .table("conversations")
            .update(
                {
                    "title": title,
                    "updated_at":
                        datetime.now(
                            timezone.utc
                        ).isoformat(),
                }
            )
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


    except Exception as e:

        print(
            "UPDATE TITLE ERROR:",
            repr(e)
        )

        return False
