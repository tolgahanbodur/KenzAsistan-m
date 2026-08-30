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
    upload_image,
)


# ============================================================
# SAYFA
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
# SESSION STATE
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

def start_new_conversation():

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

def load_conversation(conversation_id):

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

            load_conversation(
                conversations[0]["id"]
            )

        else:

            start_new_conversation()

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

            if start_new_conversation():

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

        conversation_id = conversation["id"]

        title = (
            conversation.get("title")
            or "Yeni sohbet"
        )

        if len(title) > 30:

            title = title[:30] + "..."


        if st.button(
            "💬 " + title,
            key="chat_" + conversation_id,
            use_container_width=True,
        ):

            load_conversation(
                conversation_id
            )

            st.rerun()


    st.divider()


    # --------------------------------------------------------
    # SON MODEL
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
    # SOHBET SİL
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

                    load_conversation(
                        conversations[0]["id"]
                    )

                else:

                    start_new_conversation()

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
    "Yazılı ve görsel sohbet edebilirsin."
)


# ============================================================
# GEÇMİŞ MESAJLAR
# ============================================================

for message in st.session_state.messages:

    role = message.get(
        "role",
        "assistant"
    )

    content = message.get(
        "content",
        ""
    )

    image_url = message.get(
        "image_url"
    )


    with st.chat_message(
        role
    ):

        # Görsel varsa göster
        if image_url:

            st.image(
                image_url,
                use_container_width=True
            )

        if content:

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

Ayrıca fotoğraf göndererek görseli analiz
etmemi de isteyebilirsin.

Örneğin:

👕 **"Bu kombin nasıl?"**

📸 **"Bu fotoğrafta ne görüyorsun?"**

🎨 **"Bu renkler uyumlu mu?"**

💇 **"Saçımı değerlendir."**
"""
        )


# ============================================================
# GÖRSEL YÜKLEME
# ============================================================

uploaded_file = st.file_uploader(
    "📷 Görsel ekle",
    type=[
        "jpg",
        "jpeg",
        "png",
        "webp",
    ],
    accept_multiple_files=False,
)


# ============================================================
# CHAT
# ============================================================

user_message = st.chat_input(
    "Kenz'e mesaj yaz..."
)


# ============================================================
# MESAJ GELDİ
# ============================================================

if user_message or uploaded_file:

    user_message = (
        user_message.strip()
        if user_message
        else ""
    )


    # --------------------------------------------------------
    # GÖRSEL BYTES
    # --------------------------------------------------------

    image_bytes = None


    if uploaded_file:

        try:

            image_bytes = (
                uploaded_file.getvalue()
            )

        except Exception as e:

            st.error(
                "Görsel okunamadı."
            )

            st.exception(e)

            st.stop()


    # --------------------------------------------------------
    # HİÇBİR ŞEY YOKSA
    # --------------------------------------------------------

    if (
        not user_message
        and not image_bytes
    ):

        st.warning(
            "Mesaj yaz veya görsel gönder."
        )

        st.stop()


    # ========================================================
    # KULLANICI MESAJI
    # ========================================================

    with st.chat_message(
        "user"
    ):

        if image_bytes:

            st.image(
                image_bytes,
                caption="Gönderilen görsel",
                use_container_width=True
            )

        if user_message:

            st.markdown(
                user_message
            )


    # ========================================================
    # SOHBET ID
    # ========================================================

    if not st.session_state.conversation_id:

        if not start_new_conversation():

            st.error(
                "Sohbet oluşturulamadı."
            )

            st.stop()


    # ========================================================
    # GÖRSELİ SUPABASE STORAGE'A YÜKLE
    # ========================================================

    image_url = None


    if image_bytes:

        file_name = (
            "chat/"
            + str(uuid.uuid4())
            + ".jpg"
        )


        try:

            image_url = upload_image(
                image_bytes,
                file_name,
                bucket_name="chat_images",
            )

        except Exception as e:

            st.warning(
                "Görsel Storage'a kaydedilemedi."
            )

            st.exception(e)


    # ========================================================
    # AI GEÇMİŞİ
    # ========================================================

    history_text = ""


    for message in st.session_state.messages:

        role = message.get(
            "role"
        )

        content = message.get(
            "content",
            ""
        )

        if not content:
            continue


        if role == "user":

            history_text += (
                "\nKullanıcı: "
                + content
            )

        elif role == "assistant":

            history_text += (
                "\nKenz: "
                + content
            )


    # ========================================================
    # SYSTEM PROMPT
    # ========================================================

    system_prompt = """
Sen Kenz adında kişisel bir yapay zeka asistanısın.

Kullanıcıyla Türkçe konuş.

Samimi, doğal, akıllı ve yardımcı ol.

Kullanıcı normal sohbet edebilir.

Kullanıcı görsel gönderirse görseli gerçekten analiz et.

Görselde kıyafet, kombin, saç, ürün, nesne,
mekan veya başka bir şey varsa analiz edebilirsin.

Kullanıcı "bu kombin nasıl?" gibi bir soru
sorarsa görseldeki kıyafetleri değerlendir.

Görseli görmediğin halde görmüş gibi davranma.

Soruyu doğrudan cevapla.

Gereksiz yere uzun cevap verme.
"""


    # ========================================================
    # PROMPT
    # ========================================================

    prompt = (
        system_prompt
        + "\n\nÖNCEKİ SOHBET:"
        + history_text
        + "\n\nYENİ KULLANICI MESAJI:"
        + (
            user_message
            if user_message
            else
            "Kullanıcı bir görsel gönderdi. "
            "Görseli analiz et."
        )
    )


    # ========================================================
    # USER MESSAGE SAVE
    # ========================================================

    try:

        add_message(
            conversation_id=(
                st.session_state.conversation_id
            ),

            role="user",

            content=user_message,

            image_url=image_url,

            provider=None,
        )

    except Exception as e:

        st.warning(
            "Kullanıcı mesajı kaydedilemedi."
        )

        st.exception(e)


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
                    image=image_bytes,
                )


                provider = (
                    st.session_state
                    .get(
                        "last_provider"
                    )
                )


                st.markdown(
                    answer
                )


                # ============================================
                # AI MESAJINI KAYDET
                # ============================================

                try:

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

                except Exception as e:

                    st.warning(
                        "AI cevabı kaydedilemedi."
                    )

                    st.exception(e)


                # ============================================
                # SESSION
                # ============================================

                st.session_state.messages.append(
                    {
                        "role":
                            "user",

                        "content":
                            user_message,

                        "image_url":
                            image_url,

                        "provider":
                            None,
                    }
                )


                st.session_state.messages.append(
                    {
                        "role":
                            "assistant",

                        "content":
                            answer,

                        "image_url":
                            None,

                        "provider":
                            provider,
                    }
                )


                # ============================================
                # SOHBET BAŞLIĞI
                # ============================================

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

                        title = (
                            user_message[:40]
                            if user_message
                            else "Görsel sohbet"
                        )


                        update_conversation_title(
                            st.session_state
                            .conversation_id,

                            client_id,

                            title,
                        )


            except Exception as e:

                st.error(
                    "Kenz cevap veremedi."
                )

                st.exception(e)
