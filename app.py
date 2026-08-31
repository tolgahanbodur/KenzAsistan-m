import base64
import mimetypes
import os
import re
import streamlit as st

from gemini_helper import (
    chat_with_kenz,
    convert_media_url,
    extract_wardrobe_item,
)
from supabase_client import (
    get_user_client,
    get_messages,
    save_message,
    get_memories,
    save_memory,
    delete_memory,
    get_wardrobe,
    add_wardrobe_item,
)


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Kenz",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

#MainMenu {
    visibility: hidden;
}

header {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

.stApp {
    background:
        radial-gradient(
            circle at 50% -10%,
            rgba(99,102,241,.15),
            transparent 35%
        ),
        #09090b;
    color: #f4f4f5;
}

section[data-testid="stSidebar"] {
    background: #111113;
    border-right: 1px solid #27272a;
}

section[data-testid="stSidebar"] > div {
    padding-top: 1.5rem;
}

.kenz-logo {
    font-size: 30px;
    font-weight: 800;
    letter-spacing: -1px;
    margin-bottom: 3px;
}

.kenz-subtitle {
    color: #a1a1aa;
    font-size: 13px;
}

.user-badge {
    margin-top: 12px;
    padding: 8px 11px;
    border-radius: 10px;
    background: #18181b;
    border: 1px solid #27272a;
    color: #a1a1aa;
    font-size: 11px;
}

.main-title {
    text-align: center;
    font-size: 46px;
    font-weight: 800;
    letter-spacing: -2px;
    margin-top: 80px;
    margin-bottom: 8px;
}

.main-subtitle {
    text-align: center;
    color: #a1a1aa;
    font-size: 15px;
    margin-bottom: 45px;
}

[data-testid="stChatMessage"] {
    background: transparent;
}

[data-testid="stChatMessageContent"] {
    border-radius: 18px;
}

div[data-testid="stFileUploader"] {
    border-radius: 12px;
}

.stButton > button {
    border-radius: 11px;
    border: 1px solid #27272a;
    background: #18181b;
    color: #fafafa;
}

.stButton > button:hover {
    border-color: #52525b;
    background: #27272a;
}

div[data-testid="stChatInput"] {
    border-radius: 18px;
}

div[data-testid="stChatInput"] textarea {
    font-size: 15px;
}

.small-muted {
    color: #71717a;
    font-size: 12px;
}

.file-chip {
    padding: 8px 12px;
    background: #18181b;
    border: 1px solid #27272a;
    border-radius: 10px;
    margin: 5px 0;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SUPABASE / USER
# ============================================================

supabase, user_id = get_user_client()

if not supabase or not user_id:
    st.error(
        "Kenz başlatılamadı. Supabase bağlantısını ve "
        "anonymous sign-in ayarını kontrol et."
    )
    st.stop()


# ============================================================
# SESSION
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = get_messages(
        supabase,
        user_id,
        limit=100,
    )


if "memories" not in st.session_state:
    st.session_state.memories = get_memories(
        supabase,
        user_id,
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        '<div class="kenz-logo">✦ KENZ</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="kenz-subtitle">'
        'Kişisel yapay zekâ asistanın'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="user-badge">
            Kullanıcı: {user_id[:8]}...
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button(
        "＋ Yeni sohbet",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # --------------------------------------------------------
    # HAFIZA
    # --------------------------------------------------------

    st.subheader("🧠 Hafıza")

    memories = get_memories(
        supabase,
        user_id,
    )

    if memories:

        for memory in memories[:20]:

            text = memory.get(
                "memory",
                "",
            )

            st.markdown(
                f"""
                <div class="file-chip">
                    {text}
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        st.caption(
            "Henüz kayıtlı hafıza yok."
        )

    st.divider()

    # --------------------------------------------------------
    # GARDIROP
    # --------------------------------------------------------

    st.subheader("👕 Gardırop")

    wardrobe = get_wardrobe(
        supabase,
        user_id,
    )

    st.caption(
        f"{len(wardrobe)} parça kayıtlı"
    )

    if wardrobe:

        for item in wardrobe[:10]:

            name = item.get(
                "name",
                "Kıyafet",
            )

            category = item.get(
                "category",
                "",
            )

            color = item.get(
                "color",
                "",
            )

            st.markdown(
                f"""
                <div class="file-chip">
                    <b>{name}</b><br>
                    <span class="small-muted">
                        {category} · {color}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    if st.button(
        "🗑️ Hafızayı temizle",
        use_container_width=True,
    ):

        for memory in memories:

            delete_memory(
                supabase,
                user_id,
                memory["id"],
            )

        st.session_state.memories = []

        st.success(
            "Hafıza temizlendi."
        )

        st.rerun()


# ============================================================
# MAIN TITLE
# ============================================================

if not st.session_state.messages:

    st.markdown(
        '<div class="main-title">✦</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-title" '
        'style="font-size:34px;margin-top:0;">'
        'Kenz'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-subtitle">'
        'Nasıl yardımcı olabilirim?'
        '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# DISPLAY HISTORY
# ============================================================

for message in st.session_state.messages:

    role = message.get(
        "role",
        "assistant",
    )

    content = message.get(
        "content",
        "",
    )

    file_data = message.get(
        "file_data",
    )

    file_name = message.get(
        "file_name",
    )

    with st.chat_message(
        role,
    ):

        if file_data and file_name:

            try:

                raw = base64.b64decode(
                    file_data
                )

                mime = mimetypes.guess_type(
                    file_name
                )[0] or ""

                if mime.startswith(
                    "image/"
                ):

                    st.image(
                        raw,
                        use_container_width=True,
                    )

                elif mime.startswith(
                    "audio/"
                ):

                    st.audio(
                        raw,
                    )

                elif mime.startswith(
                    "video/"
                ):

                    st.video(
                        raw,
                    )

                else:

                    st.download_button(
                        "📥 Dosyayı aç",
                        raw,
                        file_name=file_name,
                        mime=mime,
                    )

            except Exception:
                pass

        if content:
            st.markdown(content)


# ============================================================
# CHAT INPUT
# ============================================================

prompt = st.chat_input(
    "Kenz'e bir şey yaz...",
    accept_file="multiple",
    file_type=[
        "jpg",
        "jpeg",
        "png",
        "webp",
        "gif",
        "pdf",
        "txt",
        "csv",
        "docx",
        "xlsx",
        "mp3",
        "wav",
        "m4a",
        "ogg",
        "opus",
        "mp4",
        "mov",
        "mkv",
        "webm",
        "avi",
    ],
    max_upload_size=200,
    key="kenz_chat_input",
)


# ============================================================
# NEW MESSAGE
# ============================================================

if prompt:

    user_text = (
        prompt.text or ""
    ).strip()

    uploaded_files = (
        prompt.files
        if hasattr(prompt, "files")
        else []
    )

    if (
        not user_text
        and not uploaded_files
    ):

        st.stop()


    # ========================================================
    # CURRENT FILE
    # ========================================================

    file_bytes = None
    file_name = None
    mime_type = None

    if uploaded_files:

        uploaded = uploaded_files[0]

        file_bytes = uploaded.getvalue()

        file_name = uploaded.name

        mime_type = (
            uploaded.type
            or mimetypes.guess_type(
                file_name
            )[0]
            or "application/octet-stream"
        )


    # ========================================================
    # SHOW USER MESSAGE
    # ========================================================

    with st.chat_message("user"):

        if file_bytes:

            if mime_type.startswith(
                "image/"
            ):

                st.image(
                    file_bytes,
                    use_container_width=True,
                )

            elif mime_type.startswith(
                "audio/"
            ):

                st.audio(
                    file_bytes
                )

            elif mime_type.startswith(
                "video/"
            ):

                st.video(
                    file_bytes
                )

            else:

                st.caption(
                    f"📎 {file_name}"
                )

        if user_text:

            st.markdown(
                user_text
            )


    # ========================================================
    # MEMORY COMMANDS
    # ========================================================

    lower_text = user_text.lower()

    memory_saved = False

    if any(
        phrase in lower_text
        for phrase in [
            "bunu hatırla",
            "bunu hafızana al",
            "bunu hafızanda tut",
            "aklında tut",
            "bunu unutma",
            "bundan sonra",
        ]
    ):

        memory_text = re.sub(
            r"\b(bunu hatırla|bunu hafızana al|"
            r"bunu hafızanda tut|aklında tut|"
            r"bunu unutma)\b",
            "",
            user_text,
            flags=re.IGNORECASE,
        ).strip()

        if memory_text:

            save_memory(
                supabase,
                user_id,
                memory_text,
            )

            memory_saved = True


    # ========================================================
    # FORGET COMMAND
    # ========================================================

    if any(
        phrase in lower_text
        for phrase in [
            "bunu unut",
            "şunu unut",
            "hafızadan sil",
        ]
    ):

        memories = get_memories(
            supabase,
            user_id,
        )

        target = re.sub(
            r"\b(bunu unut|şunu unut|hafızadan sil)\b",
            "",
            user_text,
            flags=re.IGNORECASE,
        ).strip().lower()

        for memory in memories:

            memory_text = memory.get(
                "memory",
                "",
            )

            if (
                not target
                or target in memory_text.lower()
                or memory_text.lower() in target
            ):

                delete_memory(
                    supabase,
                    user_id,
                    memory["id"],
                )


    # ========================================================
    # WARDROBE COMMAND
    # ========================================================

    wardrobe_requested = (
        file_bytes is not None
        and any(
            phrase in lower_text
            for phrase in [
                "gardırobuma ekle",
                "gardıroba ekle",
                "dolabıma ekle",
                "kıyafetlerime ekle",
            ]
        )
    )

    if wardrobe_requested:

        try:

            with st.spinner(
                "Kıyafeti analiz ediyorum..."
            ):

                item = extract_wardrobe_item(
                    file_bytes,
                    mime_type,
                    user_text,
                )

                if item:

                    add_wardrobe_item(
                        supabase,
                        user_id,
                        item,
                    )

                    st.success(
                        "Kıyafet gardırobuna eklendi."
                    )

        except Exception as e:

            st.warning(
                "Gardırop kaydı yapılamadı: "
                + str(e)
            )


    # ========================================================
    # LINK CONVERSION
    # ========================================================

    url_match = re.search(
        r"https?://[^\s]+",
        user_text,
        flags=re.IGNORECASE,
    )

    requested_formats = [
        "mp3",
        "wav",
        "flac",
        "m4a",
        "aac",
        "opus",
        "ogg",
        "mp4",
        "mkv",
        "webm",
        "mov",
        "avi",
        "gif",
    ]

    requested_format = None

    for fmt in requested_formats:

        if re.search(
            rf"\b{re.escape(fmt)}\b",
            lower_text,
        ):

            requested_format = fmt
            break


    # ========================================================
    # CONVERSION
    # ========================================================

    if (
        url_match
        and requested_format
        and any(
            word in lower_text
            for word in [
                "çevir",
                "dönüştür",
                "indir",
                "yap",
                "format",
            ]
        )
    ):

        url = url_match.group(0)

        with st.chat_message(
            "assistant"
        ):

            with st.spinner(
                f"Link işleniyor → {requested_format.upper()}..."
            ):

                try:

                    result = convert_media_url(
                        url,
                        requested_format,
                    )

                    st.success(
                        "Dönüştürme tamamlandı."
                    )

                    st.download_button(
                        f"📥 {requested_format.upper()} indir",
                        result["bytes"],
                        file_name=result["file_name"],
                        mime=result["mime_type"],
                        use_container_width=True,
                    )

                    answer = (
                        f"Tamamdır. Linki "
                        f"**{requested_format.upper()}** "
                        f"formatına dönüştürdüm."
                    )

                    st.markdown(
                        answer
                    )

                    save_message(
                        supabase,
                        user_id,
                        "user",
                        user_text,
                        file_name,
                        file_bytes,
                    )

                    save_message(
                        supabase,
                        user_id,
                        "assistant",
                        answer,
                        None,
                        None,
                    )

                    st.session_state.messages = (
                        get_messages(
                            supabase,
                            user_id,
                            limit=100,
                        )
                    )

                    st.stop()

                except Exception as e:

                    st.error(
                        "Bu link dönüştürülemedi."
                    )

                    st.caption(
                        str(e)
                    )

                    st.stop()


    # ========================================================
    # SAVE USER MESSAGE
    # ========================================================

    save_message(
        supabase,
        user_id,
        "user",
        user_text,
        file_name,
        file_bytes,
    )


    # ========================================================
    # HISTORY FOR AI
    # ========================================================

    history = get_messages(
        supabase,
        user_id,
        limit=30,
    )


    # ========================================================
    # AI
    # ========================================================

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "Kenz düşünüyor..."
        ):

            try:

                answer = chat_with_kenz(
                    user_text=user_text,
                    file_bytes=file_bytes,
                    file_name=file_name,
                    mime_type=mime_type,
                    history=history,
                    memories=get_memories(
                        supabase,
                        user_id,
                    ),
                    wardrobe=get_wardrobe(
                        supabase,
                        user_id,
                    ),
                )

                st.markdown(
                    answer
                )

                if memory_saved:

                    st.caption(
                        "🧠 Bunu hafızama aldım."
                    )

                save_message(
                    supabase,
                    user_id,
                    "assistant",
                    answer,
                    None,
                    None,
                )

                st.session_state.messages = (
                    get_messages(
                        supabase,
                        user_id,
                        limit=100,
                    )
                )

            except Exception as e:

                st.error(
                    "Kenz cevap verirken bir hata oluştu."
                )

                with st.expander(
                    "Teknik hata"
                ):

                    st.code(
                        str(e)
                    )
