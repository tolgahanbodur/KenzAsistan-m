import streamlit as st
from google import genai
from openai import OpenAI
import requests


# ============================================================
# API KEY'LER
# ============================================================

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "")


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
# GEMINI
# ============================================================

def ask_gemini(prompt, image=None):

    if not gemini_client:
        raise Exception("Gemini API key bulunamadı.")

    contents = [prompt]

    if image is not None:
        contents.append(image)

    response = gemini_client.models.generate_content(
        model="gemini-3.7-flash",
        contents=contents
    )

    if not response.text:
        raise Exception("Gemini boş cevap verdi.")

    return response.text


# ============================================================
# OPENAI
# ============================================================

def ask_openai(prompt, image=None):

    if not openai_client:
        raise Exception("OpenAI API key bulunamadı.")

    content = []

    content.append({
        "type": "input_text",
        "text": prompt
    })

    if image is not None:

        import base64
        import io

        image_bytes = image

        if hasattr(image, "getvalue"):
            image_bytes = image.getvalue()

        base64_image = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        content.append({
            "type": "input_image",
            "image_url": (
                f"data:image/jpeg;base64,{base64_image}"
            )
        })

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
        raise Exception("OpenAI boş cevap verdi.")

    return response.output_text


# ============================================================
# OPENROUTER
# ============================================================

def ask_openrouter(prompt, image=None):

    if not OPENROUTER_API_KEY:
        raise Exception(
            "OpenRouter API key bulunamadı."
        )

    import base64

    content = []

    content.append({
        "type": "text",
        "text": prompt
    })

    if image is not None:

        image_bytes = image

        if hasattr(image, "getvalue"):
            image_bytes = image.getvalue()

        base64_image = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        content.append({
            "type": "image_url",
            "image_url": {
                "url": (
                    "data:image/jpeg;base64,"
                    + base64_image
                )
            }
        })

    response = requests.post(

        "https://openrouter.ai/api/v1/chat/completions",

        headers={
            "Authorization": (
                f"Bearer {OPENROUTER_API_KEY}"
            ),
            "Content-Type": "application/json"
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

        timeout=60
    )

    if response.status_code != 200:

        raise Exception(
            f"OpenRouter HTTP {response.status_code}: "
            f"{response.text}"
        )

    data = response.json()

    try:

        answer = data["choices"][0]["message"]["content"]

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
# ANA AI ROUTER
# ============================================================

def ask_ai(prompt, image=None):

    errors = []


    # --------------------------------------------------------
    # 1. GEMINI
    # --------------------------------------------------------

    try:

        return ask_gemini(
            prompt,
            image
        )

    except Exception as e:

        errors.append(
            "Gemini: " + str(e)
        )


    # --------------------------------------------------------
    # 2. OPENAI
    # --------------------------------------------------------

    try:

        return ask_openai(
            prompt,
            image
        )

    except Exception as e:

        errors.append(
            "OpenAI: " + str(e)
        )


    # --------------------------------------------------------
    # 3. OPENROUTER
    # --------------------------------------------------------

    try:

        return ask_openrouter(
            prompt,
            image
        )

    except Exception as e:

        errors.append(
            "OpenRouter: " + str(e)
        )


    # --------------------------------------------------------
    # HEPSİ BAŞARISIZ
    # --------------------------------------------------------

    raise Exception(
        "Hiçbir AI sağlayıcısından cevap alınamadı.\n\n"
        + "\n".join(errors)
    )
