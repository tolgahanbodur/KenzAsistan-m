import io
import uuid

import streamlit as st
from PIL import Image

from ai_router import ask_ai
from supabase_client import (
    get_conversations,
    create_conversation,
    get_messages,
    add_message,
    delete_conversation,
    update_conversation_title,
    upload_image,
)


# ============================================================
# SAYFA AYARLARI
# ============================================================

st.set_page_config(
    page_title="Kenz Asistan",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CLIENT ID
# ============================================================

if "client_id" not in st.query_params:

    st.query_params["client_id"] = str(
        uuid.uuid4()
    )

client_id = st.query_params["client_id"]


# ============================================================
# SESSION STATE
# ============================================================

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_provider" not in st.session_state:
    st.session_state.last_provider = None

if "initialized" not in st.session_state:
    st.session_state.initialized = False


# ============================================================
# SOHBET YÜKLE
# ============================================================

def load_conversation(conversation_id):

    messages = get_messages(
        conversation_id
    )

    converted = []

    for message in messages:

        converted.append(
            {
                "role": message.get(
                    "role",
                    "assistant"
                ),

                "content": message.get(
                    "content",
                    ""
                ),

                "image_url": message.get(
                    "image_url"
                ),

                "provider": message.get(
                    "provider"
                ),
            }
        )

    st.session_state.conversation_id = (
        conversation_id
    )

    st.session_state.messages = converted


# ============================================================
# YENİ SOHBET
# ============================================================

def start_new_conversation():

    conversation = create_conversation(
        client_id=client_id,
        title="Yeni sohbet"
    )

    if conversation:

        conversation_id = conversation.get(
            "id"
        )

        st.session_state.conversation_id = (
            conversation_id
        )

        st.session_state.messages = []

        return True

    return False


# ============================================================
# İLK AÇILIŞ
# ============================================================

if not st.session_state.initialized:

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


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🤖 Kenz")

    st.caption(
        "Kişisel yapay zeka asistanın"
    )

    st.divider()

    if st.button(
        "＋ Yeni sohbet",
        use_container_width=True
    ):

        if start_new_conversation():

            st.rerun()


    st.subheader("💬 Sohbetler")

    conversations = get_conversations(
        client_id
    )


    for conversation in conversations:

        conversation_id = conversation.get(
            "id"
        )

        title = conversation.get(
            "title"
        ) or "Yeni sohbet"

        if len(title) > 35:

            title = title[:35] + "..."


        active = (
            conversation_id
            ==
            st.session_state.conversation_id
        )


        button_text = (
            "🟢 "
            if active
            else "💬 "
        ) + title


        if st.button(
            button_text,
            key=f"chat_{conversation_id}",
            use_container_width=True
        ):

            load_conversation(
                conversation_id
            )

            st.rerun()


    st.divider()


    if st.session_state.last_provider:

        st.caption(
            "Son kullanılan AI"
        )

        st.info(
            st.session_state.last_provider
        )


    st.divider()


    if st.button(
        "🗑️ Bu sohbeti sil",
        use_container_width=True
    ):

        conversation_id = (
            st.session_state.conversation_id
        )

        if conversation_id:

            delete_conversation(
                conversation_id,
                client_id
            )

            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.session_state.initialized = False

            st.rerun()


# ============================================================
# ANA BAŞLIK
# ============================================================

st.title("🤖 Kenz Asistan")

st.caption(
    "Sohbet et • Görsel gönder • Analiz ettir"
)


# ============================================================
# HOŞ GELDİN MESAJI
# ============================================================

if not st.session_state.messages:

    with st.chat_message("assistant"):

        st.markdown(
            """
### Merhaba 👋

Ben **Kenz**.

Benimle normal şekilde sohbet edebilirsin.

Ayrıca 📎 butonundan fotoğraf göndererek:

- 👕 Kombinini değerlendirebilir
- 🎨 Renk uyumunu inceleyebilir
- 💇 Saç/stil analizi yapabilir
- 📸 Fotoğrafları analiz edebilir
- 🖼️ Ekran görüntülerini inceleyebilirim.

Nasıl yardımcı olabilirim?
"""
        )


# ============================================================
# GEÇMİŞ MESAJLAR
# ============================================================

for message in st.session_state.messages:

    role = message.get(
        "role",
        "assistant"
    )

    with st.chat_message(role):

        image_url = message.get(
            "image_url"
        )

        if image_url:

            try:

                st.image(
                    image_url,
                    use_container_width=True
                )

            except Exception:

                pass


        content = message.get(
            "content",
            ""
        )

        if content:

            st.markdown(
                content
            )


# ============================================================
# CHAT INPUT
# ============================================================

prompt = st.chat_input(
    "Kenz'e bir şey sor...",
    accept_file=True,
    file_type=[
        "jpg",
        "jpeg",
        "png",
        "webp"
    ],
    max_upload_size=20,
)


# ============================================================
# MESAJ GELDİ
# ============================================================

if prompt:

    user_text = ""

    try:

        user_text = prompt.text.strip()

    except Exception:

        pass


    image_bytes = None


    try:

        if prompt.files:

            image_bytes = (
                prompt
                .files[0]
                .getvalue()
            )

    except Exception as e:

        st.error(
            f"Görsel okunamadı: {e}"
        )

        st.stop()


    # --------------------------------------------------------
    # GÖRSEL KONTROL
    # --------------------------------------------------------

    if image_bytes:

        try:

            test_image = Image.open(
                io.BytesIO(
                    image_bytes
                )
            )

            test_image.verify()

        except Exception:

            st.error(
                "Yüklediğin dosya geçerli bir "
                "görsel değil."
            )

            st.stop()


    # --------------------------------------------------------
    # BOŞ MESAJ
    # --------------------------------------------------------

    if not user_text and not image_bytes:

        st.warning(
            "Bir mesaj yaz veya görsel gönder."
        )

        st.stop()


    # ========================================================
    # GÖRSELİ STORAGE'A YÜKLE
    # ========================================================

    image_url = None


    if image_bytes:

        file_name = (
            "chat/"
            + str(uuid.uuid4())
            + ".jpg"
        )

        image_url = upload_image(
            image_bytes,
            file_name,
            bucket_name="chat_images"
        )


    # ========================================================
    # KULLANICI MESAJINI SUPABASE'E KAYDET
    # ========================================================

    add_message(
        conversation_id=(
            st.session_state.conversation_id
        ),
        role="user",
        content=user_text,
        image_url=image_url,
        provider=None,
    )


    # ========================================================
    # EKRANDA GÖSTER
    # ========================================================

    with st.chat_message("user"):

        if image_bytes:

            st.image(
                image_bytes,
                caption="Gönderilen görsel",
                use_container_width=True
            )

        if user_text:

            st.markdown(
                user_text
            )


    # ========================================================
    # AI GEÇMİŞİ
    # ========================================================

    history = []


    for message in st.session_state.messages:

        text = message.get(
            "content",
            ""
        )

        if not text:
            continue

        history.append(
            {
                "role": message.get(
                    "role"
                ),
                "text": text,
            }
        )


    # ========================================================
    # SYSTEM PROMPT
    # ========================================================

    system_prompt = """
Sen Kenz adında kişisel bir yapay zeka asistanısın.

Kullanıcıyla Türkçe konuş.

Samimi, doğal, akıllı ve yardımcı ol.

Kullanıcı seninle normal şekilde sohbet edebilir.

Kullanıcı görsel gönderirse görseli gerçekten analiz et.

Görselde kıyafet, kombin, saç, ürün, nesne,
mekan veya başka bir şey varsa analiz edebilirsin.

Özellikle kombin sorularında:

- kıyafetleri belirle
- renkleri değerlendir
- parçaların uyumunu değerlendir
- eksikleri söyle
- alternatif öner
- istenirse 10 üzerinden puan ver

Görseli görmediğin halde görmüş gibi davranma.

Cevaplarını doğal ve anlaşılır tut.

Kullanıcı kısa cevap istiyorsa kısa cevap ver.

Gereksiz yere uzun cevap verme.
"""


    history_text = ""


    if history:

        history_text = (
            "\n\nÖNCEKİ KONUŞMA:\n"
        )

        for item in history:

            if item["role"] == "user":

                history_text += (
                    "Kullanıcı: "
                    + item["text"]
                    + "\n"
                )

            elif item["role"] == "assistant":

                history_text += (
                    "Kenz: "
                    + item["text"]
                    + "\n"
                )


    # ========================================================
    # AI PROMPT
    # ========================================================

    full_prompt = (
        system_prompt
        + history_text
        + "\n\nYENİ KULLANICI MESAJI:\n"
        + (
            user_text
            if user_text
            else "Kullanıcı bir görsel gönderdi."
        )
    )


    # ========================================================
    # AI CEVABI
    # ========================================================

    with st.chat_message("assistant"):

        with st.spinner(
            "Kenz düşünüyor..."
        ):

            try:

                answer = ask_ai(
                    prompt=full_prompt,
                    image=image_bytes,
                )


                provider = (
                    st.session_state.get(
                        "last_provider"
                    )
                )


                st.markdown(
                    answer
                )


                # ------------------------------------------------
                # AI MESAJINI SUPABASE'E KAYDET
                # ------------------------------------------------

                add_message(
                    conversation_id=(
                        st.session_state.conversation_id
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
                        "role": "user",
                        "content": user_text,
                        "image_url": image_url,
                    }
                )


                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "image_url": None,
                        "provider": provider,
                    }
                )


                # ------------------------------------------------
                # SOHBET BAŞLIĞI
                # ------------------------------------------------

                conversations = get_conversations(
                    client_id
                )


                current = None


                for conversation in conversations:

                    if (
                        conversation.get("id")
                        ==
                        st.session_state.conversation_id
                    ):

                        current = conversation
                        break


                if current:

                    current_title = (
                        current.get(
                            "title"
                        )
                        or "Yeni sohbet"
                    )


                    if (
                        current_title
                        ==
                        "Yeni sohbet"
                        and user_text
                    ):

                        new_title = (
                            user_text[:45]
                        )

                        update_conversation_title(
                            st.session_state.conversation_id,
                            client_id,
                            new_title,
                        )


            except Exception as e:

                st.error(
                    "Kenz cevap veremedi."
                )

                with st.expander(
                    "Teknik hata"
                ):

                    st.code(
                        str(e)
                    )


# ============================================================
# ALT BİLGİ
# ============================================================

st.divider()

st.caption(
    "Kenz Asistan • Gemini → OpenAI → OpenRouter"
)
