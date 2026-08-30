import base64
import os
import tempfile
import time

import requests
import streamlit as st

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

def get_file_bytes(uploaded_file):

    if uploaded_file is None:
        return None

    if isinstance(uploaded_file, bytes):
        return uploaded_file

    if hasattr(uploaded_file, "getvalue"):
        return uploaded_file.getvalue()

    return None


def get_mime_type(uploaded_file):

    if uploaded_file is None:
        return "application/octet-stream"

    mime = getattr(
        uploaded_file,
        "type",
        None
    )

    return mime or "application/octet-stream"


def get_filename(uploaded_file):

    if uploaded_file is None:
        return "media"

    return getattr(
        uploaded_file,
        "name",
        "media"
    )


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

    file_bytes = get_file_bytes(
        uploaded_file
    )

    # --------------------------------------------------------
    # SADECE METİN
    # --------------------------------------------------------

    if not file_bytes:

        response = (
            gemini_client
            .models
            .generate_content(
                model="gemini-3.7-flash",
                contents=prompt,
            )
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


    # --------------------------------------------------------
    # DOSYA BİLGİLERİ
    # --------------------------------------------------------

    mime_type = get_mime_type(
        uploaded_file
    )

    filename = get_filename(
        uploaded_file
    )

    extension = os.path.splitext(
        filename
    )[1]

    if not extension:
        extension = ".bin"


    temp_path = None

    try:

        # ----------------------------------------------------
        # GEÇİCİ DOSYA
        # ----------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp:

            temp.write(
                file_bytes
            )

            temp_path = temp.name


        # ----------------------------------------------------
        # GEMINI FILES API
        # ----------------------------------------------------

        uploaded = (
            gemini_client
            .files
            .upload(
                file=temp_path
            )
        )


        # ----------------------------------------------------
        # VIDEO İŞLENMESİNİ BEKLE
        # ----------------------------------------------------

        if mime_type.startswith(
            "video/"
        ):

            for _ in range(90):

                state = getattr(
                    uploaded,
                    "state",
                    None
                )

                state_name = getattr(
                    state,
                    "name",
                    ""
                )


                if state_name == "ACTIVE":
                    break


                if state_name == "FAILED":

                    raise Exception(
                        "Gemini video dosyasını "
                        "işleyemedi."
                    )


                time.sleep(2)


                uploaded = (
                    gemini_client
                    .files
                    .get(
                        name=uploaded.name
                    )
                )

            else:

                raise Exception(
                    "Video işleme zaman aşımına uğradı."
                )


        # ----------------------------------------------------
        # MULTIMODAL AI
        # ----------------------------------------------------

        response = (
            gemini_client
            .models
            .generate_content(
                model="gemini-3.7-flash",
                contents=[
                    uploaded,
                    prompt
                ],
            )
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


    finally:

        # ----------------------------------------------------
        # TEMP DOSYA SİL
        # ----------------------------------------------------

        if temp_path:

            try:
                os.remove(
                    temp_path
                )

            except Exception:
                pass


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


    content = [
        {
            "type": "input_text",
            "text": prompt,
        }
    ]


    file_bytes = get_file_bytes(
        uploaded_file
    )


    if file_bytes:

        mime_type = get_mime_type(
            uploaded_file
        )


        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

        if mime_type.startswith(
            "image/"
        ):

            encoded = (
                base64
                .b64encode(
                    file_bytes
                )
                .decode("utf-8")
            )


            content.append(
                {
                    "type":
                        "input_image",

                    "image_url":
                        (
                            f"data:{mime_type};"
                            f"base64,{encoded}"
                        )
                }
            )


        # ----------------------------------------------------
        # DİĞER DOSYALAR
        # ----------------------------------------------------

        else:

            content.append(
                {
                    "type":
                        "input_text",

                    "text":
                        (
                            "\n\n"
                            "Kullanıcı bir medya "
                            "dosyası ekledi.\n"
                            "Dosya adı: "
                            + get_filename(
                                uploaded_file
                            )
                            + "\n"
                            "Dosya türü: "
                            + mime_type
                            + "\n"
                        )
                }
            )


    # --------------------------------------------------------
    # OPENAI RESPONSE
    # --------------------------------------------------------

    response = (
        openai_client
        .responses
        .create(
            model="gpt-5-mini",

            input=[
                {
                    "role":
                        "user",

                    "content":
                        content
                }
            ],
        )
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


    content = [
        {
            "type":
                "text",

            "text":
                prompt,
        }
    ]


    file_bytes = get_file_bytes(
        uploaded_file
    )


    if file_bytes:

        mime_type = get_mime_type(
            uploaded_file
        )


        encoded = (
            base64
            .b64encode(
                file_bytes
            )
            .decode("utf-8")
        )


        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

        if mime_type.startswith(
            "image/"
        ):

            content.append(
                {
                    "type":
                        "image_url",

                    "image_url":
                        {
                            "url":
                                (
                                    f"data:{mime_type};"
                                    f"base64,{encoded}"
                                )
                        }
                }
            )


        # ----------------------------------------------------
        # AUDIO
        # ----------------------------------------------------

        elif mime_type.startswith(
            "audio/"
        ):

            content.append(
                {
                    "type":
                        "input_audio",

                    "input_audio":
                        {
                            "data":
                                encoded,

                            "format":
                                mime_type.split(
                                    "/"
                                )[-1]
                        }
                }
            )


        # ----------------------------------------------------
        # VIDEO / DİĞER
        # ----------------------------------------------------

        else:

            content.append(
                {
                    "type":
                        "text",

                    "text":
                        (
                            "\nEk medya dosyası:\n"
                            "Dosya: "
                            + get_filename(
                                uploaded_file
                            )
                            + "\n"
                            "MIME: "
                            + mime_type
                        )
                }
            )


    # --------------------------------------------------------
    # REQUEST
    # --------------------------------------------------------

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
# ANA AI ROUTER
# ============================================================

def ask_ai(
    prompt,
    uploaded_file=None,
    image=None
):

    # Eski kodlarla uyumluluk
    if uploaded_file is None:

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
    # HEPSİ BAŞARISIZ
    # ========================================================

    raise Exception(
        "Tüm AI sağlayıcıları başarısız oldu.\n\n"
        + "\n".join(
            errors
        )
    )
