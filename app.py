import streamlit as st
import uuid

from ai_router import ask_ai
from supabase_client import (
    get_client_id,
    get_conversations,
    create_conversation,
    get_messages,
    add_message,
    delete_conversation,
    update_conversation_title,
)


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Kenz Asistan",
    page_icon="🤖",
    layout="wide",
)


# ============================================================
# CLIENT ID
# ============================================================

client_id = get_client_id()


# ============================================================
# SESSION
# ============================================================

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "initialized" not in st.session_state:
    st.session_state.initialized = False

if "last_provider" not in st.session_state:
    st.session_state.last_provider = None


# ============================================================
# YENİ SOHBET
# ============================================================

def new_chat():

    conversation = create_conversation(
        client_id=client_id,
        title="Yeni sohbet",
    )

    if not conversation:
        return False

    st.session_state.conversation_id = conversation["id"]

    st.session_state.messages = []

    return True


# ============================================================
# SOHBET YÜKLE
# ============================================================

def load_chat(conversation_id):

    messages = get_messages(
        conversation_id
    )

    st.session_state.conversation_id = (
        conversation_id
    )

    st.session_state.messages = messages


# ============================================================
# İLK AÇILIŞ
# ============================================================

if not st.session_state.initialized:

    try:

        conversations = get_conversations(
            client_id
        )

        if conversations:

            load_chat(
                conversations[0]["id"]
            )

        else:

            new_chat()

        st.session_state.initialized = True

    except Exception as e:

        st.error(
            "Kenz başlatılırken hata oluştu."
        )

        st.exception(e)

        st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🤖 Kenz")

    st.caption(
        "Kişisel yapay zeka asistanın"
    )

    st.divider()


    # --------------------------------------------------------
    # YENİ SOHBET
    # --------------------------------------------------------

    if st.button(
        "＋ Yeni sohbet",
        use_container_width=True,
    ):

        try:

            if new_chat():
                st.rerun()

        except Exception as e:

            st.error(
                "Yeni sohbet oluşturulamadı."
            )

            st.exception(e)


    st.divider()


    # --------------------------------------------------------
    # SOHBET GEÇMİŞİ
    # --------------------------------------------------------

    st.subheader(
        "💬 Sohbetler"
    )


    try:

        conversations = get_conversations(
            client_id
        )

    except Exception as e:

        conversations = []

        st.error(
            "Sohbetler alınamadı."
        )

        st.exception(e)


    if not conversations:

        st.caption(
            "Henüz sohbet yok."
        )


    for conversation in conversations:

        conversation_id = (
            conversation["id"]
        )

        title = (
            conversation.get("title")
            or "Yeni sohbet"
        )


        if len(title) > 30:

            title = (
                title[:30]
                + "..."
            )


        if st.button(
            "💬 " + title,
            key=conversation_id,
            use_container_width=True,
        ):

            load_chat(
                conversation_id
            )

            st.rerun()


    st.divider()


    # --------------------------------------------------------
    # PROVIDER
    # --------------------------------------------------------

    if st.session_state.last_provider:

        st.caption(
            "Son kullanılan model"
        )

        st.write(
            st.session_state.last_provider
        )


    st.divider()


    # --------------------------------------------------------
    # SİL
    # --------------------------------------------------------

    if st.session_state.conversation_id:

        if st.button(
            "🗑️ Bu sohbeti sil",
            use_container_width=True,
        ):

            try:

                delete_conversation(
                    st.session_state.conversation_id,
                    client_id,
                )

                st.session_state.conversation_id = None

                st.session_state.messages = []

                conversations = get_conversations(
                    client_id
                )

                if conversations:

                    load_chat(
                        conversations[0]["id"]
                    )

                else:

                    new_chat()

                st.rerun()

            except Exception as e:

                st.error(
                    "Sohbet silinemedi."
                )

                st.exception(e)


# ============================================================
# ANA EKRAN
# ============================================================

st.title(
    "🤖 Kenz Asistan"
)

st.caption(
    "Senin kişisel yapay zeka asistanın"
)


# ============================================================
# MESAJLAR
# ============================================================

for message in st.session_state.messages:

    role = message.get(
        "role",
        "assistant",
    )

    content = message.get(
        "content",
        "",
    )

    if not content:
        continue

    with st.chat_message(
        role
    ):

        st.markdown(
            content
        )


# ============================================================
# BOŞ SOHBET
# ============================================================

if not st.session_state.messages:

    with st.chat_message(
        "assistant"
    ):

        st.markdown(
            """
### Merhaba 👋

Ben **Kenz**.

Benimle normal şekilde sohbet edebilirsin.

Örneğin:

**"Bugün ne giysem?"**

**"Bana bir film öner."**

**"Python öğrenmeye nereden başlamalıyım?"**

**"Bu kombin nasıl?"**

Mesajını aşağıdaki kutuya yaz.
"""
        )


# ============================================================
# CHAT INPUT
# ============================================================

user_message = st.chat_input(
    "Kenz'e mesaj yaz..."
)


# ============================================================
# MESAJ GELDİ
# ============================================================

if user_message:

    user_message = user_message.strip()


    if not user_message:

        st.warning(
            "Lütfen bir mesaj yaz."
        )

        st.stop()


    # ========================================================
    # USER MESSAGE
    # ========================================================

    with st.chat_message(
        "user"
    ):

        st.markdown(
            user_message
        )


    # ========================================================
    # GEÇMİŞİ HAZIRLA
    # ========================================================

    history = []


    for message in st.session_state.messages:

        content = message.get(
            "content",
            "",
        )

        if not content:
            continue


        history.append(
            {
                "role": message.get(
                    "role"
                ),

                "text": content,
            }
        )


    # ========================================================
    # PROMPT
    # ========================================================

    system_prompt = """
Sen Kenz adında kişisel bir yapay zeka asistanısın.

Kullanıcıyla Türkçe konuş.

Samimi, doğal, akıllı ve yardımcı ol.

Normal sohbet edebilirsin.

Soruyu doğrudan cevapla.

Gereksiz yere uzun cevap verme.

Kullanıcı detay isterse ayrıntılı cevap ver.
"""


    history_text = ""


    for item in history:

        if item["role"] == "user":

            history_text += (
                "\nKullanıcı: "
                + item["text"]
            )

        elif item["role"] == "assistant":

            history_text += (
                "\nKenz: "
                + item["text"]
            )


    prompt = (
        system_prompt
        + "\n\nÖNCEKİ KONUŞMA:"
        + history_text
        + "\n\nYENİ MESAJ:"
        + user_message
    )


    # ========================================================
    # AI
    # ========================================================

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "Kenz düşünüyor..."
        ):

            try:

                answer = ask_ai(
                    prompt=prompt,
                    image=None,
                )


                st.markdown(
                    answer
                )


                provider = (
                    st.session_state
                    .get(
                        "last_provider"
                    )
                )


                # ------------------------------------------------
                # USER SAVE
                # ------------------------------------------------

                add_message(
                    conversation_id=(
                        st.session_state
                        .conversation_id
                    ),

                    role="user",

                    content=user_message,

                    image_url=None,

                    provider=None,
                )


                # ------------------------------------------------
                # AI SAVE
                # ------------------------------------------------

                add_message(
                    conversation_id=(
                        st.session_state
                        .conversation_id
                    ),

                    role="assistant",

                    content=answer,

                    image_url=None,

                    provider=provider,
                )


                # ------------------------------------------------
                # SESSION
                # ------------------------------------------------

                st.session_state.messages.append(
                    {
                        "role":
                            "user",

                        "content":
                            user_message,
                    }
                )


                st.session_state.messages.append(
                    {
                        "role":
                            "assistant",

                        "content":
                            answer,

                        "provider":
                            provider,
                    }
                )


                # ------------------------------------------------
                # BAŞLIK
                # ------------------------------------------------

                conversations = (
                    get_conversations(
                        client_id
                    )
                )


                current = None


                for conversation in conversations:

                    if (
                        conversation["id"]
                        ==
                        st.session_state
                        .conversation_id
                    ):

                        current = conversation

                        break


                if current:

                    if (
                        current.get(
                            "title"
                        )
                        ==
                        "Yeni sohbet"
                    ):

                        update_conversation_title(
                            st.session_state
                            .conversation_id,

                            client_id,

                            user_message[:40],
                        )


            except Exception as e:

                st.error(
                    "Kenz cevap oluşturamadı."
                )

                st.exception(e)
