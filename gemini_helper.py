import io
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
from PIL import Image
from google import genai
from google.genai import types
from pydantic import BaseModel


# ============================================================
# CONFIG
# ============================================================

MODEL = "gemini-3.7-flash"


# ============================================================
# API KEY
# ============================================================

def get_api_key():

    key = os.environ.get(
        "GEMINI_API_KEY"
    )

    if key:
        return key

    try:
        return st.secrets[
            "GEMINI_API_KEY"
        ]
    except Exception:
        return None


# ============================================================
# CLIENT
# ============================================================

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
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
Sen Kenz adında kişisel bir yapay zekâ asistanısın.

Kullanıcıyla Türkçe konuş.

Görevin:
- normal sohbet etmek
- soruları cevaplamak
- görselleri analiz etmek
- fotoğrafları yorumlamak
- kıyafet ve kombin analiz etmek
- gardırop konusunda yardımcı olmak
- PDF, belge, ses, video ve diğer dosyaları analiz etmek
- kullanıcının kişisel hafızasını kullanmak

Kullanıcıya ait hafıza aşağıda verilen bilgilerle sınırlıdır.

Önemli kurallar:

1. Görmediğin bir dosyayı görmüş gibi davranma.
2. Kullanıcının verdiği dosya ve mesajı birlikte değerlendir.
3. Kullanıcı açıkça istemedikçe gereksiz uzun cevap verme.
4. Türkçe cevap ver.
5. Samimi ama doğal konuş.
6. Hafızadaki bilgileri cevap verirken uygun olduğunda kullan.
7. Kullanıcının gardırobunu biliyorsan kombin önerilerini buna göre yap.
8. Kullanıcı "bunu hatırla" dediğinde uygulama bunu ayrıca hafızaya kaydeder.
9. Kullanıcıya ait bilgileri başka kullanıcılarla paylaşma.
"""


# ============================================================
# MIME
# ============================================================

def safe_mime(
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
# FILE PART
# ============================================================

def make_file_part(
    file_bytes,
    mime_type,
):

    return types.Part.from_bytes(
        data=file_bytes,
        mime_type=mime_type,
    )


# ============================================================
# FILE CONTENT
# ============================================================

def build_file_content(
    file_bytes,
    file_name,
    mime_type,
):

    if not file_bytes:
        return []

    mime_type = safe_mime(
        file_name,
        mime_type,
    )

    # Images can be passed directly.
    if mime_type.startswith(
        "image/"
    ):

        return [
            make_file_part(
                file_bytes,
                mime_type,
            )
        ]

    # For audio/video/documents use Gemini Files API.
    temp_path = None

    try:

        suffix = Path(
            file_name or ""
        ).suffix

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp:

            temp.write(
                file_bytes
            )

            temp_path = temp.name

        uploaded = get_client().files.upload(
            file=temp_path
        )

        return [
            uploaded
        ]

    finally:

        if temp_path:

            try:
                os.remove(
                    temp_path
                )
            except Exception:
                pass


# ============================================================
# CHAT
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

    client = get_client()

    contents = [
        SYSTEM_PROMPT
    ]


    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    if memories:

        memory_lines = []

        for item in memories[:50]:

            memory = item.get(
                "memory",
                "",
            )

            if memory:
                memory_lines.append(
                    f"- {memory}"
                )

        if memory_lines:

            contents.append(
                "\nKULLANICI HAFIZASI:\n"
                + "\n".join(
                    memory_lines
                )
            )


    # --------------------------------------------------------
    # WARDROBE
    # --------------------------------------------------------

    if wardrobe:

        wardrobe_lines = []

        for item in wardrobe[:100]:

            name = item.get(
                "name",
                "",
            )

            category = item.get(
                "category",
                "",
            )

            color = item.get(
                "color",
                "",
            )

            description = item.get(
                "description",
                "",
            )

            wardrobe_lines.append(
                f"- {name} | "
                f"{category} | "
                f"{color} | "
                f"{description}"
            )

        if wardrobe_lines:

            contents.append(
                "\nKULLANICI GARDIROBU:\n"
                + "\n".join(
                    wardrobe_lines
                )
            )


    # --------------------------------------------------------
    # HISTORY
    # --------------------------------------------------------

    if history:

        history_lines = []

        for message in history[-30:]:

            role = message.get(
                "role",
                "",
            )

            text = message.get(
                "content",
                "",
            )

            if not text:
                continue

            if role == "user":
                prefix = "Kullanıcı"
            else:
                prefix = "Kenz"

            history_lines.append(
                f"{prefix}: {text}"
            )

        if history_lines:

            contents.append(
                "\nÖNCEKİ KONUŞMA:\n"
                + "\n".join(
                    history_lines
                )
            )


    # --------------------------------------------------------
    # CURRENT MESSAGE
    # --------------------------------------------------------

    current_text = (
        user_text
        if user_text
        else
        "Kullanıcı bir dosya gönderdi."
    )

    contents.append(
        "\nYENİ KULLANICI MESAJI:\n"
        + current_text
    )


    # --------------------------------------------------------
    # FILE
    # --------------------------------------------------------

    if file_bytes:

        contents.extend(
            build_file_content(
                file_bytes,
                file_name,
                mime_type,
            )
        )


    # --------------------------------------------------------
    # WEB SEARCH
    # --------------------------------------------------------

    config = types.GenerateContentConfig(
        tools=[
            types.Tool(
                google_search=types.GoogleSearch()
            )
        ]
    )


    # --------------------------------------------------------
    # GENERATE
    # --------------------------------------------------------

    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=config,
    )


    if not response.text:

        return (
            "Üzgünüm, bu isteğe cevap "
            "oluşturamadım."
        )

    return response.text


# ============================================================
# WARDROBE MODEL
# ============================================================

class WardrobeItem(BaseModel):

    name: str
    category: str
    color: str
    description: str


# ============================================================
# WARDROBE EXTRACTION
# ============================================================

def extract_wardrobe_item(
    file_bytes,
    mime_type,
    user_text="",
):

    client = get_client()

    prompt = """
Bu görseldeki kıyafeti gardırop veritabanına
kaydetmek için analiz et.

Yalnızca JSON döndür:

{
  "name": "...",
  "category": "...",
  "color": "...",
  "description": "..."
}

category örnekleri:
gömlek, tişört, polo, pantolon, jean,
ceket, mont, hırka, ayakkabı, aksesuar,
şort, takım elbise, diğer

description kısa ama faydalı olsun.
"""

    contents = [
        make_file_part(
            file_bytes,
            mime_type or "image/jpeg",
        ),
        prompt,
    ]

    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=WardrobeItem,
        ),
    )

    try:

        data = json.loads(
            response.text
        )

        return data

    except Exception:

        return None


# ============================================================
# URL
# ============================================================

URL_RE = re.compile(
    r"https?://[^\s]+",
    re.IGNORECASE,
)


# ============================================================
# FORMAT MIME
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


# ============================================================
# FORMAT PARSER
# ============================================================

def normalize_format(
    requested_format,
):

    if not requested_format:
        return None

    fmt = (
        requested_format
        .lower()
        .strip()
        .replace(".", "")
    )

    allowed = set(
        FORMAT_MIME.keys()
    )

    return (
        fmt
        if fmt in allowed
        else None
    )


# ============================================================
# FFMPEG
# ============================================================

def get_ffmpeg():

    path = imageio_ffmpeg.get_ffmpeg_exe()

    if not path:
        raise RuntimeError(
            "FFmpeg bulunamadı."
        )

    return path


# ============================================================
# DOWNLOAD SOURCE
# ============================================================

def download_source(
    url,
    directory,
):

    from yt_dlp import YoutubeDL

    ffmpeg = get_ffmpeg()

    output_template = os.path.join(
        directory,
        "source.%(ext)s",
    )

    options = {

        "outtmpl": output_template,

        "format": (
            "bestvideo+bestaudio/"
            "best"
        ),

        "merge_output_format": "mp4",

        "noplaylist": True,

        "quiet": True,

        "no_warnings": True,

        "ffmpeg_location": ffmpeg,

        "restrictfilenames": True,
    }

    with YoutubeDL(
        options
    ) as ydl:

        info = ydl.extract_info(
            url,
            download=True,
        )

        prepared = (
            ydl.prepare_filename(
                info
            )
        )

    # yt-dlp can merge to mp4.
    possible = [
        prepared,
        os.path.join(
            directory,
            "source.mp4",
        ),
    ]

    for path in possible:

        if os.path.exists(path):

            return path

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
        "Kaynak medya dosyası bulunamadı."
    )


# ============================================================
# FFMPEG CONVERSION
# ============================================================

def ffmpeg_convert(
    input_path,
    output_path,
    requested_format,
):

    ffmpeg = get_ffmpeg()

    fmt = requested_format


    # --------------------------------------------------------
    # AUDIO
    # --------------------------------------------------------

    if fmt == "mp3":

        cmd = [
            ffmpeg,
            "-y",
            "-i",
            input_path,
            "-vn",
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "2",
            output_path,
        ]

    elif fmt == "wav":

        cmd = [
            ffmpeg,
            "-y",
            "-i",
            input_path,
            "-vn",
            "-codec:a",
            "pcm_s16le",
            output_path,
        ]

    elif fmt == "flac":

        cmd = [
            ffmpeg,
            "-y",
            "-i",
            input_path,
            "-vn",
            "-codec:a",
            "flac",
            output_path,
        ]

    elif fmt == "m4a":

        cmd = [
            ffmpeg,
            "-y",
            "-i",
            input_path,
            "-vn",
            "-codec:a",
            "aac",
            "-b:a",
            "256k",
            output_path,
        ]

    elif fmt == "aac":

        cmd = [
            ffmpeg,
            "-y",
            "-i",
            input_path,
            "-vn",
            "-codec:a",
            "aac",
            "-b:a",
            "256k",
            output_path,
        ]

    elif fmt == "opus":

        cmd = [
            ffmpeg,
            "-y",
            "-i",
            input_path,
            "-vn",
            "-codec:a",
            "libopus",
            "-b:a",
            "160k",
            output_path,
        ]

    elif fmt == "ogg":

        cmd = [
            ffmpeg,
            "-y",
            "-i",
            input_path,
            "-vn",
            "-codec:a",
            "libvorbis",
            "-q:a",
            "5",
            output_path,
        ]


    # --------------------------------------------------------
    # GIF
    # --------------------------------------------------------

    elif fmt == "gif":

        cmd = [
            ffmpeg,
            "-y",
            "-i",
            input_path,
            "-vf",
            "fps=12,scale=720:-1:flags=lanczos",
            output_path,
        ]


    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

    else:

        video_codec = (
            "libvpx-vp9"
            if fmt == "webm"
            else "libx264"
        )

        audio_codec = (
            "libopus"
            if fmt == "webm"
            else "aac"
        )

        cmd = [
            ffmpeg,
            "-y",
            "-i",
            input_path,
            "-c:v",
            video_codec,
            "-c:a",
            audio_codec,
            "-crf",
            "23",
            "-preset",
            "medium",
            output_path,
        ]


    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:

        raise RuntimeError(
            result.stderr[-4000:]
        )

    if not os.path.exists(
        output_path
    ):

        raise RuntimeError(
            "FFmpeg çıktı dosyası oluşturmadı."
        )


# ============================================================
# URL CONVERTER
# ============================================================

def convert_media_url(
    url,
    requested_format,
):

    requested_format = normalize_format(
        requested_format
    )

    if not requested_format:

        raise ValueError(
            "Desteklenmeyen format."
        )


    # --------------------------------------------------------
    # CLEAN URL
    # --------------------------------------------------------

    url = url.strip()

    if not URL_RE.match(url):

        raise ValueError(
            "Geçerli bir URL değil."
        )


    # --------------------------------------------------------
    # TEMP DIRECTORY
    # --------------------------------------------------------

    workdir = tempfile.mkdtemp(
        prefix="kenz_media_"
    )

    try:

        source = download_source(
            url,
            workdir,
        )

        output = os.path.join(
            workdir,
            f"kenz_output.{requested_format}",
        )

        ffmpeg_convert(
            source,
            output,
            requested_format,
        )

        with open(
            output,
            "rb",
        ) as f:

            data = f.read()

        return {
            "bytes": data,
            "file_name": (
                f"kenz_output."
                f"{requested_format}"
            ),
            "mime_type": FORMAT_MIME[
                requested_format
            ],
        }

    finally:

        shutil.rmtree(
            workdir,
            ignore_errors=True,
        )
