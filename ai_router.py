import base64
import os
import tempfile
import time
import re

import requests
import streamlit as st

from google import genai
from openai import OpenAI


# ============================================================
# API KEYS
# ============================================================

def get_secret(name):
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""

    if not value:
        value = os.environ.get(name, "")

    return value


GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
OPENROUTER_API_KEY = get_secret("OPENROUTER_API_KEY")


# ============================================================
# CLIENTS
# ============================================================

gemini_client = None
openai_client = None


if GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(
            api_key=GEMINI_API_KEY
        )
    except Exception:
        gemini_client = None


if OPENAI_API_KEY:
    try:
        openai_client = OpenAI(
            api_key=OPENAI_API_KEY
        )
    except Exception:
        openai_client = None


# ============================================================
# RESPONSE CLEANER
# ============================================================

def clean_ai_response(answer):

    if answer is None:
        return ""

    if not isinstance(answer, str):
        answer = str(answer)

    answer = answer.strip()

    # Teknik safety çıktılarının kullanıcıya görünmesini engelle
    patterns = [
        r"User\s*Safety\s*:\s*safe",
        r"User\s*Safety\s*:\s*unsafe",
        r"User\s*Safety\s*:\s*[^\n]+",

        r"Safety\s*:\s*safe",
        r"Safety\s*:\s*unsafe",
        r"Safety\s*:\s*[^\n]+",

        r"Safety\s*Rating\s*:\s*[^\n]+",
        r"Safety\s*Result\s*:\s*[^\n]+",
    ]

    for pattern in patterns:
        answer = re.sub(
            pattern,
            "",
            answer,
            flags=re.IGNORECASE
        )

    answer = re.sub(
        r"\n{3,}",
        "\n\n",
        answer
    )

    return answer.strip()


# ============================================================
# FILE HELPERS
# ============================================================

def get_file_bytes(uploaded_file):

    if uploaded_file is None:
        return None

    if isinstance(uploaded_file, bytes):
        return uploaded_file

    if hasattr(uploaded_file, "getvalue"):
        try:
            return uploaded_file.getvalue()
        except Exception:
            return None

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

    if gemini_client is None:
        raise RuntimeError(
            "GEMINI_API_KEY bulunamadı veya Gemini istemcisi oluşturulamadı."
        )

    file_bytes = get_file_bytes(
        uploaded_file
    )

    # ========================================================
    # SADECE METİN
    # ========================================================

    if not file_bytes:

        response = (
            gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
        )

        answer = getattr(
            response,
            "text",
            None
        )

        answer = clean_ai_response(
            answer
        )

        if not answer:
            raise RuntimeError(
                "Gemini kullanıcıya gösterilebilir bir cevap üretmedi."
            )

        return answer


    # ========================================================
    # DOSYA
    # ========================================================

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

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp:

            temp.write(
                file_bytes
            )

            temp_path = temp.name

        uploaded = (
            gemini_client.files.upload(
                file=temp_path
            )
        )

        # ====================================================
        # VIDEO PROCESSING
        # ====================================================

        if mime_type.startswith("video/"):

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
                    raise RuntimeError(
                        "Gemini video dosyasını işleyemedi."
                    )

                time.sleep(2)

                uploaded = (
                    gemini_client.files.get(
                        name=uploaded.name
                    )
                )

        # ====================================================
        # MULTIMODAL
        # ====================================================

        response = (
            gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    uploaded,
                    prompt
                ]
            )
        )

        answer = getattr(
            response,
            "text",
            None
        )

        answer = clean_ai_response(
            answer
        )

        if not answer:
            raise RuntimeError(
                "Gemini medya için kullanıcıya gösterilebilir cevap üretmedi."
            )

        return answer

    finally:

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

    if openai_client is None:
        raise RuntimeError(
            "OPENAI_API_KEY bulunamadı veya OpenAI istemcisi oluşturulamadı."
        )

    content = [
        {
            "type": "input_text",
            "text": prompt
        }
    ]

    file_bytes = get_file_bytes(
        uploaded_file
    )

    if file_bytes:

        mime_type = get_mime_type(
            uploaded_file
        )

        # ====================================================
        # IMAGE
        # ====================================================

        if mime_type.startswith("image/"):

            encoded = (
                base64
                .b64encode(
                    file_bytes
                )
                .decode("utf-8")
            )

            content.append(
                {
                    "type": "input_image",
                    "image_url": (
                        f"data:{mime_type};"
                        f"base64,{encoded}"
                    )
                }
            )

        # ====================================================
        # OTHER FILE
        # ====================================================

        else:

            content.append(
                {
                    "type": "input_text",
                    "text": (
                        "\n\n"
                        "Kullanıcı bir medya dosyası yükledi.\n"
                        f"Dosya adı: {get_filename(uploaded_file)}\n"
                        f"Dosya türü: {mime_type}\n"
                        "Bu dosya doğrudan analiz edilemiyorsa "
                        "bunu dürüstçe belirt."
                    )
                }
            )

    response = (
        openai_client.responses.create(
            model="gpt-5-mini",
            input=[
                {
                    "role": "user",
                    "content": content
                }
            ]
        )
    )

    answer = getattr(
        response,
        "output_text",
        None
    )

    answer = clean_ai_response(
        answer
    )

    if not answer:
        raise RuntimeError(
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
        raise RuntimeError(
            "OPENROUTER_API_KEY bulunamadı."
        )

    content = [
        {
            "type": "text",
            "text": prompt
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

        # ====================================================
        # IMAGE
        # ====================================================

        if mime_type.startswith("image/"):

            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": (
                            f"data:{mime_type};"
                            f"base64,{encoded}"
                        )
                    }
                }
            )

        # ====================================================
        # AUDIO
        # ====================================================

        elif mime_type.startswith("audio/"):

            audio_format = (
                mime_type
                .split("/")
                [-1]
            )

            if audio_format == "mpeg":
                audio_format = "mp3"

            if audio_format == "x-m4a":
                audio_format = "m4a"

            content.append(
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": encoded,
                        "format": audio_format
                    }
                }
            )

        # ====================================================
        # VIDEO / OTHER
        # ====================================================

        else:

            content.append(
                {
                    "type": "text",
                    "text": (
                        "\n\n"
                        f"Eklenen dosya: "
                        f"{get_filename(uploaded_file)}\n"
                        f"MIME türü: {mime_type}"
                    )
                }
            )

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
                "Kenz Asistan"
        },

        json={
            "model": "openrouter/free",

            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ]
        },

        timeout=120
    )

    if response.status_code != 200:

        raise RuntimeError(
            "OpenRouter HTTP "
            + str(response.status_code)
            + ": "
            + response.text
        )

    try:

        data = response.json()

    except Exception:

        raise RuntimeError(
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

        raise RuntimeError(
            "OpenRouter cevap formatı geçersiz: "
            + str(data)
        )

    if isinstance(answer, list):

        parts = []

        for item in answer:

            if isinstance(item, dict):

                text = item.get(
                    "text"
                )

                if text:
                    parts.append(
                        text
                    )

            elif isinstance(item, str):

                parts.append(
                    item
                )

        answer = "\n".join(
            parts
        )

    answer = clean_ai_response(
        answer
    )

    if not answer:

        raise RuntimeError(
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

    # Eski app.py uyumluluğu
    if uploaded_file is None:
        uploaded_file = image

    errors = []

    # ========================================================
    # 1. GEMINI
    # ========================================================

    try:

        answer = ask_gemini(
            prompt,
            uploaded_file
        )

        st.session_state.last_provider = "Gemini"

        return clean_ai_response(
            answer
        )

    except Exception as e:

        errors.append(
            "Gemini → "
            + str(e)
        )

    # ========================================================
    # 2. OPENAI
    # ========================================================

    try:

        answer = ask_openai(
            prompt,
            uploaded_file
        )

        st.session_state.last_provider = "OpenAI"

        return clean_ai_response(
            answer
        )

    except Exception as e:

        errors.append(
            "OpenAI → "
            + str(e)
        )

    # ========================================================
    # 3. OPENROUTER
    # ========================================================

    try:

        answer = ask_openrouter(
            prompt,
            uploaded_file
        )

        st.session_state.last_provider = "OpenRouter"

        return clean_ai_response(
            answer
        )

    except Exception as e:

        errors.append(
            "OpenRouter → "
            + str(e)
        )

    # ========================================================
    # HEPSİ BAŞARISIZ
    # ========================================================

    raise RuntimeError(
        "Kenz hiçbir AI sağlayıcısından cevap alamadı.\n\n"
        + "\n".join(errors)
    )
