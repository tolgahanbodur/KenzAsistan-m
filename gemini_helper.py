import io
import os
import mimetypes
import tempfile
import subprocess

import streamlit as st

from PIL import Image
from google import genai

from ai_router import ask_ai


# ============================================================
# API
# ============================================================

def get_api_key():

    key = os.environ.get(
        "GEMINI_API_KEY"
    )

    if key:
        return key

    try:
        return st.secrets.get(
            "GEMINI_API_KEY",
            "",
        )
    except Exception:
        return ""


@st.cache_resource
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
# SYSTEM
# ============================================================

SYSTEM_PROMPT = """
Sen Kenz adında kişisel bir yapay zekâ asistanısın.

Kullanıcıyla Türkçe konuş.

Samimi, doğal, akıllı ve yardımcı ol.

Kullanıcının verdiği hafıza bilgilerini dikkate al.

Gardırop bilgilerini kullanarak kombin önerileri yap.

Kullanıcı fotoğraf gönderirse gerçekten analiz et.

Fotoğrafı görmediğin halde görmüş gibi davranma.

Kullanıcı bir dosya gönderirse dosyanın türüne göre
mümkün olduğunca yardımcı ol.

Kullanıcı bir bağlantı gönderirse bağlantının ne olduğunu
anlamaya çalış.

Kullanıcı açıkça format dönüştürme istediğinde converter
fonksiyonunun sonucunu kullan.

Zor veya belirsiz sorularda mevcut AI router üzerinden
ikinci AI görüşü kullanılabilir.

Cevapları gereksiz yere uzatma.

Kullanıcı ayrıntı istemedikçe kısa ve net cevap ver.
"""


# ============================================================
# CHAT
# ============================================================

def chat_with_kenz(
    user_text="",
    file_bytes=None,
    file_name=None,
    mime_type=None,
    history=None,
    memories=None,
    wardrobe=None,
):

    memories = memories or []
    wardrobe = wardrobe or []
    history = history or []


    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    memory_text = "\n".join(
        f"- {m.get('memory', '')}"
        for m in memories
        if m.get("memory")
    )

    # --------------------------------------------------------
    # WARDROBE
    # --------------------------------------------------------

    wardrobe_text = "\n".join(
        (
            f"- {w.get('name', 'Kıyafet')} | "
            f"{w.get('category', '')} | "
            f"{w.get('color', '')} | "
            f"{w.get('description', '')}"
        )
        for w in wardrobe
    )


    # --------------------------------------------------------
    # HISTORY
    # --------------------------------------------------------

    history_text = ""

    for message in history[-30:]:

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

        if role == "user":
            history_text += (
                f"Kullanıcı: {content}\n"
            )

        elif role == "assistant":
            history_text += (
                f"Kenz: {content}\n"
            )


    # --------------------------------------------------------
    # PROMPT
    # --------------------------------------------------------

    prompt = f"""
{SYSTEM_PROMPT}

KULLANICI HAFIZASI:
{memory_text or "Kayıtlı hafıza yok."}

KULLANICI GARDIROBU:
{wardrobe_text or "Kayıtlı gardırop yok."}

ÖNCEKİ KONUŞMA:
{history_text or "Önceki konuşma yok."}

YENİ KULLANICI MESAJI:
{user_text or "Kullanıcı bir dosya gönderdi."}
"""


    # --------------------------------------------------------
    # FILE
    # --------------------------------------------------------

    if file_bytes:

        if mime_type and mime_type.startswith(
            "image/"
        ):

            try:

                image = Image.open(
                    io.BytesIO(
                        file_bytes
                    )
                )

                prompt += (
                    "\n\nKullanıcı bir görsel gönderdi. "
                    "Görseli analiz et.\n"
                )

                return ask_ai(
                    prompt,
                    image=image,
                )

            except Exception:

                pass


    # --------------------------------------------------------
    # NORMAL / SECOND AI ROUTER
    # --------------------------------------------------------

    return ask_ai(
        prompt,
        image=None,
    )


# ============================================================
# WARDROBE AI
# ============================================================

def extract_wardrobe_item(
    file_bytes,
    mime_type,
):

    if not mime_type.startswith("image/"):

        raise ValueError(
            "Gardıroba eklemek için görsel yüklemelisin."
        )

    image = Image.open(
        io.BytesIO(file_bytes)
    )

    prompt = """
Bu görseldeki kıyafeti analiz et.

Sadece aşağıdaki JSON yapısında cevap ver:

{
  "name": "kıyafetin adı",
  "category": "kategori",
  "color": "ana renk",
  "description": "kısa açıklama"
}

Kategori örnekleri:
tişört, gömlek, polo, pantolon,
jean, ceket, hırka, mont,
ayakkabı, aksesuar, diğer.
"""

    client = get_client()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            prompt,
            image,
        ],
    )

    text = (
        response.text
        if response and response.text
        else ""
    )

    import json

    try:

        start = text.find("{")
        end = text.rfind("}") + 1

        return json.loads(
            text[start:end]
        )

    except Exception:

        return {
            "name": "Kıyafet",
            "category": "diğer",
            "color": "belirsiz",
            "description": text,
        }


# ============================================================
# MEDIA CONVERTER
# ============================================================

def convert_media_url(
    url,
    selected_format,
):

    """
    Genel URL → medya dönüştürme.

    yt-dlp bağlantının kaynağını anlamaya çalışır.
    FFmpeg varsa hedef formata dönüştürür.
    """

    try:
        import yt_dlp
    except ImportError:

        raise RuntimeError(
            "yt-dlp kurulu değil."
        )


    selected_format = (
        selected_format
        .lower()
        .strip()
    )


    with tempfile.TemporaryDirectory() as tmp:

        source = os.path.join(
            tmp,
            "source.%(ext)s",
        )

        output = os.path.join(
            tmp,
            f"converted.{selected_format}",
        )


        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        ydl_opts = {
            "outtmpl": source,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }


        # ----------------------------------------------------
        # AUDIO
        # ----------------------------------------------------

        audio_formats = [
            "mp3",
            "wav",
            "flac",
            "m4a",
            "aac",
            "opus",
            "ogg",
        ]


        if selected_format in audio_formats:

            ydl_opts["format"] = (
                "bestaudio/best"
            )


        else:

            ydl_opts["format"] = (
                "bestvideo+bestaudio/"
                "best"
            )


        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:

            ydl.download([url])


        # ----------------------------------------------------
        # FIND SOURCE
        # ----------------------------------------------------

        files = []

        for name in os.listdir(tmp):

            if name.startswith("source."):

                files.append(
                    os.path.join(
                        tmp,
                        name,
                    )
                )


        if not files:

            raise RuntimeError(
                "Kaynak medya indirilemedi."
            )


        source_file = files[0]


        # ----------------------------------------------------
        # CONVERT
        # ----------------------------------------------------

        command = [
            "ffmpeg",
            "-y",
            "-i",
            source_file,
        ]


        if selected_format == "mp3":

            command += [
                "-vn",
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "320k",
            ]

        elif selected_format == "wav":

            command += [
                "-vn",
                "-c:a",
                "pcm_s16le",
            ]

        elif selected_format == "flac":

            command += [
                "-vn",
                "-c:a",
                "flac",
            ]

        elif selected_format == "m4a":

            command += [
                "-vn",
                "-c:a",
                "aac",
                "-b:a",
                "256k",
            ]

        elif selected_format == "opus":

            command += [
                "-vn",
                "-c:a",
                "libopus",
                "-b:a",
                "192k",
            ]

        elif selected_format == "ogg":

            command += [
                "-vn",
                "-c:a",
                "libvorbis",
                "-q:a",
                "5",
            ]

        elif selected_format == "aac":

            command += [
                "-vn",
                "-c:a",
                "aac",
                "-b:a",
                "256k",
            ]

        else:

            command += [
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "-movflags",
                "+faststart",
            ]


        command.append(output)


        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,
        )


        if process.returncode != 0:

            raise RuntimeError(
                process.stderr.decode(
                    "utf-8",
                    errors="ignore",
                )[-2000:]
            )


        if not os.path.exists(output):

            raise RuntimeError(
                "Dönüştürülmüş dosya oluşturulamadı."
            )


        with open(
            output,
            "rb",
        ) as f:

            result_bytes = f.read()


    mime = (
        mimetypes.guess_type(
            f"file.{selected_format}"
        )[0]
        or "application/octet-stream"
    )


    return {
        "bytes": result_bytes,
        "file_name": (
            f"kenz_converted."
            f"{selected_format}"
        ),
        "mime_type": mime,
    }
