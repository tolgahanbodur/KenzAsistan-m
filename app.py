import streamlit as st
import io
import uuid

from PIL import Image

from ai_router import ask_ai

from supabase_client import (
    get_conversations,
    create_conversation,
    get_messages,
    add_message,
    delete_conversation,
    update_conversation_title
)


# ============================================================
# SAYFA
# ============================================================

st.set_page_config(
    page_title="Kenz Asistan",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# SESSION
# ============================================================

if "conversation_id" not in st.session_state:

    st.session_state.conversation_id = None


if "messages" not in st.session_state:

    st.session_state.messages = []


if "last_provider" not in st.session_state:

    st.session_state.last_provider = None


# ============================================================
# SOHBETİ YÜKLE
# ============================================================

def load_conversation(
    conversation_id
):

    messages = get_messages(
        conversation_id
    )

    converted = []

    for message in messages:

        converted.append({

            "role":
                message["role"],

            "content":
                message.get(
                    "content",
                    ""
                ),

            "image_url":
                message.get(
                    "image_url"
                ),

            "provider":
                message.get(
                    "provider"
                )

        })

    st.session_state.messages = converted

    st.session_state.conversation_id = (
        conversation_id
    )


# ============================================================
# YENİ SOHBET
# ============================================================

def new_conversation():

    conversation = create_conversation(
        "Yeni sohbet"
    )

    if conversation:

        st.session_state.conversation_id = (
            conversation["id"]
        )

        st.session_state.messages = []


# ============================================================
# İLK AÇILIŞ
# ============================================================

if st.session_state.conversation_id is None:

    conversations = get_conversations()

    if conversations:

        load_conversation(
            conversations[0]["id"]
        )

    else:

        new_conversation()


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

        new_conversation()

        st.rerun()


    st.subheader(
        "💬 Sohbetler"
    )


    conversations = get_conversations()


    for conversation in conversations:

        conversation_id = (
            conversation["id"]
        )

        title = (
            conversation.get(
                "title"
            )
            or "Yeni sohbet"
        )

        is_active = (
            conversation_id
            ==
            st.session_state.conversation_id
        )


        if st.button(
            (
                "🟢 "
                if is_active
                else "💬 "
            )
            + title,
            key=
                f"conversation_{conversation_id}",
            use_container_width=True
        ):

            load_conversation(
                conversation_id
            )

            st.rerun()


    st.divider()


    if st.session_state.last_provider:

        st.caption(
            "Son kullanılan model"
        )

        st.info(
            st.session_state.last_provider
        )


    st.divider()


    if st.button(
        "🗑️ Bu sohbeti sil",
        use_container_width=True
    ):

        if st.session_state.conversation_id:

            delete_conversation(
                st.session_state.conversation_id
            )

            st.session_state.conversation_id = None

            st.session_state.messages = []

            st.rerun()


# ============================================================
# BAŞLIK
# ============================================================

st.title(
    "🤖 Kenz Asistan"
)

st.caption(
    "Sohbet et • Görsel gönder • Analiz ettir"
)


# ============================================================
# MESAJLAR
# ============================================================

for message in st.session_state.messages:

    role = message.get(
        "role",
        "assistant"
    )

    with st.chat_message(
        role
    ):

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

    max_upload_size=20

)


# ============================================================
# YENİ MESAJ
# ============================================================

if prompt:

    user_text = ""

    try:

        user_text = (
            prompt.text
            .strip()
        )

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
            "Görsel okunamadı: "
            + str(e)
        )

        st.stop()


    # --------------------------------------------------------
    # GÖRSEL KONTROL
    # --------------------------------------------------------

    if image_bytes:

        try:

            image = Image.open(
                io.BytesIO(
                    image_bytes
                )
            )

            image.verify()

        except Exception:

            st.error(
                "Geçerli bir görsel yükle."
            )

            st.stop()


    # --------------------------------------------------------
    # BOŞ MESAJ
    # --------------------------------------------------------

    if (
        not user_text
        and not image_bytes
    ):

        st.warning(
            "Mesaj yaz veya görsel gönder."
        )

        st.stop()


    # ========================================================
    # GÖRSELİ SUPABASE'E YÜKLE
    # ========================================================

    image_url = None


    if image_bytes:

        from supabase_client import upload_image

        file_name = (
            "chat/"
            + str(
                uuid.uuid4()
            )
            + ".jpg"
        )


        image_url = upload_image(
            image_bytes,
            file_name
        )


    # ========================================================
    # KULLANICI MESAJINI KAYDET
    # ========================================================

    add_message(

        conversation_id=
            st.session_state.conversation_id,

        role="user",

        content=user_text,

        image_url=image_url

    )


    # ========================================================
    # EKRANDA GÖSTER
    # ========================================================

    with st.chat_message(
        "user"
    ):

        if image_bytes:

            st.image(
                image_bytes,
                use_container_width=True
            )

        if user_text:

            st.markdown(
                user_text
            )


    # ========================================================
    # GEÇMİŞİ AI'A HAZIRLA
    # ========================================================

    history = []


    for message in st.session_state.messages:

        history.append({

            "role":
                message.get(
                    "role"
                ),

            "text":
                message.get(
                    "content",
                    ""
                )

        })


    # ========================================================
    # PROMPT
    # ========================================================

    system_prompt = """

Sen Kenz adında kişisel bir yapay zeka asistanısın.

Kullanıcıyla Türkçe konuş.

Samimi, doğal, akıllı ve yardımcı ol.

Normal sohbet sorularını cevapla.

Kullanıcı görsel gönderirse gerçekten analiz et.

Özellikle kıyafet, kombin, renk uyumu, stil,
gardırop, ürün, mekan, nesne ve ekran görüntülerini
analiz edebilirsin.

Kullanıcı kombin sorarsa:

- parçaları belirle
- renkleri değerlendir
- uyumu değerlendir
- eksikleri söyle
- alternatif öner
- istenirse 10 üzerinden puan ver

Görmediğin bir görsel hakkında görmüş gibi konuşma.

Kısa sorulara gereksiz uzun cevap verme.

"""


    history_text = ""


    if history:

        history_text = (
            "\n\nÖNCEKİ SOHBET:\n"
        )


        for item in history:

            if item["text"]:

                if item["role"] == "user":

                    history_text += (
                        "Kullanıcı: "
                        + item["text"]
                        + "\n"
                    )

                else:

                    history_text += (
                        "Kenz: "
                        + item["text"]
                        + "\n"
                    )


    full_prompt = (

        system_prompt

        + history_text

        + "\n\nYENİ KULLANICI MESAJI:\n"

        + user_text

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

                    prompt=
                        full_prompt,

                    image=
                        image_bytes

                )


                # Router provider bilgisini session'a yazdıysa
                provider = (
                    st.session_state.get(
                        "last_provider"
                    )
                )


                st.markdown(
                    answer
                )


                # ====================================================
                # AI CEVABINI SUPABASE'E KAYDET
                # ====================================================

                add_message(

                    conversation_id=
                        st.session_state.conversation_id,

                    role="assistant",

                    content=
                        answer,

                    provider=
                        provider

                )


                # ====================================================
                # SESSION'A EKLE
                # ====================================================

                st.session_state.messages.append({

                    "role":
                        "user",

                    "content":
                        user_text,

                    "image_url":
                        image_url

                })


                st.session_state.messages.append({

                    "role":
                        "assistant",

                    "content":
                        answer,

                    "image_url":
                        None,

                    "provider":
                        provider

                })


                # ====================================================
                # BAŞLIK OLUŞTUR
                # ====================================================

                conversations = get_conversations()


                current = None


                for conversation in conversations:

                    if (
                        conversation["id"]
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

                        title = user_text[:40]

                        update_conversation_title(

                            st.session_state.conversation_id,

                            title

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
# ALT
# ============================================================

st.divider()

st.caption(
    "Kenz Asistan • Gemini → OpenAI → OpenRouter"
)
