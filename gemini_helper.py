import json
import mimetypes
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg
import streamlit as st

from google import genai
from google.genai import types

from openai import OpenAI

from pydantic import BaseModel


# ============================================================
# MODELS
# ============================================================

GEMINI_MODEL = "gemini-2.5-flash"

OPENAI_MODEL = "gpt-5-mini"


# ============================================================
# SECRETS
# ============================================================

def secret(
    name,
):

    value = os.environ.get(
        name
    )

    if value:
        return value

    try:

        return st.secrets[name]

    except Exception:

        return None


# ============================================================
# CLIENTS
# ============================================================

@st.cache_resource
def gemini_client():

    key = secret(
        "GEMINI_API_KEY"
    )

    if not key:

        raise ValueError(
            "GEMINI_API_KEY bulunamadı."
        )

    return genai.Client(
        api_key=key
    )


@st.cache_resource
def openai_client():

    key = secret(
        "OPENAI_API_KEY"
    )

    if not key:

        return None

    return OpenAI(
        api_key=key
    )


# ============================================================
# SYSTEM
# ============================================================

SYSTEM_PROMPT = """
Sen Kenz adında kişisel yapay zekâ asistanısın.

Kullanıcıyla Türkçe konuş.

Yeteneklerin:
- normal sohbet
- kişisel hafıza
- görsel analiz
- dosya analizi
- ses analizi
- video analizi
- gardırop
- kombin önerileri
- web araştırması
- medya linklerini dönüştürme

Kullanıcıya verilen hafıza ve gardırop bilgilerini gerektiğinde kullan.

Kullanıcıya ait bilgileri başka kullanıcılarla paylaşma.

Bir sorudan emin değilsen kesinmiş gibi konuşma.

Gerekli olduğunda ikinci bir AI görüşü alınabilir.
"""


# ============================================================
# MIME
# ============================================================

def get_mime(
    file_name,
    mime_type=None,
):

    if mime_type:
        return mime_type

    return (
        mimetypes.guess_type(
            file_name or ""
        )[0]
        or "application/octet-stream"
    )


# ============================================================
# GEMINI FILE
# ============================================================

def prepare_gemini_file(
    file_bytes,
    file_name,
    mime_type,
):

    if not file_bytes:

        return None

    mime_type = get_mime(
        file_name,
        mime_type,
    )


    # Images
    if mime_type.startswith(
        "image/"
    ):

        return types.Part.from_bytes(
            data=file_bytes,
            mime_type=mime_type,
        )


    # Other files
    suffix = Path(
        file_name or ""
    ).suffix

    temp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    )

    try:

        temp.write(
            file_bytes
        )

        temp.close()

        uploaded = (
            gemini_client()
            .files
            .upload(
                file=temp.name
            )
        )

        return uploaded

    finally:

        try:

            os.remove(
                temp.name
            )

        except Exception:
            pass


# ============================================================
# BUILD CONTEXT
# ============================================================

def build_context(
    history,
    memories,
    wardrobe,
):

    parts = [
        SYSTEM_PROMPT
    ]


    if memories:

        parts.append(
            "\nKULLANICI HAFIZASI:"
        )

        for item in memories[:50]:

            parts.append(
                "- "
                + item.get(
                    "memory",
                    "",
                )
            )


    if wardrobe:

        parts.append(
            "\nKULLANICI GARDIROBU:"
        )

        for item in wardrobe[:100]:

            parts.append(
                "- "
                + item.get(
                    "name",
                    "Kıyafet",
                )
                + " | "
                + item.get(
                    "category",
                    "",
                )
                + " | "
                + item.get(
                    "color",
                    "",
                )
                + " | "
                + item.get(
                    "description",
                    "",
                )
            )


    if history:

        parts.append(
            "\nSON KONUŞMALAR:"
        )

        for message in history[-20:]:

            role = message.get(
                "role",
                "",
            )

            content = message.get(
                "content",
                "",
            )

            if not content:
                continue

            parts.append(
                f"{role}: {content}"
            )


    return "\n".join(
        parts
    )


# ============================================================
# GEMINI FIRST OPINION
# ============================================================

def ask_gemini(
    user_text,
    file_bytes,
    file_name,
    mime_type,
    context,
):

    client = gemini_client()

    contents = [
        context,
        "\nYENİ MESAJ:\n"
        + (
            user_text
            or "Kullanıcı bir dosya gönderdi."
        ),
    ]

    if file_bytes:

        file = prepare_gemini_file(
            file_bytes,
            file_name,
            mime_type,
        )

        if file:

            contents.append(
                file
            )


    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            tools=[
                types.Tool(
                    google_search=types.GoogleSearch()
                )
            ]
        ),
    )

    return (
        response.text
        if response.text
        else ""
    )


# ============================================================
# SHOULD ASK OPENAI?
# ============================================================

def needs_second_opinion(
    user_text,
    gemini_answer,
):

    text = (
        (user_text or "")
        + " "
        + (gemini_answer or "")
    ).lower()


    manual = [
        "ikinci görüş",
        "chatgpt'ye sor",
        "openai'ye sor",
        "diğer ai'a sor",
        "başka ai'a sor",
        "emin misin",
    ]

    if any(
        phrase in text
        for phrase in manual
    ):

        return True


    uncertainty = [
        "emin değilim",
        "emin değilim.",
        "bunu doğrulayamıyorum",
        "yeterli bilgi yok",
        "kesin olarak söyleyemem",
        "bilmiyorum",
        "doğrulayamıyorum",
    ]

    if any(
        phrase in gemini_answer.lower()
        for phrase in uncertainty
    ):

        return True


    # Explicitly difficult technical/reasoning requests
    difficult = [
        "çok karmaşık",
        "derin analiz",
        "detaylı teknik analiz",
        "bu kodu düzelt",
        "kodu baştan incele",
        "bug bul",
        "hata neden",
    ]

    if any(
        phrase in text
        for phrase in difficult
    ):

        return True


    return False


# ============================================================
# OPENAI SECOND OPINION
# ============================================================

def ask_openai_second_opinion(
    user_text,
    gemini_answer,
    context,
    file_bytes=None,
    file_name=None,
    mime_type=None,
):

    client = openai_client()

    if client is None:

        return None


    prompt = f"""
Sen Kenz'in ikinci uzman AI danışmanısın.

Kullanıcı sorusu:

{user_text}

Kenz/Gemini'nin ilk cevabı:

{gemini_answer}

Bağlam:

{context}

Görevin:
1. Gemini cevabını kontrol et.
2. Hataları veya eksikleri bul.
3. Gerekirse daha doğru bir çözüm öner.
4. Gereksiz yere Gemini'ye katılma.
5. Türkçe cevap ver.

Kullanıcıya doğrudan cevap vermek zorunda değilsin.
Kenz bu sonucu kullanarak son cevabı oluşturacak.
"""


    content = [
        {
            "type": "input_text",
            "text": prompt,
        }
    ]


    # Image support
    if (
        file_bytes
        and mime_type
        and mime_type.startswith(
            "image/"
        )
    ):

        import base64

        encoded = base64.b64encode(
            file_bytes
        ).decode(
            "utf-8"
        )

        content.append(
            {
                "type": "input_image",
                "image_url":
                    f"data:{mime_type};base64,{encoded}",
            }
        )


    response = client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {
                "role": "user",
                "content": content,
            }
        ],
    )

    return response.output_text


# ============================================================
# FINAL SYNTHESIS
# ============================================================

def synthesize(
    user_text,
    gemini_answer,
    openai_answer,
    context,
):

    if not openai_answer:

        return gemini_answer


    client = gemini_client()


    prompt = f"""
Sen Kenz'sin.

Kullanıcının sorusu:

{user_text}

Senin ilk cevabın:

{gemini_answer}

İkinci AI'ın görüşü:

{openai_answer}

Bağlam:

{context}

Şimdi son cevabı oluştur.

Kurallar:
- İki görüşü karşılaştır.
- Yanlış bilgiyi ayıkla.
- Çelişki varsa en mantıklı olanı seç.
- Kullanıcıya ikinci AI'ın iç yazışmasını gösterme.
- "Gemini şöyle dedi, ChatGPT böyle dedi" şeklinde konuşma.
- Tek ve doğal bir Kenz cevabı ver.
- Türkçe konuş.
"""


    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            prompt
        ],
    )

    return (
        response.text
        if response.text
        else gemini_answer
    )


# ============================================================
# MAIN CHAT
# ============================================================

def chat_with_kenz(
    user_text,
    file_bytes=None,
    file_name=None,
    mime_type=None,
    history=None,
    memories=None,
    wardrobe=None,
):

    context = build_context(
        history or [],
        memories or [],
        wardrobe or [],
    )


    # --------------------------------------------------------
    # GEMINI
    # --------------------------------------------------------

    gemini_answer = ask_gemini(
        user_text,
        file_bytes,
        file_name,
        mime_type,
        context,
    )


    # --------------------------------------------------------
    # SECOND OPINION
    # --------------------------------------------------------

    if needs_second_opinion(
        user_text,
        gemini_answer,
    ):

        openai_answer = (
            ask_openai_second_opinion(
                user_text,
                gemini_answer,
                context,
                file_bytes,
                file_name,
                mime_type,
            )
        )

        if openai_answer:

            return synthesize(
                user_text,
                gemini_answer,
                openai_answer,
                context,
            )


    return gemini_answer


# ============================================================
# WARDROBE
# ============================================================

class WardrobeItem(BaseModel):

    name: str
    category: str
    color: str
    description: str


def extract_wardrobe_item(
    file_bytes,
    mime_type,
):

    client = gemini_client()

    image = types.Part.from_bytes(
        data=file_bytes,
        mime_type=mime_type or "image/jpeg",
    )


    prompt = """
Görseldeki kıyafeti analiz et.

JSON olarak cevap ver:

{
    "name": "kıyafet adı",
    "category": "kategori",
    "color": "ana renk",
    "description": "kısa açıklama"
}
"""


    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            image,
            prompt,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=WardrobeItem,
        ),
    )


    return json.loads(
        response.text
    )


# ============================================================
# MEDIA CONVERSION
# ============================================================

FORMAT_MIME = {

    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "flac": "audio/flac",
    "m4a": "audio/mp4",
    "aac": "audio/aac",
    "opus": "audio/opus",
    "ogg": "audio/ogg",

    "mp4": "video/mp4",
    "mkv": "video/x-matroska",
    "webm": "video/webm",
    "mov": "video/quicktime",
    "avi": "video/x-msvideo",

    "gif": "image/gif",
}


def get_ffmpeg():

    return imageio_ffmpeg.get_ffmpeg_exe()


# ============================================================
# DOWNLOAD
# ============================================================

def download_media(
    url,
    directory,
):

    from yt_dlp import YoutubeDL

    ffmpeg = get_ffmpeg()

    template = os.path.join(
        directory,
        "source.%(ext)s",
    )


    options = {

        "outtmpl": template,

        "format":
            "bestvideo+bestaudio/best",

        "merge_output_format": "mp4",

        "noplaylist": True,

        "quiet": True,

        "no_warnings": True,

        "ffmpeg_location": ffmpeg,

    }


    with YoutubeDL(
        options
    ) as ydl:

        info = ydl.extract_info(
            url,
            download=True,
        )

        filename = ydl.prepare_filename(
            info
        )


    if os.path.exists(
        filename
    ):

        return filename


    mp4 = os.path.join(
        directory,
        "source.mp4",
    )

    if os.path.exists(
        mp4
    ):

        return mp4


    files = list(
        Path(directory).glob(
            "source.*"
        )
    )

    if files:

        return str(
            files[0]
        )


    raise RuntimeError(
        "Medya indirilemedi."
    )


# ============================================================
# FFMPEG
# ============================================================

def convert_with_ffmpeg(
    source,
    destination,
    fmt,
):

    ffmpeg = get_ffmpeg()


    if fmt == "mp3":

        command = [
            ffmpeg,
            "-y",
            "-i",
            source,
            "-vn",
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "2",
            destination,
        ]


    elif fmt == "wav":

        command = [
            ffmpeg,
            "-y",
            "-i",
            source,
            "-vn",
            "-codec:a",
            "pcm_s16le",
            destination,
        ]


    elif fmt == "flac":

        command = [
            ffmpeg,
            "-y",
            "-i",
            source,
            "-vn",
            "-codec:a",
            "flac",
            destination,
        ]


    elif fmt == "m4a":

        command = [
            ffmpeg,
            "-y",
            "-i",
            source,
            "-vn",
            "-codec:a",
            "aac",
            "-b:a",
            "256k",
            destination,
        ]


    elif fmt == "aac":

        command = [
            ffmpeg,
            "-y",
            "-i",
            source,
            "-vn",
            "-codec:a",
            "aac",
            "-b:a",
            "256k",
            destination,
        ]


    elif fmt == "opus":

        command = [
            ffmpeg,
            "-y",
            "-i",
            source,
            "-vn",
            "-codec:a",
            "libopus",
            "-b:a",
            "160k",
            destination,
        ]


    elif fmt == "ogg":

        command = [
            ffmpeg,
            "-y",
            "-i",
            source,
            "-vn",
            "-codec:a",
            "libvorbis",
            "-q:a",
            "5",
            destination,
        ]


    elif fmt == "gif":

        command = [
            ffmpeg,
            "-y",
            "-i",
            source,
            "-vf",
            "fps=12,scale=720:-1",
            destination,
        ]


    else:

        command = [
            ffmpeg,
            "-y",
            "-i",
            source,
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-crf",
            "23",
            "-preset",
            "medium",
            destination,
        ]


    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


    if result.returncode != 0:

        raise RuntimeError(
            result.stderr[-4000:]
        )


# ============================================================
# URL CONVERTER
# ============================================================

def convert_media_url(
    url,
    requested_format,
):

    fmt = requested_format.lower().strip()

    if fmt not in FORMAT_MIME:

        raise ValueError(
            "Desteklenmeyen format."
        )


    workdir = tempfile.mkdtemp(
        prefix="kenz_"
    )


    try:

        source = download_media(
            url,
            workdir,
        )

        output = os.path.join(
            workdir,
            f"kenz.{fmt}",
        )

        convert_with_ffmpeg(
            source,
            output,
            fmt,
        )

        with open(
            output,
            "rb",
        ) as f:

            data = f.read()


        return {

            "bytes": data,

            "file_name":
                f"kenz.{fmt}",

            "mime_type":
                FORMAT_MIME[fmt],
        }


    finally:

        shutil.rmtree(
            workdir,
            ignore_errors=True,
        )
