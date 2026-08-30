import os
import io

from PIL import Image
import streamlit as st

from google import genai


# --------------------------------------------------
# API
# --------------------------------------------------

def get_api_key():

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:

        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass

    return api_key


def get_client():

    api_key = get_api_key()

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY bulunamadı."
        )

    return genai.Client(
        api_key=api_key
    )


# --------------------------------------------------
# KENZ SYSTEM PROMPT
# --------------------------------------------------

SYSTEM_PROMPT = """
Sen Kenz adında kişisel bir yapay zekâ asistanısın.

Kullanıcıyla Türkçe konuş.

Samimi, doğal, akıllı ve yardımcı ol.

Kullanıcı sana normal sorular sorabilir.
Bu sorulara normal bir yapay zekâ asistanı gibi cevap ver.

Kullanıcı görsel gönderirse görseli gerçekten analiz et.

Özellikle:

- kıyafet
- kombin
- renk uyumu
- stil
- gardırop
- görünüm
- ürün
- mekan
- nesne
- ekran görüntüsü

gibi görselleri analiz edebilirsin.

Kullanıcı kombin hakkında soru sorarsa:

1. Görseldeki parçaları belirle.
2. Renkleri analiz et.
3. Parçaların birbirleriyle uyumunu değerlendir.
4. Kullanıcının sorusuna doğrudan cevap ver.
5. Gerekiyorsa alternatif öner.
6. Kullanıcı puan isterse 10 üzerinden puan ver.

Cevapların gereksiz derecede uzun olmasın.

Kullanıcı açıkça detay istemediği sürece kısa,
net ve doğal cevaplar ver.

Asla görseli görmediğin halde görmüş gibi davranma.
"""


# --------------------------------------------------
# CHAT
# --------------------------------------------------

def chat_with_kenz(
    user_text,
    image_bytes=None,
    history=None
):

    client = get_client()

    contents = [
        SYSTEM_PROMPT
    ]


    # --------------------------------------------------
    # GEÇMİŞ
    # --------------------------------------------------

    if history:

        for message in history:

            role = message.get("role")

            text = message.get("text", "")

            if role == "user":

                if text:
                    contents.append(
                        f"Kullanıcı: {text}"
                    )

            elif role == "assistant":

                if text:
                    contents.append(
                        f"Kenz: {text}"
                    )


    # --------------------------------------------------
    # GÜNCEL MESAJ
    # --------------------------------------------------

    if user_text:

        contents.append(
            f"Kullanıcı: {user_text}"
        )

    else:

        contents.append(
            "Kullanıcı bir görsel gönderdi."
        )


    # --------------------------------------------------
    # GÖRSEL
    # --------------------------------------------------

    if image_bytes:

        image = Image.open(
            io.BytesIO(image_bytes)
        )

        contents.append(image)


    # --------------------------------------------------
    # GEMINI
    # --------------------------------------------------

    response = client.models.generate_content(
        model="gemini-3.7-flash",
        contents=contents
    )


    if not response.text:

        return "Üzgünüm, bu isteğe cevap oluşturamadım."

    return response.text
