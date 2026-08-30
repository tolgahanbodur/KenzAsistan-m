import streamlit as st
import io
import time

from PIL import Image

from ai_router import ask_ai


# ============================================================
# SAYFA AYARLARI
# ============================================================

st.set_page_config(
    page_title="Kenz Asistan",
    page_icon="🤖",
    layout="centered"
)


# ============================================================
# BAŞLIK
# ============================================================

st.title("🤖 Kenz Asistan")

st.caption(
    "Sohbet et, görsel gönder ve Kenz'den yardım al."
)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Merhaba 👋 Ben Kenz.\n\n"
                "Benimle normal şekilde sohbet edebilirsin. "
                "İstersen 📎 butonundan fotoğraf gönderip "
                "fotoğraf hakkında soru da sorabilirsin."
            ),
            "image": None
        }
    ]


if "last_provider" not in st.session_state:

    st.session_state.last_provider = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("🤖 Kenz")

    st.write(
        "Kişisel yapay zeka asistanın."
    )

    st.divider()

    st.subheader("✨ Özellikler")

    st.write(
        """
💬 Normal sohbet

📎 Görsel gönderme

🖼️ Görsel analiz

👕 Kombin değerlendirme

🎨 Renk uyumu

👔 Stil önerileri

📸 Fotoğraf analizi
"""
    )

    st.divider()

    if st.session_state.last_provider:

        st.caption(
            "Son kullanılan AI:"
        )

        st.info(
            st.session_state.last_provider
        )

    st.divider()

    if st.button(
        "🗑️ Sohbeti Temizle",
        use_container_width=True
    ):

        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Sohbet temizlendi 👋\n\n"
                    "Nasıl yardımcı olabilirim?"
                ),
                "image": None
            }
        ]

        st.session_state.last_provider = None

        st.rerun()


# ============================================================
# GEÇMİŞ MESAJLAR
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        image = message.get("image")

        if image is not None:

            try:

                st.image(
                    image,
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

    # --------------------------------------------------------
    # METİN
    # --------------------------------------------------------

    user_text = ""

    try:

        user_text = prompt.text.strip()

    except Exception:

        user_text = ""


    # --------------------------------------------------------
    # GÖRSEL
    # --------------------------------------------------------

    image_bytes = None

    try:

        if prompt.files:

            uploaded_file = prompt.files[0]

            image_bytes = uploaded_file.getvalue()

    except Exception as e:

        st.error(
            "Dosya okunamadı: "
            + str(e)
        )

        st.stop()


    # --------------------------------------------------------
    # GÖRSEL KONTROLÜ
    # --------------------------------------------------------

    if image_bytes:

        try:

            test_image = Image.open(
                io.BytesIO(image_bytes)
            )

            test_image.verify()

        except Exception:

            st.error(
                "Yüklediğin dosya geçerli bir "
                "görsel değil."
            )

            st.stop()


    # --------------------------------------------------------
    # BOŞ MESAJ KONTROLÜ
    # --------------------------------------------------------

    if (
        not user_text
        and not image_bytes
    ):

        st.warning(
            "Bir mesaj yaz veya görsel gönder."
        )

        st.stop()


    # ========================================================
    # KULLANICI MESAJINI SESSION'A EKLE
    # ========================================================

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_text,
            "image": image_bytes
        }
    )


    # ========================================================
    # KULLANICI MESAJINI GÖSTER
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
    # AI İÇİN PROMPT HAZIRLA
    # ========================================================

    conversation_history = []

    for message in st.session_state.messages[:-1]:

        role = message.get(
            "role",
            ""
        )

        content = message.get(
            "content",
            ""
        )

        if not content:

            continue

        if role == "user":

            conversation_history.append(
                "Kullanıcı: "
                + content
            )

        elif role == "assistant":

            conversation_history.append(
                "Kenz: "
                + content
            )


    if conversation_history:

        history_text = (
            "\n\nÖNCEKİ KONUŞMA:\n"
            + "\n".join(
                conversation_history
            )
        )

    else:

        history_text = ""


    # ========================================================
    # ANA PROMPT
    # ========================================================

    system_instruction = """
Sen Kenz adında kişisel bir yapay zeka asistanısın.

Kullanıcıyla Türkçe konuş.

Samimi, doğal ve yardımcı ol.

Kullanıcı seninle normal şekilde sohbet edebilir.

Kullanıcı bir görsel gönderirse görseli gerçekten analiz et.

Görselde kıyafet, kombin, saç, ürün, nesne,
mekan veya başka bir şey varsa açıklayabilirsin.

Kombin sorularında:

- kıyafetleri analiz et
- renkleri değerlendir
- uyumu değerlendir
- gerekirse eksikleri söyle
- alternatif öner
- puan istenirse 10 üzerinden puan ver

Görseli görmediğin halde görmüş gibi davranma.

Cevaplarını doğal ve anlaşılır tut.

Kullanıcı kısa cevap istiyorsa kısa cevap ver.
"""

    full_prompt = (
        system_instruction
        + history_text
        + "\n\nYENİ MESAJ:\n"
        + user_text
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
                    image=image_bytes
                )


                # ------------------------------------------------
                # CEVABI GÖSTER
                # ------------------------------------------------

                st.markdown(
                    answer
                )


                # ------------------------------------------------
                # SESSION'A KAYDET
                # ------------------------------------------------

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "image": None
                    }
                )


            except Exception as e:

                error_text = str(e)

                st.error(
                    "Kenz şu anda cevap veremedi."
                )

                with st.expander(
                    "Teknik hata"
                ):

                    st.code(
                        error_text
                    )


# ============================================================
# ALT BİLGİ
# ============================================================

st.divider()

st.caption(
    "Kenz Asistan • Gemini → OpenAI → OpenRouter"
)
