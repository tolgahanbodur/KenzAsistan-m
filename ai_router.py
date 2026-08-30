import base64
import io

import requests
import streamlit as st

from PIL import Image
from google import genai
from openai import OpenAI


# ============================================================
# API KEY
# ============================================================

GEMINI_API_KEY = st.secrets.get(
    "GEMINI_API_KEY",
    ""
)

OPENAI_API_KEY = st.secrets.get(
    "OPENAI_API_KEY",
    ""
)

OPENROUTER_API_KEY = st.secrets.get(
    "OPENROUTER_API_KEY",
    ""
)


# ============================================================
# CLIENT
# ============================================================

gemini_client = None
openai_client = None

if GEMINI_API_KEY:
    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )

if OPENAI_API_KEY:
    openai_client = OpenAI(
        api_key=OPENAI_API_KEY
    )


# ============================================================
# GÖRSELİ BYTES HALİNE GETİR
# ============================================================

def get_image_bytes(image):

    if image is None:
        return None

    if isinstance(image, bytes):
        return image

    if hasattr(image, "getvalue"):
        try:
            return image.getvalue()
        except Exception:
            return None

    if isinstance(image, Image.Image):

        buffer = io.BytesIO()

        image.save(
            buffer,
            format="JPEG"
        )

        return buffer.getvalue()

    return None


# ============================================================
# MIME TYPE
# ============================================================

def get_mime_type(image_bytes):

    if not image_bytes:
        return "image/jpeg"

    if image_bytes.startswith(b"\x89PNG"):
        return "image/png"

    if image_bytes.startswith(b"RIFF"):

        if b"WEBP" in image_bytes[:16]:
            return "image/webp"

    if image_bytes.startswith(b"\xff\xd8"):
        return "image/jpeg"

    return "image/jpeg"


# ============================================================
# GEMINI
# ============================================================

def ask_gemini(
    prompt,
    image=None
):

    if not gemini_client:
        raise Exception(
            "GEMINI_API_KEY bulunamadı."
        )

    contents = []

    image_bytes = get_image_bytes(
        image
    )

    if image_bytes:

        try:

            img = Image.open(
                io.BytesIO(
                    image_bytes
                )
            )

            img.load()

            contents.append(
                img
            )

        except Exception as e:

            raise Exception(
                "Gemini görseli okuyamadı: "
                + str(e)
            )

    contents.append(
        prompt
    )

    response = (
        gemini_client
        .models
        .generate_content(
            model="gemini-2.5-flash",
            contents=contents,
        )
    )

    if not response:
        raise Exception(
            "Gemini cevap vermedi."
        )

    answer = getattr(
        response,
        "text",
        None
    )

    if not answer:
        raise Exception(
            "Gemini boş cevap verdi."
        )

    return answer


# ============================================================
# OPENAI
# ============================================================

def ask_openai(
    prompt,
    image=None
):

    if not openai_client:
        raise Exception(
            "OPENAI_API_KEY bulunamadı."
        )

    content = [
        {
            "type": "input_text",
            "text": prompt,
        }
    ]

    image_bytes = get_image_bytes(
        image
    )

    if image_bytes:

        encoded = (
            base64.b64encode(
                image_bytes
            )
            .decode("utf-8")
        )

        mime_type = get_mime_type(
            image_bytes
        )

        content.append(
            {
                "type": "input_image",
                "image_url":
                    (
                        "data:"
                        + mime_type
                        + ";base64,"
                        + encoded
                    ),
            }
        )

    response = (
        openai_client
        .responses
        .create(
            model="gpt-5-mini",
            input=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
        )
    )

    if not response:
        raise Exception(
            "OpenAI cevap vermedi."
        )

    answer = getattr(
        response,
        "output_text",
        None
    )

    if not answer:
        raise Exception(
            "OpenAI boş cevap verdi."
        )

    return answer


# ============================================================
# OPENROUTER
# ============================================================

def ask_openrouter(
    prompt,
    image=None
):

    if not OPENROUTER_API_KEY:
        raise Exception(
            "OPENROUTER_API_KEY bulunamadı."
        )

    content = [
        {
            "type": "text",
            "text": prompt,
        }
    ]

    image_bytes = get_image_bytes(
        image
    )

    if image_bytes:

        encoded = (
            base64.b64encode(
                image_bytes
            )
            .decode("utf-8")
        )

        mime_type = get_mime_type(
            image_bytes
        )

        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url":
                        (
                            "data:"
                            + mime_type
                            + ";base64,"
                            + encoded
                        )
                },
            }
        )

    response = requests.post(

        "https://openrouter.ai/api/v1/chat/completions",

        headers={
            "Authorization":
                (
                    "Bearer "
                    + OPENROUTER_API_KEY
                ),

            "Content-Type":
                "application/json",

            "HTTP-Referer":
                (
                    "https://kenzasistan-m-"
                    "juobhsjgs4wqdjv7ez2nq9"
                    ".streamlit.app"
                ),

            "X-Title":
                "Kenz Asistan",
        },

        json={
            "model":
                "openrouter/free",

            "messages": [
                {
                    "role":
                        "user",

                    "content":
                        content,
                }
            ],
        },

        timeout=90,
    )

    if response.status_code != 200:

        raise Exception(
            "OpenRouter HTTP "
            + str(
                response.status_code
            )
            + ": "
            + response.text
        )

    try:

        data = response.json()

    except Exception:

        raise Exception(
            "OpenRouter geçersiz JSON döndürdü."
        )

    try:

        answer = (
            data
            ["choices"]
            [0]
            ["message"]
            ["content"]
        )

    except Exception:

        raise Exception(
            "OpenRouter cevap formatı geçersiz."
        )

    if not answer:
        raise Exception(
            "OpenRouter boş cevap verdi."
        )

    return answer


# ============================================================
# ANA ROUTER
# ============================================================

def ask_ai(
    prompt,
    image=None
):

    errors = []


    # ========================================================
    # 1 - GEMINI
    # ========================================================

    try:

        answer = ask_gemini(
            prompt=prompt,
            image=image
        )

        st.session_state.last_provider = "Gemini"

        return answer

    except Exception as e:

        errors.append(
            "Gemini: "
            + str(e)
        )


    # ========================================================
    # 2 - OPENAI
    # ========================================================

    try:

        answer = ask_openai(
            prompt=prompt,
            image=image
        )

        st.session_state.last_provider = "OpenAI"

        return answer

    except Exception as e:

        errors.append(
            "OpenAI: "
            + str(e)
        )


    # ========================================================
    # 3 - OPENROUTER
    # ========================================================

    try:

        answer = ask_openrouter(
            prompt=prompt,
            image=image
        )

        st.session_state.last_provider = "OpenRouter"

        return answer

    except Exception as e:

        errors.append(
            "OpenRouter: "
            + str(e)
        )


    # ========================================================
    # HEPSİ BAŞARISIZ
    # ========================================================

    raise Exception(
        "Tüm AI sağlayıcıları başarısız oldu.\n\n"
        + "\n".join(errors)
    )
