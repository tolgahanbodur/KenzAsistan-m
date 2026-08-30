import streamlit as st
import os
import time

import supabase_client as sc
import gemini_helper as gh


st.set_page_config(
    page_title="Kenz Asistan",
    page_icon="🤖",
    layout="centered"
)


# --------------------------------------------------
# AYARLAR
# --------------------------------------------------

def check_setup():
    keys = [
        "GEMINI_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY"
    ]

    missing = []

    for key in keys:
        value = os.environ.get(key)

        try:
            if not value:
                value = st.secrets.get(key)
        except Exception:
            pass

        if not value:
            missing.append(key)

    return len(missing) == 0, missing


is_setup, missing_keys = check_setup()


if not is_setup:

    st.title("🤖 Kenz Asistan")

    st.warning("Uygulamanın ayarları eksik.")

    st.write("Eksik ayarlar:")

    for key in missing_keys:
        st.code(key)

    st.info(
        "Streamlit Cloud → Settings → Secrets bölümünden "
        "API anahtarlarını ekleyin."
    )

    st.stop()


# --------------------------------------------------
# BAŞLIK
# --------------------------------------------------

st.title("🤖 Kenz Asistan")

st.caption(
    "Görselleri anlayabilen, kombinlerini değerlendirebilen "
    "ve seninle sohbet edebilen kişisel yapay zekâ asistanın."
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "assistant",
            "text": (
                "Merhaba 👋 Ben Kenz.\n\n"
                "Benimle normal şekilde sohbet edebilirsin. "
                "Ayrıca fotoğraf göndererek kombin, kıyafet veya "
                "başka görseller hakkında soru sorabilirsin."
            ),
            "image": None
        }
    ]


# --------------------------------------------------
# GEÇMİŞ MESAJLAR
# --------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message.get("image") is not None:
            st.image(
                message["image"],
                use_container_width=True
            )

        if message.get("text"):
            st.markdown(message["text"])


# --------------------------------------------------
# CHAT INPUT
# --------------------------------------------------

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


# --------------------------------------------------
# MESAJ GELDİ
# --------------------------------------------------

if prompt:

    user_text = prompt.text.strip()

    uploaded_files = prompt.files

    image_bytes = None

    if uploaded_files:

        uploaded_file = uploaded_files[0]

        image_bytes = uploaded_file.getvalue()


    # Kullanıcı mesajını kaydet

    st.session_state.messages.append(
        {
            "role": "user",
            "text": user_text,
            "image": image_bytes
        }
    )


    # Kullanıcı mesajını göster

    with st.chat_message("user"):

        if image_bytes:
            st.image(
                image_bytes,
                use_container_width=True
            )

        if user_text:
            st.markdown(user_text)


    # --------------------------------------------------
    # GEMINI
    # --------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("Kenz düşünüyor..."):

            try:

                history = st.session_state.messages[:-1]

                answer = gh.chat_with_kenz(
                    user_text=user_text,
                    image_bytes=image_bytes,
                    history=history
                )

                st.markdown(answer)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "text": answer,
                        "image": None
                    }
                )

            except Exception as e:

                error_message = (
                    "Bir hata oluştu:\n\n"
                    f"`{str(e)}`"
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "text": error_message,
                        "image": None
                    }
                )


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.header("🤖 Kenz")

    st.write(
        "Kişisel yapay zekâ asistanın."
    )

    st.divider()

    if st.button(
        "🗑️ Sohbeti Temizle",
        use_container_width=True
    ):

        st.session_state.messages = [
            {
                "role": "assistant",
                "text": (
                    "Sohbet temizlendi 👋 "
                    "Nasıl yardımcı olabilirim?"
                ),
                "image": None
            }
        ]

        st.rerun()

    st.divider()

    st.subheader("✨ Yapabileceklerim")

    st.write(
        """
        • Normal sohbet

        • Görsel analiz

        • Kombin değerlendirme

        • Kıyafet analizi

        • Renk uyumu

        • Stil önerileri

        • Gardırop önerileri
        """
    )
