import base64
import io

import streamlit as st
import requests

from PIL import Image
from google import genai
from openai import OpenAI


# ============================================================
# API ANAHTARLARI
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
# CLIENT'LAR
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
# GÖRSEL HAZIRLAMA
# ============================================================

def prepare_image(image):

    if image is None:
        return None

    try:

        if isinstance(image, bytes):

            return Image.open(
                io.BytesIO(image)
            )

        if hasattr(image, "getvalue"):

            return Image.open(
                io.BytesIO(
                    image.getvalue()
                )
            )

        if isinstance(
            image,
            Image.Image
        ):

            return image

    except Exception as e:

        raise Exception(
            f"Görsel işlenemedi: {e}"
        )

    return None


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


    # Görsel varsa ekle
    if image is not None:

        img = prepare_image(
            image
        )

        if img is not None:

            contents.append(
                img
            )


    # Metni ekle
    contents.append(
        prompt
    )


    # Güncel Gemini Flash modeli
    response = gemini_client.models.generate_content(

        model="gemini-2.5-flash",

        contents=contents

    )


    if not response:

        raise Exception(
            "Gemini cevap vermedi."
        )


    if not response.text:

        raise Exception(
            "Gemini boş cevap verdi."
        )


    return response.text


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
            "type":
                "input_text",

            "text":
                prompt
        }

    ]


    # --------------------------------------------------------
    # GÖRSEL
    # --------------------------------------------------------

    if image is not None:

        if isinstance(
            image,
            bytes
        ):

            image_bytes = image

        elif hasattr(
            image,
            "getvalue"
        ):

            image_bytes = (
                image.getvalue()
            )

        else:

            raise Exception(
                "OpenAI görsel formatı desteklenmiyor."
            )


        encoded_image = (
            base64.b64encode(
                image_bytes
            ).decode(
                "utf-8"
            )
        )


        content.append({

            "type":
                "input_image",

            "image_url":
                (
                    "data:image/jpeg;base64,"
                    + encoded_image
                )

        })


    # --------------------------------------------------------
    # OPENAI İSTEĞİ
    # --------------------------------------------------------

    response = openai_client.responses.create(

        model="gpt-5-mini",

        input=[

            {

                "role":
                    "user",

                "content":
                    content

            }

        ]

    )


    if not response:

        raise Exception(
            "OpenAI cevap vermedi."
        )


    answer = response.output_text


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

            "type":
                "text",

            "text":
                prompt

        }

    ]


    # --------------------------------------------------------
    # GÖRSEL
    # --------------------------------------------------------

    if image is not None:

        if isinstance(
            image,
            bytes
        ):

            image_bytes = image

        elif hasattr(
            image,
            "getvalue"
        ):

            image_bytes = (
                image.getvalue()
            )

        else:

            raise Exception(
                "OpenRouter görsel formatı desteklenmiyor."
            )


        encoded_image = (
            base64.b64encode(
                image_bytes
            ).decode(
                "utf-8"
            )
        )


        content.append({

            "type":
                "image_url",

            "image_url": {

                "url":
                    (
                        "data:image/jpeg;base64,"
                        + encoded_image
                    )

            }

        })


    # --------------------------------------------------------
    # OPENROUTER
    # --------------------------------------------------------

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
                "Kenz Asistan"

        },

        json={

            "model":
                "openrouter/free",

            "messages": [

                {

                    "role":
                        "user",

                    "content":
                        content

                }

            ]

        },

        timeout=90

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


    data = response.json()


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
# HATA KONTROLÜ
# ============================================================

def should_fallback(
    error
):

    text = str(
        error
    ).lower()


    fallback_errors = [

        "400",
        "401",
        "402",
        "403",
        "408",
        "409",
        "429",
        "500",
        "502",
        "503",
        "504",

        "api key",
        "invalid",
        "quota",
        "rate limit",
        "rate_limit",
        "too many requests",
        "resource exhausted",
        "unavailable",
        "overloaded",
        "timeout",
        "timed out",
        "model not found",
        "not found"

    ]


    for error_text in fallback_errors:

        if error_text in text:

            return True


    return False


# ============================================================
# ANA AI ROUTER
# ============================================================

def ask_ai(
    prompt,
    image=None
):

    errors = []


    # ========================================================
    # 1. GEMINI
    # ========================================================

    try:

        answer = ask_gemini(

            prompt=prompt,

            image=image

        )


        st.session_state.last_provider = (
            "Gemini"
        )


        return answer


    except Exception as e:

        errors.append(
            "Gemini: "
            + str(e)
        )


    # ========================================================
    # 2. OPENAI
    # ========================================================

    try:

        answer = ask_openai(

            prompt=prompt,

            image=image

        )


        st.session_state.last_provider = (
            "OpenAI"
        )


        return answer


    except Exception as e:

        errors.append(
            "OpenAI: "
            + str(e)
        )


    # ========================================================
    # 3. OPENROUTER
    # ========================================================

    try:

        answer = ask_openrouter(

            prompt=prompt,

            image=image

        )


        st.session_state.last_provider = (
            "OpenRouter"
        )


        return answer


    except Exception as e:

        errors.append(
            "OpenRouter: "
            + str(e)
        )


    # ========================================================
    # HİÇBİR MODEL ÇALIŞMADI
    # ========================================================

    error_message = (
        "Tüm AI sağlayıcıları başarısız oldu.\n\n"
        + "\n".join(
            errors
        )
    )


    raise Exception(
        error_message
    )
