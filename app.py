import base64
import io
import os
import tempfile

import requests
import streamlit as st

from PIL import Image
from google import genai
from openai import OpenAI


# ============================================================
# API KEYS
# ============================================================

GEMINI_API_KEY = st.secrets.get(
    "GEMINI_API_KEY",
    os.environ.get("GEMINI_API_KEY", "")
)

OPENAI_API_KEY = st.secrets.get(
    "OPENAI_API_KEY",
    os.environ.get("OPENAI_API_KEY", "")
)

OPENROUTER_API_KEY = st.secrets.get(
    "OPENROUTER_API_KEY",
    os.environ.get("OPENROUTER_API_KEY", "")
)


# ============================================================
# CLIENTS
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
# FILE HELPERS
# ============================================================

def get_file_data(uploaded_file):

    if uploaded_file is None:
        return None, None, None

    # --------------------------------------------------------
    # Yeni app.py'den gelen dictionary
    # --------------------------------------------------------

    if isinstance(uploaded_file, dict):

        file_bytes = uploaded_file.get(
            "bytes"
        )

        file_name = uploaded_file.get(
            "name",
            "file"
        )

        file_type = uploaded_file.get(
            "type",
            "application/octet-stream"
        )

        return (
            file_bytes,
            file_name,
            file_type
        )


    # --------------------------------------------------------
    # Streamlit UploadedFile
    # --------------------------------------------------------

    if hasattr(
        uploaded_file,
        "getvalue"
    ):

        file_bytes = uploaded_file.getvalue()

        file_name = getattr(
            uploaded_file,
            "name",
            "file"
        )

        file_type = getattr(
            uploaded_file,
            "type",
            "application/octet-stream"
        )

        return (
            file_bytes,
            file_name,
            file_type
        )


    # --------------------------------------------------------
    # Bytes
    # --------------------------------------------------------

    if isinstance(
        uploaded_file,
        bytes
    ):

        return (
            uploaded_file,
            "file",
            "application/octet-stream"
        )


    return None, None, None


# ============================================================
# IMAGE BYTES
# ============================================================

def get_image_bytes(
    file_bytes
):

    if not file_bytes:
        return None

    try:

        image = Image.open(
            io.BytesIO(file_bytes)
        )

        # Gemini/PIL uyumluluğu
        if image.mode not in (
            "RGB",
            "RGBA"
        ):

            image = image.convert(
                "RGB"
            )

        buffer = io.BytesIO()

        image.save(
            buffer,
            format="JPEG"
        )

        return buffer.getvalue()

    except Exception:

        return None


# ============================================================
# GEMINI
# ============================================================

def ask_gemini(
    prompt,
    uploaded_file=None
):

    if not gemini_client:

        raise Exception(
            "GEMINI_API_KEY bulunamadı."
        )


    file_bytes, file_name, file_type = (
        get_file_data(
            uploaded_file
        )
    )


    contents = []


    # ========================================================
    # IMAGE
    # ========================================================

    if (
        file_bytes
        and file_type
        and file_type.startswith(
            "image/"
        )
    ):

        image_bytes = get_image_bytes(
            file_bytes
        )

        if image_bytes:

            image = Image.open(
                io.BytesIO(
                    image_bytes
                )
            )

            contents.append(
                image
            )


    # ========================================================
    # VIDEO / AUDIO
    # ========================================================

    elif (
        file_bytes
        and file_type
        and (
            file_type.startswith("video/")
            or file_type.startswith("audio/")
        )
    ):

        suffix = ""

        if file_name and "." in file_name:

            suffix = (
                "."
                + file_name
                .split(".")[-1]
                .lower()
            )


        temp_path = None


        try:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix
            ) as temp_file:

                temp_file.write(
                    file_bytes
                )

                temp_path = temp_file.name


            uploaded = (
                gemini_client
                .files
                .upload(
                    file=temp_path
                )
            )


            contents.append(
                uploaded
            )


        finally:

            if temp_path:

                try:

                    os.remove(
                        temp_path
                    )

                except Exception:

                    pass


    # ========================================================
    # PROMPT
    # ========================================================

    contents.append(
        prompt
    )


    # ========================================================
    # REQUEST
    # ========================================================

    response = (
        gemini_client
        .models
        .generate_content(
            model="gemini-3.6-flash",
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
    uploaded_file=None
):

    if not openai_client:

        raise Exception(
            "OPENAI_API_KEY bulunamadı."
        )


    file_bytes, file_name, file_type = (
        get_file_data(
            uploaded_file
        )
    )


    content = []


    # ========================================================
    # TEXT
    # ========================================================

    content.append(
        {
            "type": "input_text",
            "text": prompt,
        }
    )


    # ========================================================
    # IMAGE
    # ========================================================

    if (
        file_bytes
        and file_type
        and file_type.startswith(
            "image/"
        )
    ):

        encoded = base64.b64encode(
            file_bytes
        ).decode(
            "utf-8"
        )


        content.append(
            {
                "type": "input_image",

                "image_url":
                    (
                        "data:"
                        + file_type
                        + ";base64,"
                        + encoded
                    ),
            }
        )


    # ========================================================
    # REQUEST
    # ========================================================

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
    uploaded_file=None
):

    if not OPENROUTER_API_KEY:

        raise Exception(
            "OPENROUTER_API_KEY bulunamadı."
        )


    file_bytes, file_name, file_type = (
        get_file_data(
            uploaded_file
        )
    )


    content = []


    # ========================================================
    # TEXT
    # ========================================================

    content.append(
        {
            "type": "text",
            "text": prompt,
        }
    )


    # ========================================================
    # IMAGE
    # ========================================================

    if (
        file_bytes
        and file_type
        and file_type.startswith(
            "image/"
        )
    ):

        encoded = base64.b64encode(
            file_bytes
        ).decode(
            "utf-8"
        )


        content.append(
            {
                "type": "image_url",

                "image_url":
                    {
                        "url":
                            (
                                "data:"
                                + file_type
                                + ";base64,"
                                + encoded
                            )
                    },
            }
        )


    # ========================================================
    # REQUEST
    # ========================================================

    response = requests.post(

        "https://openrouter.ai/api/v1/chat/completions",

        headers={

            "Authorization":
                "Bearer "
                + OPENROUTER_API_KEY,

            "Content-Type":
                "application/json",

            "HTTP-Referer":
                "https://kenzasistan-m-juobhsjgs4wqdjv7ez2nq9.streamlit.app",

            "X-Title":
                "Kenz Asistan",
        },

        json={

            "model":
                "openrouter/free",

            "messages":
                [
                    {
                        "role":
                            "user",

                        "content":
                            content,
                    }
                ],
        },

        timeout=120,
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
# MAIN ROUTER
# ============================================================

def ask_ai(
    prompt,
    uploaded_file=None,
    image=None
):

    # --------------------------------------------------------
    # GERİYE DÖNÜK UYUMLULUK
    # --------------------------------------------------------

    if uploaded_file is None and image is not None:

        uploaded_file = image


    errors = []


    # ========================================================
    # 1 — GEMINI
    # ========================================================

    try:

        answer = ask_gemini(
            prompt,
            uploaded_file
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
    # 2 — OPENAI
    # ========================================================

    try:

        answer = ask_openai(
            prompt,
            uploaded_file
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
    # 3 — OPENROUTER
    # ========================================================

    try:

        answer = ask_openrouter(
            prompt,
            uploaded_file
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
    # ALL FAILED
    # ========================================================

    raise Exception(
        "Tüm AI sağlayıcıları başarısız oldu.\n\n"
        + "\n".join(
            errors
        )
    )
