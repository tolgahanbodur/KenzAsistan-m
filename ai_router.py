import base64
import io
import time

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
# GÖRSELİ HAZIRLA
# ============================================================

def prepare_image(image):

    if image is None:
        return None

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

    if isinstance(image, Image.Image):

        return image

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


    if image is not None:

        img = prepare_image(
            image
        )

        if img is not None:

            contents.append(
                img
            )


    contents.append(
        prompt
    )


    response = gemini_client.models.generate_content(

        model="gemini-3.7-flash",

        contents=contents
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
            "type": "input_text",
            "text": prompt
        }

    ]


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
                "Görsel formatı desteklenmiyor."
            )


        encoded = base64.b64encode(
            image_bytes
        ).decode(
            "utf-8"
        )


        content.append(

            {
                "type": "input_image",
                "image_url": (
                    "data:image/jpeg;base64,"
                    + encoded
                )
            }

        )


    response = openai_client.responses.create(

        model="gpt-5-mini",

        input=[

            {
                "role": "user",
                "content": content
            }

        ]
    )


    if not response.output_text:

        raise Exception(
            "OpenAI boş cevap verdi."
        )


    return response.output_text


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
            "text": prompt
        }

    ]


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
                "Görsel formatı desteklenmiyor."
            )


        encoded = base64.b64encode(
            image_bytes
        ).decode(
            "utf-8"
        )


        content.append(

            {
                "type": "image_url",
                "image_url": {

                    "url":
                        "data:image/jpeg;base64,"
                        + encoded

                }
            }

        )


    response = requests.post(

        "https://openrouter.ai/api/v1/chat/completions",

        headers={

            "Authorization":
                f"Bearer {OPENROUTER_API_KEY}",

            "Content-Type":
                "application/json",

            "HTTP-Referer":
                "https://kenzasistan-m-juobhsjgs4wqdjv7ez2nq9.streamlit.app",

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

            "OpenRouter "
            f"HTTP {response.status_code}: "
            f"{response.text}"

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
            "OpenRouter geçerli cevap döndürmedi."
        )


    if not answer:

        raise Exception(
            "OpenRouter boş cevap verdi."
        )


    return answer


# ============================================================
# MODEL HATASI MI?
# ============================================================

def should_fallback(error):

    error_text = str(
        error
    ).lower()


    fallback_errors = [

        "503",
        "429",
        "500",
        "502",
        "504",

        "unavailable",
        "overloaded",
        "rate limit",
        "rate_limit",
        "quota",
        "resource exhausted",
        "too many requests",
        "temporarily unavailable",
        "model not found",
        "not found",

        "api key not valid",
        "invalid api key",

    ]


    for text in fallback_errors:

        if text in error_text:

            return True


    return False


# ============================================================
# ANA ROUTER
# ============================================================

def ask_ai(
    prompt,
    image=None
):

    errors = []


    # ========================================================
    # 1 — GEMINI
    # ========================================================

    try:

        result = ask_gemini(
            prompt,
            image
        )

        return result


    except Exception as e:

        errors.append(
            "Gemini: "
            + str(e)
        )

        if not should_fallback(e):

            pass


    # ========================================================
    # 2 — OPENAI
    # ========================================================

    try:

        result = ask_openai(
            prompt,
            image
        )

        return result


    except Exception as e:

        errors.append(
            "OpenAI: "
            + str(e)
        )


    # ========================================================
    # 3 — OPENROUTER
    # ========================================================

    try:

        result = ask_openrouter(
            prompt,
            image
        )

        return result


    except Exception as e:

        errors.append(
            "OpenRouter: "
            + str(e)
        )


    # ========================================================
    # HİÇBİR MODEL ÇALIŞMADI
    # ========================================================

    raise Exception(

        "Tüm AI sağlayıcıları başarısız oldu.\n\n"
        + "\n".join(errors)

    )
