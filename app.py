import streamlit as st
import os
import io
from PIL import Image
from google import genai


st.set_page_config(
    page_title="Kenz Asistan",
    page_icon="🤖",
    layout="centered"
)


def get_api_key():
    try:
        key = st.secrets["GEMINI_API_KEY"]
        if key:
            return str(key).strip()
    except Exception:
        pass

    key = os.environ.get("GEMINI_API_KEY")

    if key:
        return key.strip()

    return None


def get_client():
    api_key = get_api_key()

    if not api_key:
        raise Exception(
            "GEMINI_API_KEY bulunamadı. "
            "Streamlit Cloud > Settings > Secrets "
            "bölümünü kontrol et."
        )

    return genai.Client(api_key=api_key)


SYSTEM_PROMPT = """
Sen Kenz adında kişisel bir yapay zeka asistanısın.

Kullanıcıyla Türkçe konuş.

Samimi, doğal ve yardımcı ol.

Kullanıcı seninle normal şekilde sohbet edebilir.

Kullanıcı bir görsel gönderirse görseli analiz et.

Görsellerde özellikle:
- kıyafet
- kombin
- stil
- renk
- saç
- ürün
- nesne
- mekan
- ekran görüntüsü

analizi yapabilirsin.

Kullanıcı kombin sorarsa kıyafetleri, renkleri,
uyumu ve genel görünümü değerlendir.

Kullanıcı puan isterse 10 üzerinden puan ver.

Görseli görmediğin halde görmüş gibi davranma.

Cevaplarını doğal ve anlaşılır tut.
"""


if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "text": "Merhaba 👋 Ben Kenz. Nasıl yardımcı olabilirim?",
            "image": None
        }
    ]


st.title("🤖 Kenz Asistan")

st.caption(
    "Sohbet et, soru sor veya 📎 butonundan görsel gönder."
)


for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message.get("image") is not None:
            st.image(
                message["image"],
                use_container_width=True
            )

        if message.get("text"):
            st.markdown(message["text"])


def ask_kenz(user_text, image_bytes=None):

    client = get_client()

    contents = [SYSTEM_PROMPT]

    history = []

    for message in st.session_state.messages:

        text = message.get("text", "")

        if not text:
            continue

        if message["role"] == "user":
            history.append(
                "Kullanıcı: " + text
            )

        elif message["role"] == "assistant":
            history.append(
                "Kenz: " + text
            )

    if history:
        contents.append(
            "\nÖnceki konuşma:\n"
            + "\n".join(history)
        )

    if user_text:
        contents.append(
            "\nYeni mesaj:\n"
            + user_text
        )

    if image_bytes:

        image = Image.open(
            io.BytesIO(image_bytes)
        )

        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")

        contents.append(image)

    try:

        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=contents
        )

    except Exception as e:

        error = str(e)

        if (
            "API_KEY_INVALID" in error
            or "API key not valid" in error
        ):
            raise Exception(
                "Gemini API anahtarı geçersiz. "
                "Streamlit Cloud > Settings > Secrets "
                "bölümündeki GEMINI_API_KEY değerini kontrol et."
            )

        raise e

    if not response or not response.text:
        return "Şu anda cevap oluşturamadım."

    return response.text


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


if prompt:

    user_text = prompt.text.strip()

    image_bytes = None

    if prompt.files:

        uploaded_file = prompt.files[0]

        image_bytes = uploaded_file.getvalue()

    if not user_text and not image_bytes:

        st.warning(
            "Mesaj yaz veya görsel yükle."
        )

        st.stop()

    st.session_state.messages.append(
        {
            "role": "user",
            "text": user_text,
            "image": image_bytes
        }
    )

    with st.chat_message("user"):

        if image_bytes:
            st.image(
                image_bytes,
                use_container_width=True
            )

        if user_text:
            st.markdown(user_text)

    with st.chat_message("assistant"):

        with st.spinner("Kenz düşünüyor..."):

            try:

                answer = ask_kenz(
                    user_text=user_text,
                    image_bytes=image_bytes
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

                st.error(
                    "Bir hata oluştu:\n\n"
                    + str(e)
                )


with st.sidebar:

    st.header("🤖 Kenz")

    st.write(
        "Kişisel yapay zeka asistanın."
    )

    st.divider()

    st.subheader("Özellikler")

    st.write(
        """
💬 Normal sohbet

📎 Görsel gönderme

🖼️ Görsel analiz

👕 Kombin analizi

🎨 Renk uyumu

👔 Stil önerileri

📸 Fotoğraf analizi
"""
    )

    st.divider()

    if st.button(
        "🗑️ Sohbeti Temizle",
        use_container_width=True
    ):

        st.session_state.messages = [
            {
                "role": "assistant",
                "text": "Sohbet temizlendi 👋 Nasıl yardımcı olabilirim?",
                "image": None
            }
        ]

        st.rerun()
