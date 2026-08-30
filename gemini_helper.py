import io
import os

import streamlit as st

from PIL import Image
from google import genai


# ============================================================
# API KEY
# ============================================================

def get_api_key():

    key = os.environ.get(
        "GEMINI_API_KEY"
    )


    if not key:

        key = st.secrets.get(
            "GEMINI_API_KEY",
            ""
        )


    return key


# ============================================================
# CLIENT
# ============================================================

def get_client():

    api_key = get_api_key()


    if not api_key:

        raise ValueError(
            "GEMINI_API_KEY bulunamadı."
        )


    return genai.Client(
        api_key=api_key
    )


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
Sen Kenz adında kişisel bir yapay zeka asistanısın.

Kullanıcıyla Türkçe konuş.

Samimi, doğal, akıllı ve yardımcı ol.

Kullanıcı sana normal sorular sorabilir.

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
6. Puan istenirse 10 üzerinden puan ver.

Asla görseli görmediğin halde görmüş gibi davranma.

Gereksiz derecede uzun cevap verme.

Kullanıcı detay istemediği sürece kısa,
net ve doğal cevaplar ver.
"""


# ============================================================
# CHAT
# ============================================================

def chat_with_kenz(
    user_text,
    image_bytes=None,
    history=None
):

    client = get_client()


    contents = [
        SYSTEM_PROMPT
    ]


    # --------------------------------------------------------
    # GEÇMİŞ
    # --------------------------------------------------------

    if history:

        for message in history:

            role = message.get(
                "role"
            )

            text = message.get(
                "text",
                ""
            )


            if not text:
                continue


            if role == "user":

                contents.append(
                    "Kullanıcı: "
                    + text
                )


            elif role == "assistant":

                contents.append(
                    "Kenz: "
                    + text
                )


    # --------------------------------------------------------
    # GÜNCEL MESAJ
    # --------------------------------------------------------

    if user_text:

        contents.append(
            "Kullanıcı: "
            + user_text
        )

    else:

        contents.append(
            "Kullanıcı bir görsel gönderdi."
        )


    # --------------------------------------------------------
    # GÖRSEL
    # --------------------------------------------------------

    if image_bytes:

        image = Image.open(
            io.BytesIO(
                image_bytes
            )
        )

        contents.append(
            image
        )


    # --------------------------------------------------------
    # GEMINI
    # --------------------------------------------------------

    response = (
        client
        .models
        .generate_content(
            model="gemini-2.5-flash",
            contents=contents,
        )
    )


    if not response:

        return (
            "Üzgünüm, şu anda cevap "
            "oluşturamadım."
        )


    if not response.text:

        return (
            "Üzgünüm, bu isteğe cevap "
            "oluşturamadım."
        )


    return response.text
